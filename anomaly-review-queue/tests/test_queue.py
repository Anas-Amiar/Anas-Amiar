import unittest

from anomaly_queue import (
    DEMO_ANOMALIES,
    Decision,
    ReviewQueue,
    demo_series,
    detect,
    generate_series,
)
from anomaly_queue.generate import DEMO_EXPLAINABLE


class DetectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.detections = {d.day: d for d in detect(demo_series(), eval_days=42)}

    def test_outage_is_auto_alerted(self) -> None:
        self.assertEqual(self.detections[92].decision, Decision.AUTO_ALERT)

    def test_positive_spike_is_flagged_too(self) -> None:
        # "Up and to the right" can still be a data bug; direction is not health.
        self.assertEqual(self.detections[110].decision, Decision.AUTO_ALERT)

    def test_subtle_regression_goes_to_review_not_ignore(self) -> None:
        self.assertEqual(self.detections[117].decision, Decision.NEEDS_REVIEW)

    def test_holiday_dip_goes_to_review_not_alert(self) -> None:
        self.assertEqual(self.detections[121].decision, Decision.NEEDS_REVIEW)

    def test_clean_series_stays_quiet(self) -> None:
        series = generate_series(days=126, seed=99)
        flagged = [
            d for d in detect(series, eval_days=42) if d.decision != Decision.IGNORE
        ]
        self.assertEqual(flagged, [])

    def test_weekend_days_are_not_anomalies(self) -> None:
        # Weekends run ~35% below weekdays; a weekday-blind detector would
        # page every Saturday. Ours must not.
        weekend_days = [d for d, det in self.detections.items()
                        if d % 7 in (5, 6) and d not in DEMO_ANOMALIES
                        and d not in DEMO_EXPLAINABLE
                        and det.decision != Decision.IGNORE]
        self.assertEqual(weekend_days, [])


class QueueTests(unittest.TestCase):
    def test_review_flow_and_benchmark(self) -> None:
        detections = detect(demo_series(), eval_days=42)
        queue = ReviewQueue()
        queue.add_all(detections)

        pending = queue.pending_review()
        self.assertEqual({d.day for d in pending}, {117, 121})

        for item in pending:
            queue.submit_review(item.day, item.day in DEMO_ANOMALIES)
        for d in detections:
            if d.decision == Decision.AUTO_ALERT:
                queue.submit_review(d.day, d.day in DEMO_ANOMALIES)

        self.assertEqual(queue.pending_review(), [])

        report = queue.benchmark(set(DEMO_ANOMALIES), [d.day for d in detections])
        by_band = {b.band: b for b in report.bands}
        self.assertEqual(by_band[Decision.AUTO_ALERT].precision, 1.0)
        self.assertEqual(by_band[Decision.NEEDS_REVIEW].precision, 0.5)
        self.assertEqual(report.recall, 1.0)
        self.assertEqual(report.missed_days, [])


if __name__ == "__main__":
    unittest.main()
