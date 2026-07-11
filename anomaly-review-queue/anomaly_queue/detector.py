"""Seasonality-aware robust anomaly detection with a three-way triage.

The detector compares each day against the median of the same weekday over
the trailing weeks (Mondays vs Mondays — comparing Sunday to Wednesday just
detects the weekend). Deviation is scored in robust z-score units (MAD),
then triaged:

    score >= 6.0   AUTO_ALERT    confident enough to page someone
    score >= 2.5   NEEDS_REVIEW  ambiguous; goes to the human queue
    otherwise      IGNORE

The middle band is the point of this project. A detector that must answer
alert/ignore on every point either pages people for noise or misses subtle
regressions. Admitting uncertainty is the third option.
"""

import statistics

from .models import Decision, Detection, MetricPoint

AUTO_THRESHOLD = 6.0
REVIEW_THRESHOLD = 2.5
BASELINE_WEEKS = 8
# MAD can collapse to ~0 on quiet metrics; floor the scale at 2% of the
# median so a 3% wiggle can't become a 40-sigma "anomaly".
MIN_SCALE_FRACTION = 0.02


def score_day(history: list[MetricPoint], point: MetricPoint) -> Detection | None:
    same_weekday = [p.value for p in history if p.day % 7 == point.day % 7]
    baseline = same_weekday[-BASELINE_WEEKS:]
    if len(baseline) < 4:
        return None  # not enough history to say anything honest

    expected = statistics.median(baseline)
    mad = statistics.median([abs(v - expected) for v in baseline])
    scale = max(1.4826 * mad, MIN_SCALE_FRACTION * expected)
    score = abs(point.value - expected) / scale

    if score >= AUTO_THRESHOLD:
        decision = Decision.AUTO_ALERT
    elif score >= REVIEW_THRESHOLD:
        decision = Decision.NEEDS_REVIEW
    else:
        decision = Decision.IGNORE

    return Detection(
        day=point.day,
        value=point.value,
        expected=expected,
        score=round(score, 2),
        decision=decision,
    )


def detect(series: list[MetricPoint], eval_days: int = 42) -> list[Detection]:
    """Score the last `eval_days` of the series against trailing history."""
    detections = []
    for i, point in enumerate(series):
        if point.day <= len(series) - eval_days:
            continue
        detection = score_day(series[:i], point)
        if detection is not None:
            detections.append(detection)
    return detections
