import argparse
import csv
import math
from pathlib import Path


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else float("nan")


def median(values: list[float]) -> float:
    if not values:
        return float("nan")
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2


def normal_cdf(value: float) -> float:
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


def wilcoxon_signed_rank(diffs: list[float]) -> tuple[int, float, float]:
    nonzero = [d for d in diffs if d != 0]
    n = len(nonzero)
    if n == 0:
        return 0, 0.0, 1.0

    abs_with_sign = sorted((abs(d), 1 if d > 0 else -1) for d in nonzero)
    ranks = []
    i = 0
    while i < n:
        j = i
        while j < n and abs_with_sign[j][0] == abs_with_sign[i][0]:
            j += 1
        avg_rank = (i + 1 + j) / 2
        for k in range(i, j):
            ranks.append((avg_rank, abs_with_sign[k][1]))
        i = j

    w_plus = sum(rank for rank, sign in ranks if sign > 0)
    expected = n * (n + 1) / 4
    variance = n * (n + 1) * (2 * n + 1) / 24
    if variance == 0:
        return n, w_plus, 1.0
    z = (w_plus - expected) / math.sqrt(variance)
    p = 2 * (1 - normal_cdf(abs(z)))
    return n, w_plus, p


def paired_effect_size(diffs: list[float]) -> float:
    nonzero = [d for d in diffs if d != 0]
    if not nonzero:
        return 0.0
    positive = sum(1 for d in nonzero if d > 0)
    negative = sum(1 for d in nonzero if d < 0)
    return (positive - negative) / len(nonzero)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rubric-glob", default="results/final/*_rubric.csv")
    parser.add_argument("--models", nargs="+", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    scores: dict[str, dict[str, float]] = {}
    for path in sorted(Path(".").glob(args.rubric_glob)):
        for row in read_csv(path):
            model = row["model"]
            if model in args.models:
                scores.setdefault(model, {})[row["task_id"]] = float(row["rubric_total"])

    rows = []
    for i, model_a in enumerate(args.models):
        for model_b in args.models[i + 1 :]:
            common_tasks = sorted(set(scores.get(model_a, {})) & set(scores.get(model_b, {})))
            diffs = [scores[model_a][task_id] - scores[model_b][task_id] for task_id in common_tasks]
            n_nonzero, w_plus, p_value = wilcoxon_signed_rank(diffs)
            rows.append(
                {
                    "model_a": model_a,
                    "model_b": model_b,
                    "n_common_tasks": len(common_tasks),
                    "mean_a": round(mean([scores[model_a][t] for t in common_tasks]), 4),
                    "mean_b": round(mean([scores[model_b][t] for t in common_tasks]), 4),
                    "mean_diff_a_minus_b": round(mean(diffs), 4),
                    "median_diff_a_minus_b": round(median(diffs), 4),
                    "nonzero_pairs": n_nonzero,
                    "wilcoxon_w_plus": round(w_plus, 4),
                    "p_value_normal_approx": round(p_value, 6),
                    "paired_sign_effect": round(paired_effect_size(diffs), 4),
                }
            )

    if not rows:
        raise SystemExit("No paired comparisons generated. Check model names and rubric paths.")
    write_csv(Path(args.out), rows)
    print(f"wrote={args.out}")
    print(f"rows={len(rows)}")


if __name__ == "__main__":
    main()
