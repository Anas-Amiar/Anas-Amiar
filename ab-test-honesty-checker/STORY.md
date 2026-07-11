# The two-minute version

## The problem

In my prompt A/B testing project, the platform once refused to declare a winner at p=0.68 and made me collect 12,000 samples to get to p=0.014. That refusal was the most valuable thing it did. This project is that refusal, generalized: an analyzer for product experiments whose main feature is declining to conclude.

Because here's how most A/B "wins" actually happen: a PM watches the dashboard daily, the p-value dips under 0.05 on day 7 (as it will, eventually, by chance), the experiment stops, and a false winner ships with a celebratory Slack post.

## The insight

The three ways experiments lie have a strict priority order, and the checker enforces it:

1. **A broken split invalidates everything.** If the assignment logging crashes for 12% of treatment users, both conversion rates are biased and no amount of statistics downstream can fix it. The SRM check runs first, and its verdict is INVALID even when the p-value looks fantastic — there's a test that pins exactly that case, because "great p-value, broken experiment" is the most dangerous combination.
2. **Every peek raises the bar.** The checker counts the looks and divides alpha by them. Blunt Bonferroni, chosen deliberately: it never flatters the result.
3. **Underpowered means unanswered.** The honest output of a too-small test isn't a verdict, it's a number: collect 13,249 more users per arm.

## The part I'm proud of

The peeking simulation is honest about the mechanism. It doesn't inject a fake significant result — it simulates a true null, re-analyzes daily like a real dashboard, and stops when p < 0.05, exactly as the incentives push a real team to do. There's even a `find_peeking_seed()` helper that searches for a seed where this happens, and the point is how quickly it finds one: manufacturing a false winner under a true null takes a handful of tries.

And then the demo handed me a gift I didn't plan: in the underpowered scenario, a variant with a *true +10% lift* measured as a nominally significant *−19% loss* at 1,500 users per arm. The checker's KEEP_COLLECTING verdict didn't just avoid a missed win — it avoided killing a good feature based on a significant-looking lie in the wrong direction.

## What it isn't

It's not a sequential testing framework — no alpha-spending functions or Bayesian stopping rules, which is what a mature experimentation platform would use. Bonferroni over-corrects. I chose it because the failure mode of over-correcting is "wait longer", and the failure mode of the sophisticated thing misused is "ship noise". For a tool whose job is honesty, I'll take the conservative error.
