import unittest

from data_quality_gate import (
    ORDERS_CONTRACT,
    Scenario,
    candidate,
    golden,
    population_stability_index,
    run_gate,
)


class GateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.golden = golden()

    def _gate(self, scenario: Scenario):
        return run_gate(self.golden, candidate(scenario), ORDERS_CONTRACT)

    def test_safe_refactor_passes(self) -> None:
        result = self._gate(Scenario.SAFE_REFACTOR)
        self.assertTrue(result.passed, result.describe())

    def test_lossy_filter_blocked_on_row_count(self) -> None:
        result = self._gate(Scenario.LOSSY_FILTER)
        self.assertFalse(result.passed)
        self.assertIn("row_count", [v.check for v in result.violations])

    def test_unit_bug_blocked_on_distribution_not_row_count(self) -> None:
        # Same number of rows, same schema, every value "valid" — only the
        # distribution gives the cents/dollars bug away.
        result = self._gate(Scenario.UNIT_BUG)
        self.assertFalse(result.passed)
        checks = [v.check for v in result.violations]
        self.assertIn("distribution_psi", checks)
        self.assertNotIn("row_count", checks)

    def test_duplicate_join_blocked_on_primary_key(self) -> None:
        result = self._gate(Scenario.DUPLICATE_JOIN)
        self.assertFalse(result.passed)
        self.assertIn("primary_key_unique", [v.check for v in result.violations])

    def test_null_leak_blocked_on_null_rate(self) -> None:
        result = self._gate(Scenario.NULL_LEAK)
        self.assertFalse(result.passed)
        self.assertIn("null_rate", [v.check for v in result.violations])

    def test_psi_is_near_zero_for_same_distribution(self) -> None:
        values = [float(r["amount"]) for r in self.golden]
        self.assertLess(population_stability_index(values, values), 0.01)

    def test_psi_detects_scale_shift(self) -> None:
        values = [float(r["amount"]) for r in self.golden]
        shifted = [v * 100 for v in values]
        self.assertGreater(population_stability_index(values, shifted), 0.25)


if __name__ == "__main__":
    unittest.main()
