"""A synthetic daily metric with weekly seasonality, noise, and planted
anomalies of very different sizes — because real anomalies don't arrive
pre-sorted into 'obvious' and 'subtle'."""

import random

from .models import MetricPoint

WEEKDAY_LEVELS = [1.00, 1.04, 1.05, 1.03, 0.98, 0.72, 0.65]  # Mon..Sun
BASE = 50_000.0


def generate_series(
    days: int = 126,
    seed: int = 21,
    anomalies: dict[int, float] | None = None,
    explainable: dict[int, float] | None = None,
) -> list[MetricPoint]:
    """`anomalies` maps day -> multiplier (0.55 = a 45% drop that day).
    `explainable` days get the same treatment but are NOT labeled as true
    anomalies — a holiday dip is statistically weird and operationally fine."""
    rng = random.Random(seed)
    anomalies = anomalies or {}
    explainable = explainable or {}
    points = []
    for day in range(1, days + 1):
        level = BASE * WEEKDAY_LEVELS[day % 7]
        noise = rng.gauss(1.0, 0.015)
        value = level * noise
        multiplier = anomalies.get(day, explainable.get(day))
        if multiplier is not None:
            value *= multiplier
        points.append(
            MetricPoint(day=day, value=round(value, 2), true_anomaly=day in anomalies)
        )
    return points


# The eval window is the last 42 days of a 126-day series. Four planted
# anomalies spanning the difficulty range, from "pages itself" to "only a
# human would catch it".
DEMO_ANOMALIES = {
    92: 0.55,   # infrastructure outage: -45%, unmissable
    103: 0.82,  # partial degradation: -18%, ambiguous
    110: 1.30,  # marketing spike: +30%, real but positive
    117: 0.93,  # subtle config regression: -7%, borderline
}

# Statistically weird, operationally fine: a public holiday. The detector
# should flag it (it can't know the calendar) and the human should clear it.
DEMO_EXPLAINABLE = {
    121: 0.91,
}


def demo_series(seed: int = 21) -> list[MetricPoint]:
    return generate_series(
        days=126, seed=seed, anomalies=DEMO_ANOMALIES, explainable=DEMO_EXPLAINABLE
    )
