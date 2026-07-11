import unittest

from ab_honesty import (
    Verdict,
    check,
    normal_quantile,
    required_n_per_arm,
    srm_pvalue,
    two_proportion_pvalue,
)
from ab_honesty.simulate import (
    clean_win,
    find_peeking_seed,
    peeking,
    srm_bug,
    true_null_powered,
    underpowered,
)


class StatsTests(unittest.TestCase):
    def test_normal_quantile_matches_known_values(self) -> None:
        self.assertAlmostEqual(normal_quantile(0.975), 1.959964, places=4)
        self.assertAlmostEqual(normal_quantile(0.8), 0.841621, places=4)
        self.assertAlmostEqual(normal_quantile(0.5), 0.0, places=6)

    def test_equal_arms_are_not_significant(self) -> None:
        self.assertGreater(two_proportion_pvalue(100, 1000, 100, 1000), 0.99)

    def test_large_difference_is_significant(self) -> None:
        self.assertLess(two_proportion_pvalue(100, 1000, 200, 1000), 0.001)

    def test_srm_pvalue_flags_broken_split(self) -> None:
        self.assertLess(srm_pvalue(10000, 8800), 1e-10)
        self.assertGreater(srm_pvalue(10000, 9990), 0.5)

    def test_required_n_matches_standard_formula(self) -> None:
        # 10% baseline, 10% relative MDE, alpha 0.05, power 0.8 -> ~14.7k/arm.
        n = required_n_per_arm(0.10, 0.10)
        self.assertTrue(14000 < n < 15500, n)


class CheckerTests(unittest.TestCase):
    def test_clean_win_ships(self) -> None:
        self.assertEqual(check(clean_win()).verdict, Verdict.SHIP)

    def test_srm_invalidates_even_with_great_pvalue(self) -> None:
        report = check(srm_bug())
        self.assertEqual(report.verdict, Verdict.INVALID)
        # The p-value looked shippable — that's what makes SRM dangerous.
        self.assertLess(report.p_value, 0.05)

    def test_underpowered_refuses_to_conclude(self) -> None:
        report = check(underpowered())
        self.assertEqual(report.verdict, Verdict.KEEP_COLLECTING)
        self.assertLess(report.users_per_arm, report.required_per_arm)

    def test_peeked_significance_is_rejected(self) -> None:
        data = peeking(find_peeking_seed())
        report = check(data)
        self.assertLess(report.p_value, 0.05)  # the PM saw a "winner"
        self.assertNotEqual(report.verdict, Verdict.SHIP)

    def test_powered_null_is_a_confident_dont_ship(self) -> None:
        self.assertEqual(check(true_null_powered()).verdict, Verdict.DONT_SHIP)


if __name__ == "__main__":
    unittest.main()
