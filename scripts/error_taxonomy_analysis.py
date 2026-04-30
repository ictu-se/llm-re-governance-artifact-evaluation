import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def classify(row: dict) -> str:
    if row.get("error"):
        return "runtime_or_timeout"
    if float(row.get("rater_a_parse_ok", row.get("parse_ok", 0)) or 0) < 1:
        return "malformed_or_unparseable"
    dims = {
        "correctness": float(row["correctness"]),
        "completeness": float(row["completeness"]),
        "traceability_usefulness": float(row["traceability_usefulness"]),
        "governance_adequacy": float(row["governance_adequacy"]),
        "hallucination_risk": float(row["hallucination_risk"]),
    }
    if dims["correctness"] < 1:
        return "incorrect_or_off_context"
    if dims["completeness"] < 2:
        return "incomplete_artifact"
    if dims["traceability_usefulness"] < 1:
        return "missing_traceability"
    if dims["traceability_usefulness"] < 2:
        return "generic_traceability"
    if dims["governance_adequacy"] < 2:
        return "weak_governance"
    if dims["hallucination_risk"] < 2:
        return "unsupported_or_risky_content"
    return "no_major_flag"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rubric-glob", default="results/final/*_rubric.csv")
    parser.add_argument("--out-summary", required=True)
    parser.add_argument("--out-by-model", required=True)
    args = parser.parse_args()

    rows = []
    for path in sorted(Path(".").glob(args.rubric_glob)):
        rows.extend(read_csv(path))

    summary = Counter()
    by_model = defaultdict(Counter)
    for row in rows:
        category = classify(row)
        summary[category] += 1
        by_model[row["model"]][category] += 1

    total = sum(summary.values())
    summary_rows = [
        {
            "category": category,
            "n": count,
            "percent": round(count / total * 100, 2) if total else 0.0,
        }
        for category, count in summary.most_common()
    ]

    model_rows = []
    for model, counts in sorted(by_model.items()):
        model_total = sum(counts.values())
        for category, count in counts.most_common():
            model_rows.append(
                {
                    "model": model,
                    "category": category,
                    "n": count,
                    "percent": round(count / model_total * 100, 2) if model_total else 0.0,
                }
            )

    write_csv(Path(args.out_summary), summary_rows)
    write_csv(Path(args.out_by_model), model_rows)
    print(f"wrote={args.out_summary}")
    print(f"wrote={args.out_by_model}")


if __name__ == "__main__":
    main()
