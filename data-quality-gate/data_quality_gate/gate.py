"""The gate itself: compare a candidate table against the golden dataset
under a contract, and return a machine-readable pass/fail.

Checks, in order of how often they catch real regressions:
row count drift, primary-key uniqueness, null rates, value ranges, and
Population Stability Index (distribution drift) on numeric columns.
"""

import math

from .contracts import ColumnSpec, ColumnType, Contract, GateResult, Violation
from .generator import Row

PSI_BINS = 10
_PY_TYPES = {ColumnType.INT: int, ColumnType.FLOAT: (int, float), ColumnType.STR: str}


def _numeric_values(rows: list[Row], column: str) -> list[float]:
    return [float(r[column]) for r in rows if r.get(column) is not None]


def population_stability_index(golden: list[float], candidate: list[float]) -> float:
    """PSI over decile bins of the golden distribution.

    PSI is the standard 'did the population move?' score in credit-risk
    monitoring: <0.1 stable, 0.1-0.25 drifting, >0.25 the population changed.
    """
    if not golden or not candidate:
        return float("inf")
    ordered = sorted(golden)
    edges = [ordered[int(len(ordered) * i / PSI_BINS)] for i in range(1, PSI_BINS)]

    def bin_shares(values: list[float]) -> list[float]:
        counts = [0] * PSI_BINS
        for v in values:
            idx = sum(1 for e in edges if v > e)
            counts[idx] += 1
        # Laplace smoothing keeps empty bins from producing log(0).
        return [(c + 1) / (len(values) + PSI_BINS) for c in counts]

    g_shares = bin_shares(golden)
    c_shares = bin_shares(candidate)
    return sum((c - g) * math.log(c / g) for g, c in zip(g_shares, c_shares))


def _check_column(spec: ColumnSpec, golden: list[Row], candidate: list[Row]) -> list[Violation]:
    violations = []
    values = [r.get(spec.name) for r in candidate]
    null_count = sum(1 for v in values if v is None)
    null_rate = null_count / len(values) if values else 0.0

    limit = spec.max_null_rate if spec.nullable else 0.0
    if null_rate > limit:
        violations.append(
            Violation(
                check="null_rate",
                column=spec.name,
                observed=null_rate,
                limit=limit,
                message=f"{null_rate:.1%} of rows have null '{spec.name}'",
            )
        )

    non_null = [v for v in values if v is not None]
    bad_type = sum(1 for v in non_null if not isinstance(v, _PY_TYPES[spec.type]))
    if bad_type:
        violations.append(
            Violation(
                check="type",
                column=spec.name,
                observed=float(bad_type),
                limit=0.0,
                message=f"{bad_type} rows are not {spec.type.value}",
            )
        )
        return violations  # range/PSI on mistyped data would just be noise

    if spec.type != ColumnType.STR and non_null:
        numeric = [float(v) for v in non_null]  # type: ignore[arg-type]
        if spec.min_value is not None and min(numeric) < spec.min_value:
            violations.append(
                Violation(
                    check="min_value",
                    column=spec.name,
                    observed=min(numeric),
                    limit=spec.min_value,
                    message=f"'{spec.name}' has values below the allowed minimum",
                )
            )
        if spec.max_value is not None and max(numeric) > spec.max_value:
            violations.append(
                Violation(
                    check="max_value",
                    column=spec.name,
                    observed=max(numeric),
                    limit=spec.max_value,
                    message=f"'{spec.name}' has values above the allowed maximum",
                )
            )
        if spec.max_psi is not None:
            psi = population_stability_index(_numeric_values(golden, spec.name), numeric)
            if psi > spec.max_psi:
                violations.append(
                    Violation(
                        check="distribution_psi",
                        column=spec.name,
                        observed=psi,
                        limit=spec.max_psi,
                        message=f"distribution of '{spec.name}' drifted from golden (PSI {psi:.2f})",
                    )
                )
    return violations


def run_gate(golden: list[Row], candidate: list[Row], contract: Contract) -> GateResult:
    violations: list[Violation] = []
    checks_run = 0

    # Row count drift.
    checks_run += 1
    drift_pct = abs(len(candidate) - len(golden)) / len(golden) * 100 if golden else 100.0
    if drift_pct > contract.row_count_tolerance_pct:
        violations.append(
            Violation(
                check="row_count",
                observed=float(len(candidate)),
                limit=float(len(golden)),
                message=f"row count drifted {drift_pct:.1f}% from golden "
                        f"(tolerance {contract.row_count_tolerance_pct:.1f}%)",
            )
        )

    # Primary-key uniqueness.
    if contract.primary_key:
        checks_run += 1
        keys = [tuple(r.get(c) for c in contract.primary_key) for r in candidate]
        dupes = len(keys) - len(set(keys))
        if dupes:
            violations.append(
                Violation(
                    check="primary_key_unique",
                    column=",".join(contract.primary_key),
                    observed=float(dupes),
                    limit=0.0,
                    message=f"{dupes} duplicate primary keys",
                )
            )

    for spec in contract.columns:
        checks_run += 1
        violations.extend(_check_column(spec, golden, candidate))

    return GateResult(
        table=contract.table,
        passed=not violations,
        checks_run=checks_run,
        violations=violations,
        golden_rows=len(golden),
        candidate_rows=len(candidate),
    )
