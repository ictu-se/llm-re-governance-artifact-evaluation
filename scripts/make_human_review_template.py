import argparse
import csv
import json
from pathlib import Path


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--limit-per-model", type=int, default=48)
    parser.add_argument("predictions", nargs="+")
    args = parser.parse_args()

    tasks = {row["task_id"]: row for row in read_jsonl(Path(args.tasks))}
    rows = []
    for pred_path in args.predictions:
        records = read_jsonl(Path(pred_path))
        for pred in records[: args.limit_per_model]:
            task = tasks[pred["task_id"]]
            rows.append(
                {
                    "reviewer_id": "",
                    "model": pred["model"],
                    "task_id": pred["task_id"],
                    "system_type": task["system_type"],
                    "stakeholder_intent": task["stakeholder_intent"],
                    "context": task["context"],
                    "available_evidence": " | ".join(task["available_evidence"]),
                    "disallowed_behavior": " | ".join(task["disallowed_behavior"]),
                    "model_response": pred.get("response", ""),
                    "correctness_0_2": "",
                    "completeness_0_2": "",
                    "traceability_usefulness_0_2": "",
                    "governance_adequacy_0_2": "",
                    "hallucination_risk_0_2": "",
                    "notes": "",
                }
            )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
