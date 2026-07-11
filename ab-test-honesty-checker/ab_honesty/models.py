from enum import Enum

from pydantic import BaseModel, Field


class Verdict(str, Enum):
    SHIP = "ship"
    DONT_SHIP = "dont_ship"
    KEEP_COLLECTING = "keep_collecting"
    INVALID = "invalid"  # the experiment itself is broken; the data can't be trusted


class Design(BaseModel):
    """What was decided BEFORE the experiment started. The checker holds the
    analysis to this, not to whatever looks good afterwards."""

    name: str
    baseline_rate: float = Field(gt=0.0, lt=1.0)
    relative_mde: float = Field(gt=0.0, description="smallest lift worth detecting, e.g. 0.10")
    alpha: float = Field(default=0.05, gt=0.0, lt=1.0)
    power: float = Field(default=0.8, gt=0.0, lt=1.0)
    expected_share_control: float = Field(default=0.5, gt=0.0, lt=1.0)


class Look(BaseModel):
    """One interim peek at the experiment: cumulative counts at that moment."""

    day: int
    control_users: int
    control_conversions: int
    treatment_users: int
    treatment_conversions: int


class ExperimentData(BaseModel):
    design: Design
    looks: list[Look] = Field(min_length=1)

    @property
    def final(self) -> Look:
        return self.looks[-1]


class Report(BaseModel):
    experiment: str
    verdict: Verdict
    control_rate: float
    treatment_rate: float
    relative_lift: float
    p_value: float
    adjusted_alpha: float
    n_looks: int
    srm_p_value: float
    users_per_arm: int
    required_per_arm: int
    reasons: list[str] = Field(default_factory=list)

    def describe(self) -> str:
        lines = [
            f"Experiment: {self.experiment}",
            f"  control {self.control_rate:.2%} vs treatment {self.treatment_rate:.2%} "
            f"(lift {self.relative_lift:+.1%}), p={self.p_value:.4f}",
            f"  looks={self.n_looks} (alpha adjusted {self.adjusted_alpha:.4f}), "
            f"srm_p={self.srm_p_value:.2g}, "
            f"n={self.users_per_arm}/arm of {self.required_per_arm} required",
            f"  VERDICT: {self.verdict.value.upper()}",
        ]
        lines += [f"    - {r}" for r in self.reasons]
        return "\n".join(lines)
