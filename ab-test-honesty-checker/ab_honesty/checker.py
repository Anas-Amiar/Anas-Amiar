"""The honesty checks, in the order that matters.

1. Sample ratio mismatch first — if the traffic split is broken, every
   number downstream is untrustworthy and the analysis stops there.
2. Peeking correction — every interim look at the data was a chance to
   stop on noise, so the significance bar rises with the number of looks
   (Bonferroni: blunt, but never flattering).
3. Power — a non-significant result from an underpowered test is not
   evidence of no effect, and a significant one is probably inflated.
   Either way the honest answer is a sample count, not a verdict.
"""

from .models import ExperimentData, Report, Verdict
from .stats import required_n_per_arm, srm_pvalue, two_proportion_pvalue

SRM_ALARM_P = 0.001  # below this, the split itself is broken


def check(data: ExperimentData) -> Report:
    design = data.design
    final = data.final

    control_rate = final.control_conversions / final.control_users
    treatment_rate = final.treatment_conversions / final.treatment_users
    lift = (treatment_rate - control_rate) / control_rate if control_rate else 0.0

    p_value = two_proportion_pvalue(
        final.control_conversions, final.control_users,
        final.treatment_conversions, final.treatment_users,
    )
    n_looks = len(data.looks)
    adjusted_alpha = design.alpha / n_looks
    srm_p = srm_pvalue(final.control_users, final.treatment_users, design.expected_share_control)
    required = required_n_per_arm(
        design.baseline_rate, design.relative_mde, design.alpha, design.power
    )
    users_per_arm = min(final.control_users, final.treatment_users)

    def report(verdict: Verdict, reasons: list[str]) -> Report:
        return Report(
            experiment=design.name,
            verdict=verdict,
            control_rate=control_rate,
            treatment_rate=treatment_rate,
            relative_lift=lift,
            p_value=p_value,
            adjusted_alpha=adjusted_alpha,
            n_looks=n_looks,
            srm_p_value=srm_p,
            users_per_arm=users_per_arm,
            required_per_arm=required,
            reasons=reasons,
        )

    # 1. Is the experiment itself broken?
    if srm_p < SRM_ALARM_P:
        share = final.control_users / (final.control_users + final.treatment_users)
        return report(
            Verdict.INVALID,
            [
                f"Sample ratio mismatch: expected {design.expected_share_control:.0%} control, "
                f"got {share:.1%} (p={srm_p:.2g}).",
                "Some users are missing from one arm in a non-random way, so both "
                "conversion rates are biased. No conclusion can be drawn from this data.",
                "Find the assignment/logging bug and restart the experiment.",
            ],
        )

    significant = p_value < adjusted_alpha
    peeked_significant = p_value < design.alpha and not significant
    powered = users_per_arm >= required

    # 2 & 3. Combine peeking and power into an honest verdict.
    if significant and powered:
        if lift > 0:
            return report(
                Verdict.SHIP,
                [
                    f"Significant after correcting for {n_looks} look(s) "
                    f"(p={p_value:.4f} < {adjusted_alpha:.4f}) with adequate power.",
                ],
            )
        return report(
            Verdict.DONT_SHIP,
            [
                f"Treatment is significantly WORSE (lift {lift:+.1%}, p={p_value:.4f}).",
            ],
        )

    if peeked_significant:
        return report(
            Verdict.KEEP_COLLECTING,
            [
                f"p={p_value:.4f} beats your alpha of {design.alpha}, but you looked at "
                f"this experiment {n_looks} times — each look was a chance to stop on noise.",
                f"After correction the bar is {adjusted_alpha:.4f}, and this doesn't clear it.",
                "This is exactly how false winners get shipped. Keep collecting.",
            ],
        )

    if not powered:
        deficit = required - users_per_arm
        return report(
            Verdict.KEEP_COLLECTING,
            [
                f"Underpowered: {users_per_arm} users/arm, but detecting a "
                f"{design.relative_mde:.0%} lift on a {design.baseline_rate:.0%} baseline "
                f"needs {required}/arm.",
                f"Collect at least {deficit} more users per arm before drawing any conclusion.",
                "'Not significant' from an underpowered test is not evidence of no effect.",
            ],
        )

    return report(
        Verdict.DONT_SHIP,
        [
            f"Adequately powered ({users_per_arm}/arm) and no significant effect "
            f"(p={p_value:.4f}).",
            f"If a {design.relative_mde:.0%} lift existed, this test would probably have "
            f"found it. Ship something else.",
        ],
    )
