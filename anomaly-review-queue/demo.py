"""End to end: detect -> triage -> human review -> benchmark.

    python demo.py

Four anomalies are planted in the eval window, from a -45% outage down to
a -7% config regression. The detector never sees the labels; the simulated
human reviewer does (they're the answer key), and their answers become the
accuracy benchmark.
"""

from anomaly_queue import DEMO_ANOMALIES, Decision, ReviewQueue, demo_series, detect


def main() -> None:
    series = demo_series()
    detections = detect(series, eval_days=42)
    flagged = [d for d in detections if d.decision != Decision.IGNORE]

    print("Detections over the 42-day eval window (ignored days omitted):")
    for d in flagged:
        print("  " + d.describe())

    queue = ReviewQueue()  # use a file path to persist across runs
    queue.add_all(detections)

    # A human works the review queue. In this demo the 'human' consults the
    # generator's answer key; in production this is your on-call analyst.
    print("\nHuman works the review queue:")
    for item in queue.pending_review():
        is_real = item.day in DEMO_ANOMALIES
        queue.submit_review(item.day, is_real)
        print(f"  day {item.day}: score {item.score:.1f} -> human says "
              f"{'REAL ANOMALY' if is_real else 'false alarm'}")

    # Auto-alerts get audited too — that's how you find out if the
    # auto threshold deserves its confidence.
    for d in detections:
        if d.decision == Decision.AUTO_ALERT:
            queue.submit_review(d.day, d.day in DEMO_ANOMALIES)

    report = queue.benchmark(
        true_anomaly_days=set(DEMO_ANOMALIES),
        eval_days=[d.day for d in detections],
    )
    print("\nBenchmark (built from the human labels):")
    for band in report.bands:
        precision = f"{band.precision:.0%}" if band.precision is not None else "n/a"
        print(f"  {band.band.value:<13} total={band.total:<3} reviewed={band.reviewed:<3} "
              f"precision={precision}")
    recall = f"{report.recall:.0%}" if report.recall is not None else "n/a"
    print(f"  recall on planted anomalies: {recall} "
          f"({report.caught}/{report.true_anomalies_in_window}, missed days: {report.missed_days or 'none'})")


if __name__ == "__main__":
    main()
