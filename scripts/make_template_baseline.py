import argparse
import json
from pathlib import Path


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--mode", choices=["generic", "grounded"], default="generic")
    args = parser.parse_args()

    rows = []
    for task in read_jsonl(Path(args.tasks)):
        if args.mode == "grounded":
            artifact = {
                "capability_requirement": f"The {task['system_type']} shall support the stated stakeholder intent: {task['stakeholder_intent']}",
                "source_constraints": task.get("available_evidence", []),
                "failure_behavior": [
                    "Use only the listed evidence sources.",
                    "Refuse or escalate when the request is unsupported by available evidence.",
                    "Do not perform disallowed behavior.",
                ],
                "validation_scenarios": [
                    f"Validate a normal request for {task['system_type']}.",
                    "Validate unsupported evidence and disallowed behavior cases.",
                ],
                "traceability_links": [
                    task["task_id"],
                    "stakeholder intent",
                    "available evidence list",
                    "disallowed behavior list",
                ],
                "runtime_signals": [
                    "unsupported request count",
                    "refusal or escalation count",
                    "missing evidence signal",
                ],
            }
        else:
            artifact = {
                "capability_requirement": "The assistant shall support the requested capability.",
                "source_constraints": ["approved sources"],
                "failure_behavior": ["refuse unsupported requests"],
                "validation_scenarios": ["normal request", "unsupported request"],
                "traceability_links": ["requirement", "test", "log"],
                "runtime_signals": ["request count", "error count"],
            }
        rows.append(
            {
                "task_id": task["task_id"],
                "model": f"template_baseline_{args.mode}",
                "elapsed_sec": 0.0,
                "response": json.dumps(artifact, ensure_ascii=False),
                "error": None,
            }
        )

    write_jsonl(Path(args.out), rows)
    print(f"wrote={args.out}")
    print(f"rows={len(rows)}")


if __name__ == "__main__":
    main()
