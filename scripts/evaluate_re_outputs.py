import argparse
import csv
import json
import re
from pathlib import Path


SLOTS = [
    "capability_requirement",
    "source_constraints",
    "failure_behavior",
    "validation_scenarios",
    "traceability_links",
    "runtime_signals",
]


def extract_json(text: str):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text, flags=re.I).strip()
        text = re.sub(r"```$", "", text).strip()
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r"\{.*\}", text, flags=re.S)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                return None
    return None


def flatten(value) -> str:
    if isinstance(value, list):
        return " ".join(flatten(v) for v in value)
    if isinstance(value, dict):
        return " ".join(flatten(v) for v in value.values())
    return str(value)


def recall(text: str, keywords: list[str]) -> float:
    lower = text.lower()
    if not keywords:
        return 0.0
    hits = sum(1 for kw in keywords if kw.lower() in lower)
    return hits / len(keywords)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", required=True)
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    tasks = {json.loads(line)["task_id"]: json.loads(line) for line in Path(args.tasks).read_text(encoding="utf-8-sig").splitlines() if line.strip()}
    rows = []
    for line in Path(args.predictions).read_text(encoding="utf-8-sig").splitlines():
        pred = json.loads(line)
        task = tasks[pred["task_id"]]
        parsed = extract_json(pred.get("response", ""))
        parse_ok = parsed is not None and isinstance(parsed, dict)
        slot_nonempty = 0
        text = pred.get("response", "")
        if parse_ok:
            for slot in SLOTS:
                if flatten(parsed.get(slot, "")).strip():
                    slot_nonempty += 1
            text = flatten(parsed)
        rows.append({
            "task_id": pred["task_id"],
            "model": pred["model"],
            "parse_ok": int(parse_ok),
            "slot_coverage": round(slot_nonempty / len(SLOTS), 4),
            "gold_keyword_recall": round(recall(text, task["gold_keywords"]), 4),
            "risk_control_recall": round(recall(text, task["risk_keywords"]), 4),
            "traceability_signal_recall": round(recall(text, task["trace_keywords"]), 4),
            "elapsed_sec": pred.get("elapsed_sec"),
            "error": pred.get("error"),
        })

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
