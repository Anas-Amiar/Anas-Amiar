"""Run five incidents through the forensics engine.

Four are data bugs planted at different pipeline stages; one is a genuine
demand drop. The engine sees only the pipeline's health stats — it is never
told which scenario it is looking at.

    python demo.py
"""

from metric_forensics import FailureMode, baseline_runs, diagnose, run_pipeline

SCENARIOS = [
    (FailureMode.SOURCE_DROPOUT, "Mobile SDK release breaks event delivery"),
    (FailureMode.SCHEMA_CHANGE, "Upstream team ships 'amount' as a string"),
    (FailureMode.JOIN_FANOUT, "Customer dim loaded twice, join fans out"),
    (FailureMode.TIMEZONE_SHIFT, "Producer switches timestamps to UTC"),
    (FailureMode.REAL_CHANGE, "Demand genuinely drops 20%"),
]


def main() -> None:
    baseline = baseline_runs(days=14)

    for failure, headline in SCENARIOS:
        incident = run_pipeline(day=15, failure=failure)
        diagnosis = diagnose(baseline, incident)

        print("=" * 72)
        print(f"Scenario: {headline}")
        print(f"Dashboard shows: revenue {diagnosis.change_pct:+.1f}% "
              f"({diagnosis.observed:,.0f} vs expected {diagnosis.expected:,.0f})")
        print(f"Verdict: {diagnosis.verdict.value.upper()}")
        if diagnosis.first_broken_stage:
            print(f"First broken stage: {diagnosis.first_broken_stage}")
            for check in diagnosis.evidence:
                print(f"  {check.describe()}")
        print(f"Summary: {diagnosis.summary}")
        print()


if __name__ == "__main__":
    main()
