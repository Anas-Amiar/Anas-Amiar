from .contracts import ColumnSpec, ColumnType, Contract, GateResult, Violation
from .gate import population_stability_index, run_gate
from .generator import Scenario, candidate, golden

__all__ = [
    "ColumnSpec",
    "ColumnType",
    "Contract",
    "GateResult",
    "Scenario",
    "Violation",
    "candidate",
    "golden",
    "population_stability_index",
    "run_gate",
]

ORDERS_CONTRACT = Contract(
    table="orders_daily",
    primary_key=["order_id"],
    row_count_tolerance_pct=5.0,
    columns=[
        ColumnSpec(name="order_id", type=ColumnType.INT),
        ColumnSpec(name="amount", type=ColumnType.FLOAT, min_value=0.0, max_psi=0.1),
        ColumnSpec(name="region", type=ColumnType.STR, nullable=True, max_null_rate=0.01),
        ColumnSpec(name="items", type=ColumnType.INT, min_value=1, max_value=50),
    ],
)
