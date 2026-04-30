import argparse
import json
import time
import urllib.request
from pathlib import Path


SYSTEM_PROMPT = """You are a requirements engineer for LLM-based software systems.
Return only valid JSON with these keys:
capability_requirement, source_constraints, failure_behavior,
validation_scenarios, traceability_links, runtime_signals.
Use concise engineering language. Ground the requirement in the supplied context.
Do not invent system features outside the task."""


def call_ollama(model: str, prompt: str, timeout: int = 180) -> tuple[str, float]:
    payload = {
        "model": model,
        "prompt": prompt,
        "system": SYSTEM_PROMPT,
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


def build_prompt(task: dict) -> str:
    return f"""Task ID: {task['task_id']}
System type: {task['system_type']}
Stakeholder intent: {task['stakeholder_intent']}
Context: {task['context']}
Available evidence: {', '.join(task['available_evidence'])}
Disallowed behavior: {', '.join(task['disallowed_behavior'])}

Create a requirements engineering artifact for this LLM-based system.
The JSON fields must contain:
- capability_requirement: one precise requirement sentence
- source_constraints: list of allowed evidence/source constraints
- failure_behavior: list of refusal, escalation, privacy, or uncertainty behaviors
- validation_scenarios: list of scenario names or short scenario descriptions
- traceability_links: list of artifacts that should be linked to the requirement
- runtime_signals: list of monitoring signals for production governance
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    tasks = [json.loads(line) for line in Path(args.tasks).read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as f:
        for task in tasks:
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
