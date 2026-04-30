import argparse
import csv
import json
from pathlib import Path


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("predictions", nargs="+")
    args = parser.parse_args()

    task_count = len(read_jsonl(Path(args.tasks)))
    rows = []
    for pred in args.predictions:
        path = Path(pred)
        records = read_jsonl(path)
        models = sorted({row.get("model", "") for row in records})
        errors = sum(1 for row in records if row.get("error") is not None)
        rows.append(
            {
                "file": str(path),
                "model": ";".join(models),
                "rows": len(records),
                "task_count": task_count,
                "complete_240": int(len(records) == task_count),
                "errors": errors,
                "included_in_final": int(len(records) == task_count),
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
