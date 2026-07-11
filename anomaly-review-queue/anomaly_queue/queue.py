"""SQLite-backed review queue and benchmark.

Detections land here. Ambiguous ones wait for a human; every human answer
is stored and becomes benchmark data. The benchmark is the payoff: it
measures per-band precision, which tells you whether the thresholds are
earning their keep — and it only exists because the corrections were
captured instead of thrown away in a Slack thread.
"""

import sqlite3

from .models import BandStats, BenchmarkReport, Decision, Detection

SCHEMA = """
CREATE TABLE IF NOT EXISTS detections (
    day INTEGER PRIMARY KEY,
    value REAL NOT NULL,
    expected REAL NOT NULL,
    score REAL NOT NULL,
    decision TEXT NOT NULL,
    human_label INTEGER  -- NULL until reviewed; 1 real anomaly, 0 false alarm
);
"""


class ReviewQueue:
    def __init__(self, db_path: str = ":memory:") -> None:
        self.conn = sqlite3.connect(db_path)
        self.conn.execute(SCHEMA)

    def add_all(self, detections: list[Detection]) -> None:
        self.conn.executemany(
            "INSERT OR REPLACE INTO detections (day, value, expected, score, decision) "
            "VALUES (?, ?, ?, ?, ?)",
            [(d.day, d.value, d.expected, d.score, d.decision.value) for d in detections],
        )
        self.conn.commit()

    def pending_review(self) -> list[Detection]:
        rows = self.conn.execute(
            "SELECT day, value, expected, score, decision FROM detections "
            "WHERE decision = ? AND human_label IS NULL ORDER BY score DESC",
            (Decision.NEEDS_REVIEW.value,),
        ).fetchall()
        return [
            Detection(day=r[0], value=r[1], expected=r[2], score=r[3], decision=Decision(r[4]))
            for r in rows
        ]

    def submit_review(self, day: int, is_real_anomaly: bool) -> None:
        self.conn.execute(
            "UPDATE detections SET human_label = ? WHERE day = ?",
            (int(is_real_anomaly), day),
        )
        self.conn.commit()

    def benchmark(self, true_anomaly_days: set[int], eval_days: list[int]) -> BenchmarkReport:
        """Per-band precision from human labels, plus recall against the
        answer key for the eval window."""
        bands = []
        for band in Decision:
            rows = self.conn.execute(
                "SELECT human_label FROM detections WHERE decision = ?",
                (band.value,),
            ).fetchall()
            labels = [r[0] for r in rows]
            judged = [l for l in labels if l is not None]
            bands.append(
                BandStats(
                    band=band,
                    total=len(labels),
                    reviewed=len(judged),
                    true_positives=sum(1 for l in judged if l == 1),
                    false_positives=sum(1 for l in judged if l == 0),
                )
            )

        flagged_days = {
            r[0]
            for r in self.conn.execute(
                "SELECT day FROM detections WHERE decision != ?", (Decision.IGNORE.value,)
            ).fetchall()
        }
        in_window = true_anomaly_days & set(eval_days)
        caught = len(in_window & flagged_days)
        return BenchmarkReport(
            bands=bands,
            true_anomalies_in_window=len(in_window),
            caught=caught,
            missed_days=sorted(in_window - flagged_days),
        )
