"""The statistics, from scratch on the standard library.

Nothing exotic: normal CDF via erf, a two-proportion z-test, a chi-square
sample-ratio-mismatch test (df=1 for two arms), and the standard sample
size formula for comparing two proportions.
"""

import math


def normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def normal_quantile(p: float) -> float:
    """Inverse normal CDF by bisection — slow and boring, but dependency-free
    and accurate to ~1e-10, which is far tighter than anything else here."""
    if not 0.0 < p < 1.0:
        raise ValueError("p must be in (0, 1)")
    lo, hi = -10.0, 10.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if normal_cdf(mid) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def two_proportion_pvalue(conv_a: int, n_a: int, conv_b: int, n_b: int) -> float:
    """Two-sided p-value for H0: the two conversion rates are equal."""
    if n_a == 0 or n_b == 0:
        return 1.0
    p_a, p_b = conv_a / n_a, conv_b / n_b
    pooled = (conv_a + conv_b) / (n_a + n_b)
    se = math.sqrt(pooled * (1 - pooled) * (1 / n_a + 1 / n_b))
    if se == 0:
        return 1.0
    z = (p_b - p_a) / se
    return 2.0 * (1.0 - normal_cdf(abs(z)))


def srm_pvalue(n_a: int, n_b: int, expected_share_a: float = 0.5) -> float:
    """Chi-square test (df=1): did the traffic split we got match the split
    we configured? For df=1, p = erfc(sqrt(stat/2))."""
    total = n_a + n_b
    if total == 0:
        return 1.0
    exp_a = total * expected_share_a
    exp_b = total * (1 - expected_share_a)
    stat = (n_a - exp_a) ** 2 / exp_a + (n_b - exp_b) ** 2 / exp_b
    return math.erfc(math.sqrt(stat / 2.0))


def required_n_per_arm(
    baseline_rate: float, relative_mde: float, alpha: float = 0.05, power: float = 0.8
) -> int:
    """Users per arm needed to detect a `relative_mde` lift over
    `baseline_rate` at the given alpha and power (two-sided)."""
    p1 = baseline_rate
    p2 = baseline_rate * (1 + relative_mde)
    z_alpha = normal_quantile(1 - alpha / 2)
    z_power = normal_quantile(power)
    variance = p1 * (1 - p1) + p2 * (1 - p2)
    n = (z_alpha + z_power) ** 2 * variance / (p2 - p1) ** 2
    return math.ceil(n)
