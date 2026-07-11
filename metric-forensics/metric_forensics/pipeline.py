"""A deterministic mock of a small analytics pipeline.

Four stages, the way most revenue dashboards are actually fed:

    ingest -> staging -> enrich -> aggregate

Every stage records the health stats a forensics tool needs (row counts,
null rates, join fanout, hour-of-day distribution). Failure modes are
injected here, at the source, so the forensics engine downstream never
gets told what broke — it has to find out.
"""

import random
from enum import Enum

from pydantic import BaseModel, Field

SOURCES = ["web", "mobile", "pos"]

# Share of daily traffic per source, and a diurnal curve: weights for each
# hour of the day (people buy less at 4am).
SOURCE_WEIGHTS = {"web": 0.5, "mobile": 0.35, "pos": 0.15}
HOUR_WEIGHTS = [1, 1, 1, 1, 1, 2, 3, 5, 7, 8, 9, 9, 10, 9, 9, 8, 8, 9, 10, 9, 7, 5, 3, 2]


class FailureMode(str, Enum):
    NONE = "none"
    SOURCE_DROPOUT = "source_dropout"      # one upstream source delivers nothing
    SCHEMA_CHANGE = "schema_change"        # amount arrives as "12.34 USD", parser nulls it
    JOIN_FANOUT = "join_fanout"            # duplicated dimension keys multiply rows
    TIMEZONE_SHIFT = "timezone_shift"      # events timestamped in the wrong timezone
    REAL_CHANGE = "real_change"            # demand genuinely dropped — nothing is broken


class IngestStats(BaseModel):
    rows_by_source: dict[str, int]

    @property
    def total_rows(self) -> int:
        return sum(self.rows_by_source.values())


class StagingStats(BaseModel):
    rows: int
    amount_null_rate: float


class EnrichStats(BaseModel):
    rows_in: int
    rows_out: int
    dim_match_rate: float

    @property
    def fanout(self) -> float:
        return self.rows_out / self.rows_in if self.rows_in else 0.0


class AggregateStats(BaseModel):
    revenue: float
    orders: int
    hour_histogram: list[float] = Field(min_length=24, max_length=24)


class PipelineRun(BaseModel):
    day: int
    failure: FailureMode
    ingest: IngestStats
    staging: StagingStats
    enrich: EnrichStats
    aggregate: AggregateStats


def _generate_events(day: int, rng: random.Random, failure: FailureMode) -> list[dict]:
    base_orders = 2000 + rng.randint(-80, 80)
    if failure == FailureMode.REAL_CHANGE:
        base_orders = int(base_orders * 0.80)  # demand really is down 20%

    events = []
    hour_total = sum(HOUR_WEIGHTS)
    for source, share in SOURCE_WEIGHTS.items():
        if failure == FailureMode.SOURCE_DROPOUT and source == "mobile":
            continue  # the mobile SDK vendor shipped a bad release; nothing arrives
        n = int(base_orders * share)
        for _ in range(n):
            hour = rng.choices(range(24), weights=HOUR_WEIGHTS)[0]
            amount = round(rng.lognormvariate(3.4, 0.5), 2)
            if failure == FailureMode.TIMEZONE_SHIFT:
                # Producer switched to UTC; local midnight moved. Events from
                # the first 8 local hours now land on the previous day.
                if hour < 8:
                    continue
                hour = (hour - 8) % 24
            raw_amount: object = amount
            if failure == FailureMode.SCHEMA_CHANGE:
                raw_amount = f"{amount:.2f} USD"  # was a float yesterday
            events.append(
                {
                    "source": source,
                    "hour": hour,
                    "amount": raw_amount,
                    "customer_id": rng.randint(1, 500),
                }
            )
        _ = hour_total
    return events


def run_pipeline(day: int, seed: int = 7, failure: FailureMode = FailureMode.NONE) -> PipelineRun:
    """Run one day of the pipeline and record per-stage health stats."""
    rng = random.Random(seed * 10_000 + day)

    # Stage 1: ingest — count what each source delivered.
    events = _generate_events(day, rng, failure)
    rows_by_source = {s: 0 for s in SOURCES}
    for e in events:
        rows_by_source[e["source"]] += 1
    ingest = IngestStats(rows_by_source=rows_by_source)

    # Stage 2: staging — parse and type the raw events.
    staged = []
    nulls = 0
    for e in events:
        amount = e["amount"]
        if not isinstance(amount, (int, float)):
            amount = None  # parser can't coerce "12.34 USD"
            nulls += 1
        staged.append({**e, "amount": amount})
    staging = StagingStats(
        rows=len(staged),
        amount_null_rate=nulls / len(staged) if staged else 0.0,
    )

    # Stage 3: enrich — join orders to the customer dimension.
    dim = {cid: {"segment": "smb" if cid % 3 else "enterprise"} for cid in range(1, 476)}
    lookup: dict[int, list[dict]] = {}
    copies = 2 if failure == FailureMode.JOIN_FANOUT else 1
    for cid, attrs in dim.items():
        # A bad dim load appended instead of replacing: every key now twice.
        lookup[cid] = [attrs] * copies
    enriched = []
    matched = 0
    for row in staged:
        hits = lookup.get(row["customer_id"], [None])
        if hits != [None]:
            matched += 1
        for h in hits:
            enriched.append({**row, "segment": h["segment"] if h else None})
    enrich = EnrichStats(
        rows_in=len(staged),
        rows_out=len(enriched),
        dim_match_rate=matched / len(staged) if staged else 0.0,
    )

    # Stage 4: aggregate — the number that ends up on the dashboard.
    revenue = sum(r["amount"] for r in enriched if r["amount"] is not None)
    hour_counts = [0] * 24
    for r in enriched:
        hour_counts[r["hour"]] += 1
    total = sum(hour_counts) or 1
    aggregate = AggregateStats(
        revenue=round(revenue, 2),
        orders=len(enriched),
        hour_histogram=[c / total for c in hour_counts],
    )

    return PipelineRun(day=day, failure=failure, ingest=ingest, staging=staging, enrich=enrich, aggregate=aggregate)


def baseline_runs(days: int = 14, seed: int = 7) -> list[PipelineRun]:
    """A clean history to compare the incident day against."""
    return [run_pipeline(day, seed=seed) for day in range(1, days + 1)]
