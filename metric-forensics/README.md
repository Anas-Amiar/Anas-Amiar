# Metric Forensics

**"Revenue is down 12%" — is that the business, or a broken pipeline?**

When a KPI moves on a dashboard, the first question is never "what happened to the business." It's "did an upstream table break." This tool answers that question automatically: it walks the pipeline in execution order, runs health diagnostics on every stage, and blames the **first** stage that broke — or clears the pipeline and confirms the change is real.

## The idea

A dashboard number is a claim, not a fact. Before anyone reacts to it, verify the chain that produced it:

```
ingest -> staging -> enrich -> aggregate -> "revenue is down 12%"
```

Each stage gets diagnostics that compare the incident day against a 14-day baseline:

| Stage | What can break | What we check |
|---|---|---|
| ingest | a source stops delivering | rows per source vs baseline |
| staging | a schema change nulls a column | parse-failure rate on `amount` |
| enrich | a bad dim load fans out the join | fanout ratio, dim match rate |
| aggregate | timestamps land in the wrong day | hour-of-day distribution distance |

Ordering matters. A source dropout also makes revenue look wrong at the aggregate stage, but the aggregate isn't the culprit — it faithfully summed the rows it was given. The engine blames the *first* broken stage, not the last one that looked bad.

## Run it

```bash
pip install pydantic
python demo.py
```

The demo runs five incidents. Four are data bugs planted at different stages; one is a genuine 20% demand drop. The engine is never told which is which:

```
Scenario: Producer switches timestamps to UTC
Dashboard shows: revenue -12.6% (59,402 vs expected 67,973)
Verdict: DATA_ISSUE
First broken stage: aggregate
  [FAIL] aggregate.hour_distribution_l1: observed=1.034 expected=0.000 (tol ±0.150)

Scenario: Demand genuinely drops 20%
Dashboard shows: revenue -23.6% (51,919 vs expected 67,973)
Verdict: REAL_CHANGE
Summary: ... every pipeline stage checks out. This looks like a real business
change, not a data bug.
```

## Tests

```bash
python -m unittest discover tests -v
```

The tests assert that each planted failure is blamed on the correct stage — including the case where a schema change zeroes out revenue entirely and the engine must still point at staging, not at the scary number downstream.

## Design notes

- **Mock pipeline, real diagnostics.** The pipeline is a deterministic simulation with realistic failure modes (`pipeline.py`). The forensics engine (`forensics.py`) never sees the injected failure — only the health stats a real warehouse would expose. Swapping the simulation for real stage metadata (row counts from your loader, null rates from dbt tests) doesn't change the engine.
- **Shape checks, not just size checks.** Row counts catch missing data; they don't catch a timezone bug where the counts look plausible. The hour-of-day distribution check compares the *shape* of the day against baseline.
- **Every verdict is a pydantic model** (`models.py`), so the output can drive a Slack alert or a dashboard annotation instead of being prose in a terminal.
