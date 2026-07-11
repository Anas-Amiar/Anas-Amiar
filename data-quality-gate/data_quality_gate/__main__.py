"""CI entry point.

    python -m data_quality_gate --scenario safe_refactor   # exit 0
    python -m data_quality_gate --scenario lossy_filter    # exit 1, merge blocked

In a real deployment the --scenario flag is replaced by "run the changed
pipeline against the fixture inputs" — the gate logic doesn't change.
"""

import argparse
import sys

from . import ORDERS_CONTRACT, Scenario, candidate, golden, run_gate


def main() -> int:
    parser = argparse.ArgumentParser(prog="data_quality_gate")
    parser.add_argument(
        "--scenario",
        type=Scenario,
        choices=list(Scenario),
        default=Scenario.SAFE_REFACTOR,
        help="which simulated pipeline change to gate",
    )
    args = parser.parse_args()

    result = run_gate(golden(), candidate(args.scenario), ORDERS_CONTRACT)
    print(result.describe())
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
