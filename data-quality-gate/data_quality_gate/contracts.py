"""Data contracts as pydantic models.

A contract is the analytics equivalent of a golden eval set: it pins down
what "the output of this pipeline looks healthy" means, numerically, so a
code change that violates it can be caught in CI instead of on a dashboard.
"""

from enum import Enum

from pydantic import BaseModel, Field


class ColumnType(str, Enum):
    INT = "int"
    FLOAT = "float"
    STR = "str"


class ColumnSpec(BaseModel):
    name: str
    type: ColumnType
    nullable: bool = False
    max_null_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    min_value: float | None = None
    max_value: float | None = None
    # Population Stability Index vs the golden dataset. 0.1 is the classic
    # "start paying attention" threshold; 0.25 is "the population changed".
    max_psi: float | None = None


class Contract(BaseModel):
    table: str
    columns: list[ColumnSpec]
    # How far the candidate's row count may drift from the golden dataset.
    row_count_tolerance_pct: float = Field(default=5.0, ge=0.0)
    # Primary key columns that must be unique together.
    primary_key: list[str] = Field(default_factory=list)


class Violation(BaseModel):
    check: str
    column: str | None = None
    observed: float
    limit: float
    message: str

    def describe(self) -> str:
        where = f" [{self.column}]" if self.column else ""
        return f"BLOCK {self.check}{where}: {self.message} (observed {self.observed:.4g}, limit {self.limit:.4g})"


class GateResult(BaseModel):
    table: str
    passed: bool
    checks_run: int
    violations: list[Violation] = Field(default_factory=list)
    golden_rows: int
    candidate_rows: int

    def describe(self) -> str:
        if self.passed:
            return (
                f"PASS: {self.table} — {self.checks_run} checks, "
                f"{self.candidate_rows} rows vs {self.golden_rows} golden"
            )
        lines = [f"FAIL: {self.table} — {len(self.violations)} violation(s) in {self.checks_run} checks"]
        lines += ["  " + v.describe() for v in self.violations]
        return "\n".join(lines)
