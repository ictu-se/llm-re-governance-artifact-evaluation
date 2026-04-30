import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path


DIMENSIONS = [
    "correctness_0_2",
    "completeness_0_2",
    "traceability_usefulness_0_2",
    "governance_adequacy_0_2",
    "hallucination_risk_0_2",
]


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def fleiss_kappa(items: list[list[int]]) -> float:
    if not items:
        return float("nan")
    labels = sorted({score for item in items for score in item})
    n_raters = len(items[0])
    if n_raters < 2:
        return float("nan")
    p_j = {label: 0 for label in labels}
    p_i = []
    for item in items:
        counts = Counter(item)
        agreement = sum(count * count for count in counts.values()) - n_raters
        p_i.append(agreement / (n_raters * (n_raters - 1)))
        for label in labels:
            p_j[label] += counts[label]
    n_items = len(items)
    for label in labels:
        p_j[label] /= n_items * n_raters
    p_bar = sum(p_i) / n_items
    p_e = sum(value * value for value in p_j.values())
    return 1.0 if p_e == 1 else (p_bar - p_e) / (1 - p_e)


def krippendorff_alpha_ordinal(items: list[list[int]]) -> float:
    if not items:
        return float("nan")
    observed_num = 0.0
    observed_den = 0
    values = []
    for item in items:
        values.extend(item)
        for i, a in enumerate(item):
            for j, b in enumerate(item):
                if i != j:
                    observed_num += (a - b) ** 2
                    observed_den += 1
    observed = observed_num / observed_den if observed_den else 0.0
    counts = Counter(values)
    total = sum(counts.values())
    expected_num = 0.0
    for a, ca in counts.items():
        for b, cb in counts.items():
            expected_num += ca * cb * ((a - b) ** 2)
    expected = expected_num / (total * (total - 1)) if total > 1 else 0.0
    return 1.0 if expected == 0 else 1 - observed / expected


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ratings", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    rows = read_csv(Path(args.ratings))
    out_rows = []
    for dim in DIMENSIONS:
        grouped = defaultdict(list)
        for row in rows:
            value = row.get(dim, "").strip()
            if value:
                grouped[(row["model"], row["task_id"])].append(int(float(value)))
        complete_items = [scores for scores in grouped.values() if len(scores) >= 2]
        out_rows.append(
            {
                "dimension": dim,
                "n_items": len(complete_items),
                "min_raters_per_item": min(len(scores) for scores in complete_items) if complete_items else 0,
                "max_raters_per_item": max(len(scores) for scores in complete_items) if complete_items else 0,
                "fleiss_kappa": round(fleiss_kappa(complete_items), 4),
                "krippendorff_alpha_ordinal": round(krippendorff_alpha_ordinal(complete_items), 4),
            }
        )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        writer.writeheader()
        writer.writerows(out_rows)


if __name__ == "__main__":
    main()
