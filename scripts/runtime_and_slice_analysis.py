import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


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
    return sum(values) / len(values) if values else 0.0


def bucket_count(value: int) -> str:
    if value <= 3:
        return "low"
    if value <= 5:
        return "medium"
    return "high"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", required=True)
    parser.add_argument("--prediction-glob", default="results/predictions/*_v240*.jsonl")
    parser.add_argument("--manifest")
    parser.add_argument("--rubric-glob", default="results/final/*_rubric.csv")
    parser.add_argument("--outdir", required=True)
    args = parser.parse_args()

    tasks = {row["task_id"]: row for row in read_jsonl(Path(args.tasks))}
    outdir = Path(args.outdir)

    runtime_rows = []
    if args.manifest:
        prediction_paths = [Path(row["file"]) for row in read_csv(Path(args.manifest)) if row.get("included_in_final") == "1"]
    else:
        prediction_paths = sorted(Path(".").glob(args.prediction_glob))
    for path in prediction_paths:
        rows = read_jsonl(path)
        if not rows:
            continue
        model = rows[0].get("model", path.stem)
        elapsed = [float(row.get("elapsed_sec") or 0.0) for row in rows if row.get("elapsed_sec") not in (None, "")]
        errors = sum(1 for row in rows if row.get("error"))
        runtime_rows.append(
            {
                "model": model,
                "file": str(path),
                "n_rows": len(rows),
                "task_count": len({row["task_id"] for row in rows}),
                "total_elapsed_sec": round(sum(elapsed), 3),
                "mean_elapsed_sec": round(mean(elapsed), 3),
                "max_elapsed_sec": round(max(elapsed) if elapsed else 0.0, 3),
                "errors": errors,
                "throughput_tasks_per_min": round((len(rows) / sum(elapsed) * 60) if sum(elapsed) else 0.0, 4),
            }
        )

    rubric_rows = []
    for path in sorted(Path(".").glob(args.rubric_glob)):
        for row in read_csv(path):
            task = tasks.get(row["task_id"])
            if task is None:
                continue
            row = dict(row)
            row["available_evidence_count"] = len(task.get("available_evidence", []))
            row["disallowed_behavior_count"] = len(task.get("disallowed_behavior", []))
            row["gold_keyword_count"] = len(task.get("gold_keywords", []))
            row["risk_keyword_count"] = len(task.get("risk_keywords", []))
            row["trace_keyword_count"] = len(task.get("trace_keywords", []))
            rubric_rows.append(row)

    slice_groups = defaultdict(list)
    for row in rubric_rows:
        if row["model"].startswith("starcoder2"):
            continue
        score = float(row["rubric_total"])
        slice_groups[("available_evidence", bucket_count(int(row["available_evidence_count"])))].append(score)
        slice_groups[("disallowed_behavior", bucket_count(int(row["disallowed_behavior_count"])))].append(score)
        slice_groups[("gold_keyword", bucket_count(int(row["gold_keyword_count"])))].append(score)
        slice_groups[("trace_keyword", bucket_count(int(row["trace_keyword_count"])))].append(score)

    groups_by_slice = defaultdict(list)
    for (slice_name, group), values in slice_groups.items():
        groups_by_slice[slice_name].append((group, values))

    slice_rows = []
    for slice_name, grouped_values in sorted(groups_by_slice.items()):
        # Do not report non-informative slices. In the current benchmark, evidence
        # list sizes are intentionally controlled and therefore constant.
        if len(grouped_values) < 2:
            continue
        for group, values in sorted(grouped_values):
            slice_rows.append(
                {
                    "slice": slice_name,
                    "group": group,
                    "n": len(values),
                    "mean_rubric_total": round(mean(values), 4),
                }
            )

    write_csv(outdir / "runtime_summary.csv", runtime_rows)
    write_csv(outdir / "evidence_complexity_slices_non_starcoder.csv", slice_rows)
    print(f"wrote={outdir}")


if __name__ == "__main__":
    main()
