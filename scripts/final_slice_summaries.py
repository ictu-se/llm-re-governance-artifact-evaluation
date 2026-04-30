import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


DIMENSIONS = [
    "correctness",
    "completeness",
    "traceability_usefulness",
    "governance_adequacy",
    "hallucination_risk",
]


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def sd(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = mean(values)
    return (sum((v - m) ** 2 for v in values) / (len(values) - 1)) ** 0.5


def family_of(model: str) -> str:
    if model.startswith("qwen2.5-coder"):
        return "qwen2.5-coder"
    if model.startswith("qwen2.5"):
        return "qwen2.5"
    if model.startswith("qwen3"):
        return "qwen3"
    if model.startswith("granite-code"):
        return "granite-code"
    if model.startswith("starcoder2"):
        return "starcoder2"
    return model.split(":")[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", required=True)
    parser.add_argument("--rubric-glob", default="results/final/*_rubric.csv")
    parser.add_argument("--outdir", required=True)
    args = parser.parse_args()

    task_rows = read_jsonl(Path(args.tasks))
    tasks = {row["task_id"]: row for row in task_rows}
    # The manuscript's robustness check treats the first four scenario
    # templates within each system type as the calibration slice. This keeps
    # all 20 system types represented in both calibration and holdout splits.
    calibration_ids = {row["task_id"] for row in task_rows if int(row["task_id"].split("-")[1]) <= 4}

    rubric_rows = []
    for path in sorted(Path(".").glob(args.rubric_glob)):
        for row in read_csv(path):
            task = tasks.get(row["task_id"])
            if task is None:
                continue
            row = dict(row)
            row["system_type"] = task["system_type"]
            row["split"] = "calibration" if row["task_id"] in calibration_ids else "holdout"
            row["family"] = family_of(row["model"])
            rubric_rows.append(row)

    non_starcoder = [row for row in rubric_rows if not row["model"].startswith("starcoder2")]

    by_system = defaultdict(list)
    for row in non_starcoder:
        by_system[row["system_type"]].append(float(row["rubric_total"]))
    system_rows = [
        {
            "system_type": key,
            "n": len(values),
            "mean_total": mean(values),
            "sd_total": sd(values),
        }
        for key, values in by_system.items()
    ]
    system_rows.sort(key=lambda row: (row["mean_total"], row["system_type"]))

    dimension_rows = []
    for dim in DIMENSIONS:
        values = [float(row[dim]) for row in non_starcoder]
        dimension_rows.append(
            {
                "dimension": dim,
                "n": len(values),
                "mean_score": mean(values),
                "sd_score": sd(values),
            }
        )

    def split_rows(group_key: str) -> list[dict]:
        grouped = defaultdict(lambda: defaultdict(list))
        for row in rubric_rows:
            grouped[row[group_key]][row["split"]].append(float(row["rubric_total"]))
        rows = []
        for key, split_values in grouped.items():
            calibration = split_values["calibration"]
            holdout = split_values["holdout"]
            rows.append(
                {
                    group_key: key,
                    "calibration_n": len(calibration),
                    "calibration_mean": mean(calibration),
                    "holdout_n": len(holdout),
                    "holdout_mean": mean(holdout),
                    "delta_holdout_minus_calibration": mean(holdout) - mean(calibration),
                    "_overall_mean": mean(calibration + holdout),
                }
            )
        rows.sort(key=lambda row: row["_overall_mean"], reverse=True)
        for row in rows:
            del row["_overall_mean"]
        return rows

    outdir = Path(args.outdir)
    write_csv(
        outdir / "system_type_difficulty_non_starcoder.csv",
        system_rows,
        ["system_type", "n", "mean_total", "sd_total"],
    )
    write_csv(
        outdir / "rubric_dimension_summary_non_starcoder.csv",
        dimension_rows,
        ["dimension", "n", "mean_score", "sd_score"],
    )
    write_csv(
        outdir / "split_robustness_model_summary.csv",
        split_rows("model"),
        ["model", "calibration_n", "calibration_mean", "holdout_n", "holdout_mean", "delta_holdout_minus_calibration"],
    )
    write_csv(
        outdir / "split_robustness_family_summary.csv",
        split_rows("family"),
        ["family", "calibration_n", "calibration_mean", "holdout_n", "holdout_mean", "delta_holdout_minus_calibration"],
    )

    print(f"wrote={outdir}")


if __name__ == "__main__":
    main()
