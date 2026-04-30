import argparse
import json
from pathlib import Path


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--retry", nargs="*", default=[])
    args = parser.parse_args()

    by_task: dict[str, dict] = {}
    replaced = 0
    for row in read_jsonl(Path(args.base)):
        by_task[row["task_id"]] = row

    for retry_path in args.retry:
        for row in read_jsonl(Path(retry_path)):
            task_id = row["task_id"]
            old = by_task.get(task_id)
            old_bad = old is None or old.get("error") is not None or not old.get("response")
            new_good = row.get("error") is None and bool(row.get("response"))
            if old_bad and new_good:
                replaced += 1
                by_task[task_id] = row
            elif old is None:
                by_task[task_id] = row

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for task_id in sorted(by_task):
            f.write(json.dumps(by_task[task_id], ensure_ascii=False) + "\n")

    total = len(by_task)
    errors = sum(1 for row in by_task.values() if row.get("error") is not None)
    print(json.dumps({"out": str(out_path), "rows": total, "errors": errors, "replaced": replaced}, indent=2))


if __name__ == "__main__":
    main()
