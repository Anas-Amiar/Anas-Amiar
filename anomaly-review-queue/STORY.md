# The two-minute version

## The problem

Every metric alerting system I've seen dies the same death. Week one: threshold set low, catches everything, pages constantly. Week three: the channel is muted. Week six: a real 15% regression runs for days because the system that cried wolf no longer gets read. The root cause isn't the threshold value — it's that the detector is forced to give a binary answer about days that genuinely aren't binary.

## The insight

I used this pattern once before, in my OCR project: score every extraction, auto-accept the confident ones, and route the shaky ones to a human review queue whose corrections become an accuracy benchmark. Metric anomalies have exactly the same structure. A -45% outage needs no human judgment. A -7% dip needs nothing *but* human judgment — it's either a config regression or a public holiday, and no statistical test knows the calendar.

So the detector's output isn't alert/silence, it's alert / ask / ignore. The middle band goes to a SQLite queue, a human answers, and the answer is stored — not as a courtesy, but as benchmark data.

## The part I'm proud of

The benchmark measures the *thresholds*, not just the detector. Per-band precision from human labels tells you directly: if auto-alert precision drops below 100%, the auto threshold is too eager and is spending the team's trust; if humans confirm most needs-review items, the band boundary should move down because you're asking about things you should be alerting on. The demo makes the argument in one line — the review band comes out at 50% precision. Those two days (a real regression and a holiday, near-identical scores of 4.0 and 3.5) are precisely the days a binary detector must get wrong, in one direction or the other.

Second detail: seasonality first, robustness second. The baseline is same-weekday median/MAD over 8 trailing weeks. Weekends run 35% below weekdays in the demo data — a detector that compares Saturday to the weekly average pages every Saturday forever, and there's a test asserting that never happens. MAD instead of standard deviation because the baseline window contains last month's outage, and a detector whose sensitivity is ruined by the previous anomaly misses the next one.

## What it isn't

There's no forecasting model — no Prophet, no LSTM. For daily business metrics with weekly seasonality, same-weekday median gets you most of the accuracy with none of the opacity, and when the detector flags something, the explanation ("Tuesdays average 35,598, today is 32,679") fits in one sentence a human can check. For a system whose middle band exists to earn human trust, explainability is load-bearing.
