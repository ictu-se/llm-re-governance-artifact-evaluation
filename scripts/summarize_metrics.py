import argparse
import csv
from collections import defaultdict
from pathlib import Path


METRICS = [
    "parse_ok",
    "slot_coverage",
    "gold_keyword_recall",
    "risk_control_recall",
    "traceability_signal_recall",
    "elapsed_sec",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metrics", nargs="+", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    grouped = defaultdict(list)
    for path in args.metrics:
        with Path(path).open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                grouped[row["model"]].append(row)

    rows = []
    for model, items in sorted(grouped.items()):
        out = {"model": model, "n": len(items)}
        for metric in METRICS:
            vals = []
            for row in items:
                value = row.get(metric)
                if value not in (None, "", "None"):
                    vals.append(float(value))
            out[f"mean_{metric}"] = round(sum(vals) / len(vals), 4) if vals else ""
        rows.append(out)

    fieldnames = list(rows[0].keys())
    with Path(args.out).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
