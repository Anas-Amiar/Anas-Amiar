"""Five experiments, one honest checker.

    python demo.py

The checker never learns the true effect behind each dataset — it has to
earn its verdicts from the numbers, and refuse when the numbers can't
support one.
"""

from ab_honesty import check
from ab_honesty.simulate import (
    clean_win,
    find_peeking_seed,
    peeking,
    srm_bug,
    true_null_powered,
    underpowered,
)


def main() -> None:
    scenarios = [
        ("A real 15% lift, pre-registered, fully powered", clean_win()),
        ("Treatment crashes for 12% of users before logging", srm_bug()),
        ("A real lift, but only 1,500 users per arm", underpowered()),
        ("NO true effect; PM peeked daily and stopped at p<0.05", peeking(find_peeking_seed())),
        ("No effect, fully powered — a trustworthy negative", true_null_powered()),
    ]
    for truth, data in scenarios:
        print("=" * 72)
        print(f"Ground truth (hidden from the checker): {truth}")
        print(check(data).describe())
        print()


if __name__ == "__main__":
    main()
