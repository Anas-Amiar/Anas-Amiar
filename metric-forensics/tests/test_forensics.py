import unittest

from metric_forensics import FailureMode, Verdict, baseline_runs, diagnose, run_pipeline


class ForensicsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.baseline = baseline_runs(days=14)

    def _diagnose(self, failure: FailureMode):
        return diagnose(self.baseline, run_pipeline(day=15, failure=failure))

    def test_clean_day_is_no_anomaly(self) -> None:
        diagnosis = self._diagnose(FailureMode.NONE)
        self.assertEqual(diagnosis.verdict, Verdict.NO_ANOMALY)
        self.assertIsNone(diagnosis.first_broken_stage)

    def test_source_dropout_blames_ingest(self) -> None:
        diagnosis = self._diagnose(FailureMode.SOURCE_DROPOUT)
        self.assertEqual(diagnosis.verdict, Verdict.DATA_ISSUE)
        self.assertEqual(diagnosis.first_broken_stage, "ingest")

    def test_schema_change_blames_staging_not_aggregate(self) -> None:
        # Revenue is zero, which also looks catastrophic at the aggregate
        # stage — the engine must still blame the earliest broken stage.
        diagnosis = self._diagnose(FailureMode.SCHEMA_CHANGE)
        self.assertEqual(diagnosis.verdict, Verdict.DATA_ISSUE)
        self.assertEqual(diagnosis.first_broken_stage, "staging")

    def test_join_fanout_blames_enrich(self) -> None:
        diagnosis = self._diagnose(FailureMode.JOIN_FANOUT)
        self.assertEqual(diagnosis.verdict, Verdict.DATA_ISSUE)
        self.assertEqual(diagnosis.first_broken_stage, "enrich")

    def test_timezone_shift_blames_aggregate(self) -> None:
        diagnosis = self._diagnose(FailureMode.TIMEZONE_SHIFT)
        self.assertEqual(diagnosis.verdict, Verdict.DATA_ISSUE)
        self.assertEqual(diagnosis.first_broken_stage, "aggregate")

    def test_real_change_is_not_blamed_on_the_pipeline(self) -> None:
        diagnosis = self._diagnose(FailureMode.REAL_CHANGE)
        self.assertEqual(diagnosis.verdict, Verdict.REAL_CHANGE)
        self.assertIsNone(diagnosis.first_broken_stage)
        self.assertLess(diagnosis.change_pct, -10)

    def test_every_diagnosis_reports_all_stages(self) -> None:
        for failure in FailureMode:
            diagnosis = self._diagnose(failure)
            self.assertEqual(
                [r.stage for r in diagnosis.stage_reports],
                ["ingest", "staging", "enrich", "aggregate"],
            )


if __name__ == "__main__":
    unittest.main()
