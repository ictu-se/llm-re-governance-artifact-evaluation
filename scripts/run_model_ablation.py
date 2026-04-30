import argparse
import json
import time
import urllib.request
from pathlib import Path

from run_ollama_re_experiment import SYSTEM_PROMPT, build_prompt


NO_SCHEMA_SYSTEM_PROMPT = """You are a requirements engineer for LLM-based software systems.
Write a concise requirements engineering artifact grounded in the supplied context.
Do not invent system features outside the task."""


def call_ollama(model: str, prompt: str, system: str, timeout: int = 180) -> tuple[str, float]:
    payload = {
        "model": model,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "options": {"temperature": 0.1, "num_ctx": 4096},
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    start = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return body.get("response", ""), time.time() - start


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--mode", choices=["schema", "no_schema"], required=True)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    tasks = read_jsonl(Path(args.tasks))
    if args.limit is not None:
        tasks = tasks[: args.limit]
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    done = {row["task_id"] for row in read_jsonl(out_path)} if out_path.exists() else set()
    system = SYSTEM_PROMPT if args.mode == "schema" else NO_SCHEMA_SYSTEM_PROMPT

    with out_path.open("a", encoding="utf-8") as f:
        for task in tasks:
            if task["task_id"] in done:
                continue
            prompt = build_prompt(task)
            try:
                response, elapsed = call_ollama(args.model, prompt, system)
                row = {
                    "task_id": task["task_id"],
                    "model": f"{args.model}__{args.mode}",
                    "elapsed_sec": round(elapsed, 3),
                    "response": response,
                    "error": None,
                }
            except Exception as exc:
                row = {
                    "task_id": task["task_id"],
                    "model": f"{args.model}__{args.mode}",
                    "elapsed_sec": None,
                    "response": "",
                    "error": str(exc),
                }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            f.flush()


if __name__ == "__main__":
    main()
