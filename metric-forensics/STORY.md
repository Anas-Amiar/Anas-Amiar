# The two-minute version

## The problem

A revenue dashboard drops 12% overnight. Someone posts it in Slack. Within an hour there's a meeting about pricing, a theory about a competitor, and a very stressed marketing team. Two days later a data engineer finds the actual cause: an upstream producer switched its timestamps to UTC, and the first eight hours of every day were landing on the previous day.

The expensive part wasn't the bug. It was the two days the company spent reacting to a number that was never true.

## The insight

Every dashboard number is the output of a chain — ingest, staging, enrich, aggregate — and each link can lie in a characteristic way. Sources drop out. Schemas change silently. Joins fan out. Timestamps shift. When the final number moves, "did the business change?" is the *last* question to ask. The first is "did every link in the chain behave like it did yesterday?"

So the tool works like an incident responder, not a statistician. It walks the pipeline in execution order, compares each stage's health stats against a 14-day baseline, and stops at the first stage that broke. Only if the whole chain is clean does it say: this change is real, go have that meeting.

## The part I'm proud of

Blame ordering. A schema change that nulls out the `amount` column makes *every* downstream stage look catastrophic — revenue goes to literally zero. A naive checker would scream about the aggregate stage, because that's where the damage is most visible. The engine blames staging instead, because that's where the damage was *done*. There's a test that locks this in: revenue at zero, and the verdict still points three stages upstream.

The other detail: the timezone bug is invisible to row counts. The day still has plausible volume; it's the *shape* of the day that's wrong. That's why the aggregate stage checks the hour-of-day distribution against baseline, not just the total.

## What it isn't

It doesn't do root-cause analysis on real changes — if demand genuinely dropped 20%, its job is to verify the pipeline and get out of the way. Knowing when to stop is the feature: the tool's whole value is that when it says REAL_CHANGE, you can trust the number enough to act on it.
