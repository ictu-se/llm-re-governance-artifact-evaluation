import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


SCENARIO_BY_INDEX = {
    "01": "factual_answering",
    "02": "unsupported_request",
    "03": "sensitive_information",
    "04": "policy_exception",
    "05": "prompt_injection",
    "06": "citation_grounding",
    "07": "tool_authority",
    "08": "auditability",
    "09": "stale_evidence",
    "10": "advice_boundary",
    "11": "severity_classification",
    "12": "regression_testing",
}


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


def scenario(task_id: str) -> str:
    suffix = task_id.split("-")[-1]
    return SCENARIO_BY_INDEX.get(suffix, "unknown")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", required=True)
    parser.add_argument("--rubric-glob", default="results/final/*_rubric.csv")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    task_ids = {row["task_id"] for row in read_jsonl(Path(args.tasks))}
    groups = defaultdict(list)
    by_model = defaultdict(list)
    for path in sorted(Path(".").glob(args.rubric_glob)):
        for row in read_csv(path):
            if row["task_id"] not in task_ids or row["model"].startswith("starcoder2"):
                continue
            sc = scenario(row["task_id"])
            score = float(row["rubric_total"])
            groups[sc].append(score)
            by_model[(row["model"], sc)].append(score)

    rows = [
        {
            "scenario": sc,
            "n": len(vals),
            "mean_rubric_total": round(mean(vals), 4),
        }
        for sc, vals in sorted(groups.items(), key=lambda item: mean(item[1]))
    ]

    write_csv(Path(args.out), rows)
    print(f"wrote={args.out}")


if __name__ == "__main__":
    main()
