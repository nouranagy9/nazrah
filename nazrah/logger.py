import csv
import os
import time


class UsageLogger:
    """Logs every phrase selection to a CSV file. This is the raw data for
    MYP Criterion D (Evaluating): which phrases actually get used, so the
    phrase set and grid layout can be iterated on based on real usage rather
    than guesswork.
    """

    def __init__(self, log_path="usage_log.csv"):
        self.log_path = log_path
        if not os.path.isfile(self.log_path):
            with open(self.log_path, "w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(["timestamp", "phrase_id", "phrase_text_ar"])

    def log_selection(self, phrase):
        with open(self.log_path, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(
                [time.strftime("%Y-%m-%d %H:%M:%S"), phrase.id, phrase.text_ar]
            )

    def most_used(self, top_n=5):
        if not os.path.isfile(self.log_path):
            return []
        counts = {}
        with open(self.log_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                counts[row["phrase_id"]] = counts.get(row["phrase_id"], 0) + 1
        return sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:top_n]
