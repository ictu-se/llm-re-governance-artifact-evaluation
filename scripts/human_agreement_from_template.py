import argparse
import csv
from collections import Counter
from pathlib import Path


DIMENSIONS = [
    "correctness_0_2",
    "completeness_0_2",
    "traceability_usefulness_0_2",
    "governance_adequacy_0_2",
    "hallucination_risk_0_2",
]


def cohen_kappa(a: list[int], b: list[int]) -> float:
    n = len(a)
    if n == 0:
        return float("nan")
    observed = sum(1 for x, y in zip(a, b) if x == y) / n
    labels = sorted(set(a) | set(b))
    ca = Counter(a)
    cb = Counter(b)
    expected = sum((ca[label] / n) * (cb[label] / n) for label in labels)
    return 1.0 if expected == 1 else (observed - expected) / (1 - expected)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ratings", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    with Path(args.ratings).open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    grouped = {}
    for row in rows:
        key = (row["model"], row["task_id"])
        grouped.setdefault(key, []).append(row)

    out_rows = []
    for dim in DIMENSIONS:
        a_vals = []
        b_vals = []
        for ratings in grouped.values():
            complete = [r for r in ratings if r.get(dim, "").strip() != ""]
            if len(complete) >= 2:
                a_vals.append(int(float(complete[0][dim])))
                b_vals.append(int(float(complete[1][dim])))
        out_rows.append({"dimension": dim, "n_pairs": len(a_vals), "cohen_kappa": round(cohen_kappa(a_vals, b_vals), 4)})

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        writer.writeheader()
        writer.writerows(out_rows)


if __name__ == "__main__":
    main()
