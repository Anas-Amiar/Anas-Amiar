from enum import Enum

from pydantic import BaseModel, Field


class Decision(str, Enum):
    AUTO_ALERT = "auto_alert"      # confident enough to page someone
    NEEDS_REVIEW = "needs_review"  # ambiguous — a human decides
    IGNORE = "ignore"              # within normal variation


class MetricPoint(BaseModel):
    day: int
    value: float
    # Ground truth from the generator. The detector NEVER reads this; it
    # exists so the human reviewer and the benchmark have an answer key.
    true_anomaly: bool = False


class Detection(BaseModel):
    day: int
    value: float
    expected: float
    score: float = Field(description="robust z-score vs same-weekday baseline")
    decision: Decision

    @property
    def deviation_pct(self) -> float:
        return (self.value - self.expected) / self.expected * 100 if self.expected else 0.0

    def describe(self) -> str:
        return (
            f"day {self.day:>3}  value {self.value:>9,.0f}  "
            f"expected {self.expected:>9,.0f}  ({self.deviation_pct:+6.1f}%)  "
            f"score {self.score:>5.1f}  -> {self.decision.value}"
        )


class BandStats(BaseModel):
    band: Decision
    total: int
    reviewed: int
    true_positives: int
    false_positives: int

    @property
    def precision(self) -> float | None:
        judged = self.true_positives + self.false_positives
        return self.true_positives / judged if judged else None


class BenchmarkReport(BaseModel):
    bands: list[BandStats]
    true_anomalies_in_window: int
    caught: int
    missed_days: list[int]

    @property
    def recall(self) -> float | None:
        if not self.true_anomalies_in_window:
            return None
        return self.caught / self.true_anomalies_in_window
