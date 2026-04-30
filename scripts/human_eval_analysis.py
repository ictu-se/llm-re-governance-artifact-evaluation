import argparse
import csv
import math
from collections import Counter, defaultdict
from pathlib import Path


HUMAN_DIMS = [
    "correctness_0_2",
    "completeness_0_2",
    "traceability_usefulness_0_2",
    "governance_adequacy_0_2",
    "hallucination_risk_0_2",
]

AUTO_DIMS = [
    "correctness",
    "completeness",
    "traceability_usefulness",
    "governance_adequacy",
    "hallucination_risk",
]


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


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else float("nan")


def ranks(values: list[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    out = [0.0] * len(values)
    i = 0
    while i < len(indexed):
        j = i
        while j < len(indexed) and indexed[j][1] == indexed[i][1]:
            j += 1
        avg = (i + 1 + j) / 2
        for k in range(i, j):
            out[indexed[k][0]] = avg
        i = j
    return out


def pearson(a: list[float], b: list[float]) -> float:
    if len(a) < 2 or len(a) != len(b):
        return float("nan")
    ma, mb = mean(a), mean(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    da = math.sqrt(sum((x - ma) ** 2 for x in a))
    db = math.sqrt(sum((y - mb) ** 2 for y in b))
    return num / (da * db) if da and db else float("nan")


def spearman(a: list[float], b: list[float]) -> float:
    if len(a) < 2 or len(a) != len(b):
        return float("nan")
    return pearson(ranks(a), ranks(b))


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


def load_auto_scores(pattern: str) -> dict[tuple[str, str], dict]:
    scores = {}
    for path in sorted(Path(".").glob(pattern)):
        for row in read_csv(path):
            scores[(row["model"], row["task_id"])] = row
    return scores


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ratings", required=True)
    parser.add_argument("--rubric-glob", default="results/final/*_rubric.csv")
    parser.add_argument("--outdir", required=True)
    args = parser.parse_args()

    rating_rows = read_csv(Path(args.ratings))
    auto = load_auto_scores(args.rubric_glob)
    outdir = Path(args.outdir)

    synthetic_values = {row.get("synthetic_data", "").strip() for row in rating_rows if "synthetic_data" in row}
    is_synthetic = "1" in synthetic_values

    grouped = defaultdict(list)
    for row in rating_rows:
        grouped[(row["model"], row["task_id"])].append(row)

    agreement_rows = []
    for dim in HUMAN_DIMS:
        items = []
        for ratings in grouped.values():
            scores = [int(float(row[dim])) for row in ratings if row.get(dim, "").strip() != ""]
            if len(scores) >= 2:
                items.append(scores)
        agreement_rows.append(
            {
                "dimension": dim,
                "n_items": len(items),
                "min_raters_per_item": min((len(item) for item in items), default=0),
                "max_raters_per_item": max((len(item) for item in items), default=0),
                "fleiss_kappa": round(fleiss_kappa(items), 4),
                "krippendorff_alpha_ordinal": round(krippendorff_alpha_ordinal(items), 4),
                "synthetic_data_detected": int(is_synthetic),
            }
        )

    adjudicated_rows = []
    for (model, task_id), ratings in sorted(grouped.items()):
        row = {"model": model, "task_id": task_id}
        total = 0.0
        for hdim in HUMAN_DIMS:
            vals = [float(r[hdim]) for r in ratings if r.get(hdim, "").strip() != ""]
            value = mean(vals)
            row[hdim.replace("_0_2", "_mean")] = round(value, 4)
            total += value
        row["human_total_mean_0_10"] = round(total, 4)
        row["n_reviewers"] = len(ratings)
        row["synthetic_data_detected"] = int(is_synthetic)
        if (model, task_id) in auto:
            row["automated_total_0_10"] = float(auto[(model, task_id)]["rubric_total"])
        adjudicated_rows.append(row)

    by_model = defaultdict(list)
    for row in adjudicated_rows:
        by_model[row["model"]].append(float(row["human_total_mean_0_10"]))
    summary_rows = [
        {
            "model": model,
            "n_items": len(vals),
            "mean_human_total_0_10": round(mean(vals), 4),
            "synthetic_data_detected": int(is_synthetic),
        }
        for model, vals in sorted(by_model.items())
    ]

    paired_human = []
    paired_auto = []
    for row in adjudicated_rows:
        if row.get("automated_total_0_10", "") != "":
            paired_human.append(float(row["human_total_mean_0_10"]))
            paired_auto.append(float(row["automated_total_0_10"]))
    correlation_rows = [
        {
            "comparison": "automated_total_vs_mean_human_total",
            "n_items": len(paired_human),
            "pearson_r": round(pearson(paired_auto, paired_human), 4),
            "spearman_rho": round(spearman(paired_auto, paired_human), 4),
            "mean_difference_automated_minus_human": round(mean([a - h for a, h in zip(paired_auto, paired_human)]), 4),
            "synthetic_data_detected": int(is_synthetic),
        }
    ]

    write_csv(outdir / "human_agreement.csv", agreement_rows)
    write_csv(outdir / "human_item_mean_scores.csv", adjudicated_rows)
    write_csv(outdir / "human_model_score_summary.csv", summary_rows)
    write_csv(outdir / "human_automated_correlation.csv", correlation_rows)
    print(f"wrote={outdir}")
    print(f"synthetic_data_detected={int(is_synthetic)}")


if __name__ == "__main__":
    main()
