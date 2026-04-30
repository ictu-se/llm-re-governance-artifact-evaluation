import argparse
import json
from pathlib import Path

from run_ollama_re_experiment import build_prompt, call_ollama


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
    parser.add_argument("--tasks", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    task_path = Path(args.tasks)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    tasks = read_jsonl(task_path)
    done = {row["task_id"] for row in read_jsonl(out_path)}
    remaining = [task for task in tasks if task["task_id"] not in done]
    if args.limit is not None:
        remaining = remaining[: args.limit]

    with out_path.open("a", encoding="utf-8") as f:
        for task in remaining:
            prompt = build_prompt(task)
            try:
                response, elapsed = call_ollama(args.model, prompt)
                row = {
                    "task_id": task["task_id"],
                    "model": args.model,
                    "elapsed_sec": round(elapsed, 3),
                    "response": response,
                    "error": None,
                }
            except Exception as exc:
                row = {
                    "task_id": task["task_id"],
                    "model": args.model,
                    "elapsed_sec": None,
                    "response": "",
                    "error": str(exc),
                }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            f.flush()


if __name__ == "__main__":
    main()
