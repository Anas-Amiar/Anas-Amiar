# The two-minute version

## The problem

Code changes to data pipelines get reviewed like code: does it read well, does it run, do the unit tests pass. But the thing a pipeline change actually breaks is the *data*, and nobody diffs the data. A cleaner WHERE clause that accidentally excludes a region passes every code review — the SQL is valid, tests are green, and the damage only shows up as a dashboard that's quietly wrong for a week.

## The insight

I already built this tool once, for prompts. My model regression detector freezes a golden dataset, runs every prompt change against it, and blocks the merge if accuracy drops. A data pipeline is the same shape of problem: the output is a claim, the change is a risk, and the fix is a frozen reference plus a diff with tolerances.

So the contract is pydantic, the golden dataset is the frozen reference, and the gate is a CI step with an exit code. Five checks: row count drift, primary-key uniqueness, null rates, value ranges, and distribution drift.

## The part I'm proud of

The cents/dollars scenario. A new payment provider reports amounts in minor units and nobody divides by 100. Look at what the usual checks see: same row count, same schema, every value is a valid positive float. Four of my five checks pass. It's only the Population Stability Index — comparing the *shape* of the amount distribution against golden — that screams (PSI 7.66 against a 0.1 threshold, which is roughly "this is a different dataset").

There's a test that pins this: the unit bug must be caught by PSI alone, with the row count check explicitly asserted as passing. Deleting the PSI check makes that test fail — which is exactly the property I want, because that's the check someone would delete as "too sensitive".

## The design decision that matters

Tolerances, not equality. The safe-refactor scenario reorders rows and re-rounds floats; a naive diff would block it, and a gate that blocks safe changes gets disabled within a month — then it's not a gate, it's a comment. Every threshold in the contract encodes "how much drift is normal here": ±5% rows, 1% nulls, PSI under 0.1. The gate's real job isn't catching bugs; it's staying trusted enough to be allowed to keep catching bugs.
