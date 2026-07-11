"""The forensics engine.

Given a baseline of clean pipeline runs and one incident day, decide:
did the metric move because the data broke, or because the business moved?

The engine walks the pipeline in execution order and blames the FIRST
stage whose diagnostics fail. That ordering matters: a source dropout also
makes revenue look wrong at the aggregate stage, but the aggregate isn't
the culprit — it faithfully summed the rows it was given.
"""

import statistics

from .models import Check, Diagnosis, StageReport, Verdict
from .pipeline import SOURCES, PipelineRun


def _mean(values: list[float]) -> float:
    return statistics.fmean(values)


def _stdev(values: list[float]) -> float:
    return statistics.stdev(values) if len(values) > 1 else 0.0


def _check_ingest(baseline: list[PipelineRun], incident: PipelineRun) -> StageReport:
    checks = []
    for source in SOURCES:
        history = [float(r.ingest.rows_by_source[source]) for r in baseline]
        expected = _mean(history)
        tolerance = expected * 0.30
        observed = float(incident.ingest.rows_by_source[source])
        checks.append(
            Check(
                name=f"ingest.rows[{source}]",
                passed=abs(observed - expected) <= tolerance,
                observed=observed,
                expected=expected,
                tolerance=tolerance,
                detail=f"source '{source}' delivered {int(observed)} rows",
            )
        )
    return StageReport(stage="ingest", checks=checks)


def _check_staging(baseline: list[PipelineRun], incident: PipelineRun) -> StageReport:
    history = [r.staging.amount_null_rate for r in baseline]
    expected = _mean(history)
    tolerance = 0.02  # a couple of percent of unparseable rows is normal noise
    observed = incident.staging.amount_null_rate
    check = Check(
        name="staging.amount_null_rate",
        passed=observed <= expected + tolerance,
        observed=observed,
        expected=expected,
        tolerance=tolerance,
        detail="share of rows where 'amount' failed to parse",
    )
    return StageReport(stage="staging", checks=[check])


def _check_enrich(baseline: list[PipelineRun], incident: PipelineRun) -> StageReport:
    fanout_hist = [r.enrich.fanout for r in baseline]
    match_hist = [r.enrich.dim_match_rate for r in baseline]
    checks = [
        Check(
            name="enrich.join_fanout",
            passed=abs(incident.enrich.fanout - _mean(fanout_hist)) <= 0.02,
            observed=incident.enrich.fanout,
            expected=_mean(fanout_hist),
            tolerance=0.02,
            detail="output rows per input row across the dim join",
        ),
        Check(
            name="enrich.dim_match_rate",
            passed=incident.enrich.dim_match_rate >= _mean(match_hist) - 0.05,
            observed=incident.enrich.dim_match_rate,
            expected=_mean(match_hist),
            tolerance=0.05,
            detail="share of orders that found their customer",
        ),
    ]
    return StageReport(stage="enrich", checks=checks)


def _check_aggregate(baseline: list[PipelineRun], incident: PipelineRun) -> StageReport:
    # Compare the shape of the day, not its size: an L1 distance between
    # hour-of-day distributions catches timestamps landing in the wrong
    # buckets even when row counts look plausible.
    n_hours = 24
    mean_hist = [
        _mean([r.aggregate.hour_histogram[h] for r in baseline]) for h in range(n_hours)
    ]
    l1 = sum(abs(incident.aggregate.hour_histogram[h] - mean_hist[h]) for h in range(n_hours))
    check = Check(
        name="aggregate.hour_distribution_l1",
        passed=l1 <= 0.15,
        observed=l1,
        expected=0.0,
        tolerance=0.15,
        detail="distance between today's hour-of-day shape and baseline",
    )
    return StageReport(stage="aggregate", checks=[check])


STAGE_CHECKS = [_check_ingest, _check_staging, _check_enrich, _check_aggregate]


def diagnose(baseline: list[PipelineRun], incident: PipelineRun) -> Diagnosis:
    """Walk the pipeline in order and produce a verdict for the incident day."""
    revenue_hist = [r.aggregate.revenue for r in baseline]
    expected = _mean(revenue_hist)
    spread = max(_stdev(revenue_hist), expected * 0.01)
    observed = incident.aggregate.revenue
    change_pct = (observed - expected) / expected * 100

    reports = [check(baseline, incident) for check in STAGE_CHECKS]

    metric_moved = abs(observed - expected) > 3 * spread
    first_broken = next((r for r in reports if not r.healthy), None)

    if first_broken is not None:
        evidence = first_broken.failures
        verdict = Verdict.DATA_ISSUE
        summary = (
            f"Revenue is {change_pct:+.1f}% vs baseline, but the pipeline broke first: "
            f"stage '{first_broken.stage}' failed "
            f"{', '.join(c.name for c in evidence)}. "
            f"Fix the data before anyone reacts to this number."
        )
        return Diagnosis(
            verdict=verdict,
            metric_name="daily_revenue",
            observed=observed,
            expected=expected,
            change_pct=change_pct,
            first_broken_stage=first_broken.stage,
            evidence=evidence,
            stage_reports=reports,
            summary=summary,
        )

    if metric_moved:
        return Diagnosis(
            verdict=Verdict.REAL_CHANGE,
            metric_name="daily_revenue",
            observed=observed,
            expected=expected,
            change_pct=change_pct,
            stage_reports=reports,
            summary=(
                f"Revenue is {change_pct:+.1f}% vs baseline and every pipeline stage "
                f"checks out. This looks like a real business change, not a data bug."
            ),
        )

    return Diagnosis(
        verdict=Verdict.NO_ANOMALY,
        metric_name="daily_revenue",
        observed=observed,
        expected=expected,
        change_pct=change_pct,
        stage_reports=reports,
        summary=f"Revenue is {change_pct:+.1f}% vs baseline — within normal variation.",
    )
