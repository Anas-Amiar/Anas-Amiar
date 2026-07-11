# Data Quality Gate

**A CI gate for data pipelines: if your code change breaks the data, the merge is blocked.**

Model changes get regression tests. Pipeline changes usually don't — a "harmless" SQL refactor ships, and three days later someone notices APAC revenue has been zero since Tuesday. This gate runs the changed pipeline's output against a golden dataset under a **data contract**, and fails the PR check if the output drifted.

## The idea

A data contract, written in pydantic, pins down what healthy output means numerically:

```python
Contract(
    table="orders_daily",
    primary_key=["order_id"],
    row_count_tolerance_pct=5.0,
    columns=[
        ColumnSpec(name="amount", type=ColumnType.FLOAT, min_value=0.0, max_psi=0.1),
        ColumnSpec(name="region", type=ColumnType.STR, nullable=True, max_null_rate=0.01),
        ...
    ],
)
```

The gate compares candidate output to golden on five axes: row count drift, primary-key uniqueness, null rates, value ranges, and **Population Stability Index** (distribution drift) on numeric columns. PSI is the check that earns its keep — it catches the bug where row counts, schema, and every individual value look fine, but the population moved (see the cents/dollars scenario below).

## Run it

```bash
pip install pydantic
python demo.py
```

The demo gates five simulated pipeline changes. One is a safe refactor; four carry bugs that really ship:

```
Proposed change: New payment provider reports cents, not dollars
FAIL: orders_daily — 1 violation(s) in 6 checks
  BLOCK distribution_psi [amount]: distribution of 'amount' drifted from golden (PSI 7.66)
CI outcome: MERGE BLOCKED

Proposed change: Refactor: same logic, cleaner SQL
PASS: orders_daily — 6 checks, 5000 rows vs 5000 golden
CI outcome: merge allowed
```

As a CI step, the module is the check — exit code 0 or 1:

```bash
python -m data_quality_gate --scenario lossy_filter && echo mergeable || echo blocked
```

A ready-to-use workflow lives in [`examples/github-actions.yml`](examples/github-actions.yml).

## Tests

```bash
python -m unittest discover tests -v
```

The key test: the unit bug (cents vs dollars) must be caught by PSI *alone* — same row count, valid schema, all values positive. If you delete the PSI check, that bug ships.

## Design notes

- **Golden datasets are eval sets for pipelines.** Same discipline as prompt regression testing: freeze known-good output, diff every change against it, block on drift.
- **Tolerances, not equality.** Real pipelines have noise. The contract encodes how much drift is normal (±5% rows, 1% nulls, PSI < 0.1) so the gate doesn't cry wolf and get disabled — the fate of most data quality tooling.
- **The simulated scenarios are the mock mode.** In a real deployment, `--scenario` is replaced by "run the changed pipeline on fixture inputs"; `run_gate()` doesn't change.
