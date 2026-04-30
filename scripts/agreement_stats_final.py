import argparse
import csv
import math
import random
import re
from collections import Counter, defaultdict
from pathlib import Path


DIMENSIONS = [
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


def cohen_kappa(a: list[int], b: list[int]) -> float:
    n = len(a)
    if n == 0:
        return float("nan")
    labels = sorted(set(a) | set(b))
    observed = sum(1 for x, y in zip(a, b) if x == y) / n
    ca = Counter(a)
    cb = Counter(b)
    expected = sum((ca[label] / n) * (cb[label] / n) for label in labels)
    if expected == 1:
        return 1.0
    return (observed - expected) / (1 - expected)


def krippendorff_alpha_ordinal(pairs: list[tuple[int, int]]) -> float:
    values = [v for pair in pairs for v in pair]
    if not values:
        return float("nan")
    counts = Counter(values)
    n_total = sum(counts.values())
    do_num = sum((a - b) ** 2 for a, b in pairs)
    do_den = len(pairs)
    observed = do_num / do_den if do_den else 0
    expected = 0.0
    for a, ca in counts.items():
        for b, cb in counts.items():
            expected += ca * cb * ((a - b) ** 2)
    expected = expected / (n_total * (n_total - 1)) if n_total > 1 else 0
    if expected == 0:
        return 1.0
    return 1 - observed / expected


def model_family(model: str) -> str:
    name = model.split(":")[0]
    if name.startswith("qwen2.5-coder"):
        return "qwen2.5-coder"
    if name.startswith("qwen2.5"):
        return "qwen2.5"
    if name.startswith("qwen3"):
        return "qwen3"
    if name.startswith("granite-code"):
        return "granite-code"
    if name.startswith("starcoder2"):
        return "starcoder2"
    return name


def model_size_b(model: str) -> float:
    match = re.search(r":([0-9.]+)b", model.lower())
    return float(match.group(1)) if match else float("nan")


def mean(vals: list[float]) -> float:
    return sum(vals) / len(vals) if vals else float("nan")


def bootstrap_ci(vals: list[float], iterations: int = 2000) -> tuple[float, float]:
    if not vals:
        return float("nan"), float("nan")
    rng = random.Random(17)
    means = []
    for _ in range(iterations):
        sample = [vals[rng.randrange(len(vals))] for _ in vals]
        means.append(mean(sample))
    means.sort()
    return means[int(0.025 * iterations)], means[int(0.975 * iterations)]


def cliffs_delta(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return float("nan")
    gt = lt = 0
    for x in a:
        for y in b:
            if x > y:
                gt += 1
            elif x < y:
                lt += 1
    return (gt - lt) / (len(a) * len(b))


def mann_whitney_u(a: list[float], b: list[float]) -> tuple[float, float]:
    combined = sorted([(v, "a") for v in a] + [(v, "b") for v in b], key=lambda item: item[0])
    ranks = {}
    i = 0
    while i < len(combined):
        j = i
        while j < len(combined) and combined[j][0] == combined[i][0]:
            j += 1
        avg_rank = (i + 1 + j) / 2
        for k in range(i, j):
            ranks[k] = avg_rank
        i = j
    rank_a = sum(ranks[i] for i, item in enumerate(combined) if item[1] == "a")
    n1, n2 = len(a), len(b)
    u1 = rank_a - n1 * (n1 + 1) / 2
    mean_u = n1 * n2 / 2
    sd_u = math.sqrt(n1 * n2 * (n1 + n2 + 1) / 12)
    if sd_u == 0:
        return u1, 1.0
    z = (u1 - mean_u) / sd_u
    p = math.erfc(abs(z) / math.sqrt(2))
    return u1, p


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rubric-glob", required=True)
    parser.add_argument("--outdir", required=True)
    args = parser.parse_args()

    paths = sorted(Path(".").glob(args.rubric_glob))
    rows = []
    for path in paths:
        rows.extend(read_csv(path))

    for row in rows:
        row["family"] = model_family(row["model"])
        row["size_b"] = model_size_b(row["model"])

    agreement_rows = []
    all_pairs = []
    for dim in DIMENSIONS:
        a = [int(float(row[f"rater_a_{dim}"])) for row in rows]
        b = [int(float(row[f"rater_b_{dim}"])) for row in rows]
        pairs = list(zip(a, b))
        all_pairs.extend(pairs)
        agreement_rows.append(
            {
                "dimension": dim,
                "n": len(pairs),
                "cohen_kappa": round(cohen_kappa(a, b), 4),
                "krippendorff_alpha_ordinal": round(krippendorff_alpha_ordinal(pairs), 4),
            }
        )
    agreement_rows.append(
        {
            "dimension": "all_dimensions",
            "n": len(all_pairs),
            "cohen_kappa": "",
            "krippendorff_alpha_ordinal": round(krippendorff_alpha_ordinal(all_pairs), 4),
        }
    )

    by_model = defaultdict(list)
    by_family = defaultdict(list)
    by_size = defaultdict(list)
    for row in rows:
        score = float(row["rubric_total"])
        by_model[row["model"]].append(score)
        by_family[row["family"]].append(score)
        by_size[str(row["size_b"])].append(score)

    model_rows = []
    for model, vals in sorted(by_model.items()):
        lo, hi = bootstrap_ci(vals)
        model_rows.append(
            {
                "model": model,
                "family": model_family(model),
                "size_b": model_size_b(model),
                "n": len(vals),
                "mean_rubric_total": round(mean(vals), 4),
                "ci95_low": round(lo, 4),
                "ci95_high": round(hi, 4),
            }
        )

    family_rows = []
    for family, vals in sorted(by_family.items()):
        lo, hi = bootstrap_ci(vals)
        family_rows.append(
            {
                "family": family,
                "n": len(vals),
                "mean_rubric_total": round(mean(vals), 4),
                "ci95_low": round(lo, 4),
                "ci95_high": round(hi, 4),
            }
        )

    comparison_rows = []
    families = sorted(by_family)
    for i, fa in enumerate(families):
        for fb in families[i + 1 :]:
            u, p = mann_whitney_u(by_family[fa], by_family[fb])
            comparison_rows.append(
                {
                    "group_a": fa,
                    "group_b": fb,
                    "n_a": len(by_family[fa]),
                    "n_b": len(by_family[fb]),
                    "mean_a": round(mean(by_family[fa]), 4),
                    "mean_b": round(mean(by_family[fb]), 4),
                    "cliffs_delta_a_minus_b": round(cliffs_delta(by_family[fa], by_family[fb]), 4),
                    "mann_whitney_u": round(u, 4),
                    "p_value_normal_approx": round(p, 6),
                }
            )

    outdir = Path(args.outdir)
    write_csv(outdir / "rubric_agreement.csv", agreement_rows)
    write_csv(outdir / "final_model_rubric_summary.csv", model_rows)
    write_csv(outdir / "final_family_rubric_summary.csv", family_rows)
    write_csv(outdir / "statistical_comparisons_family.csv", comparison_rows)


if __name__ == "__main__":
    main()
