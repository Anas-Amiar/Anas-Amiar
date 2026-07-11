# A/B Test Honesty Checker

**An experiment analyzer that refuses to give you the answer you want.**

Most A/B test "wins" are one of three lies: a broken traffic split, a peeked p-value, or an underpowered sample. This checker runs those three checks *before* it will state a verdict — and when the data can't support a conclusion, the verdict is a sample count, not an opinion.

## The idea

An experiment result is a claim, not a fact. Three honesty checks, in the order that matters:

1. **Sample ratio mismatch (SRM).** If you configured a 50/50 split and got 53/47, users went missing from one arm in a non-random way, and both conversion rates are biased. Verdict: `INVALID`, regardless of how good the p-value looks. This check runs first because it invalidates everything downstream.
2. **Peeking correction.** Every interim look at the dashboard was a chance to stop on noise. The significance bar rises with the number of looks (Bonferroni — blunt, but never flattering).
3. **Power.** "Not significant" from an underpowered test is not evidence of no effect — and a *significant* result from one is probably inflated. Either way: `KEEP_COLLECTING`, with exactly how many more users you need.

## Run it

```bash
pip install pydantic
python demo.py
```

Five simulated experiments; the checker is never told the ground truth:

```
Ground truth (hidden from the checker): NO true effect; PM peeked daily and stopped at p<0.05
Experiment: cta_button_color
  control 8.29% vs treatment 10.14% (lift +22.4%), p=0.0375
  looks=7 (alpha adjusted 0.0071), srm_p=1, n=2100/arm of 14749 required
  VERDICT: KEEP_COLLECTING
    - p=0.0375 beats your alpha of 0.05, but you looked at this experiment 7 times ...
    - This is exactly how false winners get shipped. Keep collecting.
```

Two demo details worth noticing:

- The peeking scenario has **no true effect at all**. The simulator just re-analyzes daily and stops when p dips under 0.05, exactly like a dashboard-watching PM — and finds a "+22% winner" within a week. `find_peeking_seed()` shows how little searching that takes.
- The underpowered scenario has a **true +10% lift**, and at 1,500 users/arm it measured as a nominally significant **−19% loss**. Small samples don't just miss effects; they invert them.

## Tests

```bash
python -m unittest discover tests -v
```

Includes checks of the statistics themselves against known values (normal quantiles, the ~14.7k/arm sample size for a 10% MDE on a 10% baseline), plus a test asserting the SRM scenario is invalidated *even though its p-value looked shippable*.

## Design notes

- **Stats from scratch on the standard library** — normal CDF via `math.erf`, two-proportion z-test, chi-square SRM test, standard sample-size formula. No scipy; `pip install pydantic` is the whole setup.
- **The design is pre-registered.** Baseline rate, MDE, alpha, and power are declared in a pydantic `Design` model before the data arrives, and the checker holds the analysis to that — not to whatever threshold would make the result look good afterwards.
- **Verdicts are typed** (`SHIP` / `DONT_SHIP` / `KEEP_COLLECTING` / `INVALID`), so this can gate an experimentation platform's "conclude" button, not just print advice.
