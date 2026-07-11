"""Gate five simulated pipeline changes against the golden dataset.

    python demo.py
"""

from data_quality_gate import ORDERS_CONTRACT, Scenario, candidate, golden, run_gate

HEADLINES = {
    Scenario.SAFE_REFACTOR: "Refactor: same logic, cleaner SQL",
    Scenario.LOSSY_FILTER: "Simplified WHERE clause (silently drops APAC)",
    Scenario.UNIT_BUG: "New payment provider reports cents, not dollars",
    Scenario.DUPLICATE_JOIN: "Join rewrite duplicates 8% of rows",
    Scenario.NULL_LEAK: "Refactor stops coalescing region",
}


def main() -> None:
    golden_rows = golden()
    for scenario, headline in HEADLINES.items():
        result = run_gate(golden_rows, candidate(scenario), ORDERS_CONTRACT)
        print("=" * 72)
        print(f"Proposed change: {headline}")
        print(result.describe())
        print(f"CI outcome: {'merge allowed' if result.passed else 'MERGE BLOCKED'}")
        print()


if __name__ == "__main__":
    main()
