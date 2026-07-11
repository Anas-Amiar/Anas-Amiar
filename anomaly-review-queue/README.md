# Anomaly Review Queue

**An anomaly detector that knows what it doesn't know.**

Most metric alerting is binary: page or stay silent. Set the threshold low and you page people for noise until they mute the channel; set it high and the subtle regressions sail through. This detector has a third answer — *"I'm not sure, a human should look"* — and the humans' answers are captured as a benchmark that measures whether the thresholds deserve their confidence.

## The idea

Each day's metric is scored against the median of the same weekday over the trailing 8 weeks (Mondays vs Mondays — comparing Sunday to Wednesday just detects the weekend), in robust z-score units. Then a three-way triage:

| Score | Decision | Meaning |
|---|---|---|
| ≥ 6.0 | `auto_alert` | confident enough to page someone |
| ≥ 2.5 | `needs_review` | ambiguous — goes to the human queue (SQLite) |
| < 2.5 | `ignore` | normal variation |

Every human review is stored, and the benchmark computes **per-band precision** from those labels. That's the flywheel: if `auto_alert` precision drops, the threshold is too eager; if humans keep confirming `needs_review` items, it's too shy. The corrections that normally die in a Slack thread become the tuning data.

## Run it

```bash
pip install pydantic
python demo.py
```

Four anomalies are planted in a 42-day eval window — a -45% outage, a -18% degradation, a +30% spike, a -7% config regression — plus one **holiday dip** that is statistically weird but operationally fine:

```
day  92  ... ( -45.3%)  score  19.9  -> auto_alert
day 117  ... (  -9.2%)  score   4.0  -> needs_review
day 121  ... (  -7.0%)  score   3.5  -> needs_review

Human works the review queue:
  day 117: score 4.0 -> human says REAL ANOMALY      (config regression)
  day 121: score 3.5 -> human says false alarm        (public holiday)

Benchmark:
  auto_alert    precision=100%
  needs_review  precision=50%
  recall on planted anomalies: 100% (4/4)
```

The review band's 50% precision is the whole argument for its existence: those two days are exactly the ones a binary detector gets wrong — either paging for a holiday or missing a real regression.

## Tests

```bash
python -m unittest discover tests -v
```

Including: weekends must never be flagged (they're 35% below weekdays — a seasonality-blind detector pages every Saturday), a fully clean series must stay silent, and the +30% spike must alert too, because "up and to the right" can still be a data bug.

## Design notes

- **Median/MAD, not mean/stdev.** One outage in the baseline window would inflate a standard deviation and mask the next outage; robust statistics shrug it off.
- **A scale floor** (2% of the median) stops quiet metrics from producing 40-sigma "anomalies" out of 3% wiggles — the classic way robust detectors destroy their own credibility.
- **SQLite as the queue and the benchmark store**, one table, `human_label NULL` meaning "still pending". Swap `:memory:` for a file path and the queue persists across runs.
