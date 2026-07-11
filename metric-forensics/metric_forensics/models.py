"""Typed results for a forensics run. Everything the tool concludes is a
pydantic model, so a downstream consumer (Slack bot, dashboard annotation)
gets structure, not prose."""

from enum import Enum

from pydantic import BaseModel, Field


class Verdict(str, Enum):
    NO_ANOMALY = "no_anomaly"
    DATA_ISSUE = "data_issue"
    REAL_CHANGE = "real_change"


class Check(BaseModel):
    """One diagnostic comparison between the incident day and the baseline."""

    name: str
    passed: bool
    observed: float
    expected: float
    tolerance: float
    detail: str = ""

    def describe(self) -> str:
        status = "ok" if self.passed else "FAIL"
        return (
            f"[{status}] {self.name}: observed={self.observed:.3f} "
            f"expected={self.expected:.3f} (tol ±{self.tolerance:.3f}) {self.detail}"
        )


class StageReport(BaseModel):
    """All diagnostics for one pipeline stage."""

    stage: str
    checks: list[Check] = Field(default_factory=list)

    @property
    def healthy(self) -> bool:
        return all(c.passed for c in self.checks)

    @property
    def failures(self) -> list[Check]:
        return [c for c in self.checks if not c.passed]


class Diagnosis(BaseModel):
    """The final verdict: is the metric change a data problem or a real one?"""

    verdict: Verdict
    metric_name: str
    observed: float
    expected: float
    change_pct: float
    first_broken_stage: str | None = None
    evidence: list[Check] = Field(default_factory=list)
    stage_reports: list[StageReport] = Field(default_factory=list)
    summary: str
