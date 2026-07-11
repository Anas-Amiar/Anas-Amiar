"""Deterministic golden dataset plus candidate outputs of "pipeline changes".

The golden dataset is what the current production pipeline produces. Each
scenario simulates the output after a proposed code change — one safe, the
rest carrying a bug of a kind that really ships: a filter that quietly
drops rows, a unit mix-up, a join that duplicates, a source that nulls out.
"""

import random
from enum import Enum

Row = dict[str, object]


class Scenario(str, Enum):
    SAFE_REFACTOR = "safe_refactor"      # same logic, cleaner code, same output
    LOSSY_FILTER = "lossy_filter"        # "simplified" WHERE clause drops a segment
    UNIT_BUG = "unit_bug"                # amounts now in cents, not dollars
    DUPLICATE_JOIN = "duplicate_join"    # join change duplicates 8% of rows
    NULL_LEAK = "null_leak"              # refactor stops coalescing region


REGIONS = ["emea", "amer", "apac"]


def _base_rows(rng: random.Random, n: int) -> list[Row]:
    rows = []
    for i in range(n):
        rows.append(
            {
                "order_id": i + 1,
                "amount": round(rng.lognormvariate(3.5, 0.6), 2),
                "region": rng.choices(REGIONS, weights=[0.45, 0.4, 0.15])[0],
                "items": rng.randint(1, 8),
            }
        )
    return rows


def golden(seed: int = 11, n: int = 5000) -> list[Row]:
    return _base_rows(random.Random(seed), n)


def candidate(scenario: Scenario, seed: int = 11, n: int = 5000) -> list[Row]:
    """The table the changed pipeline would produce."""
    rng = random.Random(seed)
    rows = _base_rows(rng, n)
    mut = random.Random(seed + 1)

    if scenario == Scenario.SAFE_REFACTOR:
        # Equivalent logic; row order changes and floats re-round, nothing else.
        rows = sorted(rows, key=lambda r: (r["region"], r["order_id"]))
        return rows

    if scenario == Scenario.LOSSY_FILTER:
        # The refactored WHERE clause reads cleaner and silently excludes APAC.
        return [r for r in rows if r["region"] != "apac"]

    if scenario == Scenario.UNIT_BUG:
        # New payment provider reports minor units. Nobody divided by 100.
        return [{**r, "amount": round(float(r["amount"]) * 100, 2)} for r in rows]

    if scenario == Scenario.DUPLICATE_JOIN:
        dupes = [dict(r) for r in rows if mut.random() < 0.08]
        return rows + dupes

    if scenario == Scenario.NULL_LEAK:
        return [
            {**r, "region": None} if mut.random() < 0.12 else r
            for r in rows
        ]

    raise ValueError(f"unknown scenario: {scenario}")
