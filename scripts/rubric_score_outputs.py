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

GOVERNANCE_TERMS = [
    "refuse",
    "escalate",
    "privacy",
    "uncertain",
    "unsupported",
    "evidence",
    "monitor",
    "audit",
    "review",
    "log",
    "source",
]

TRACE_TERMS = [
    "trace",
    "link",
    "source",
    "evidence",
    "model",
    "version",
    "validation",
    "scenario",
    "runtime",
    "signal",
    "log",
]


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


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
    if value is None:
        return ""
    return str(value)


def contains_any(text: str, terms: list[str]) -> int:
    lower = text.lower()
    return sum(1 for term in terms if term.lower() in lower)


def recall(text: str, terms: list[str]) -> float:
    if not terms:
        return 0.0
    return contains_any(text, terms) / len(terms)


def score_slot_coverage(parsed) -> tuple[int, int]:
    if not isinstance(parsed, dict):
        return 0, 0
    nonempty = sum(1 for slot in SLOTS if flatten(parsed.get(slot, "")).strip())
    if nonempty == len(SLOTS):
        return 2, nonempty
    if nonempty >= 4:
        return 1, nonempty
    return 0, nonempty


def score_correctness(task: dict, parsed, text: str, strict: bool) -> int:
    if not isinstance(parsed, dict):
        return 0
    intent_terms = [w for w in re.findall(r"[A-Za-z][A-Za-z0-9.-]+", task["stakeholder_intent"].lower()) if len(w) > 4]
    context_hit = task["system_type"].split()[0].lower() in text.lower()
    gold = recall(text, task.get("gold_keywords", []))
    intent = recall(text, intent_terms[:8])
    threshold = 0.45 if strict else 0.35
    if context_hit and (gold >= threshold or intent >= threshold):
        return 2
    if context_hit or gold >= 0.2 or intent >= 0.2:
        return 1
    return 0


def score_traceability(parsed, text: str, strict: bool) -> int:
    if not isinstance(parsed, dict):
        return 0
    trace_text = flatten(parsed.get("traceability_links", "")) + " " + flatten(parsed.get("runtime_signals", ""))
    hits = contains_any(trace_text or text, TRACE_TERMS)
    if hits >= (5 if strict else 4):
        return 2
    if hits >= 2:
        return 1
    return 0


def score_governance(task: dict, parsed, text: str, strict: bool) -> int:
    if not isinstance(parsed, dict):
        return 0
    gov_text = " ".join(
        [
            flatten(parsed.get("source_constraints", "")),
            flatten(parsed.get("failure_behavior", "")),
            flatten(parsed.get("validation_scenarios", "")),
            flatten(parsed.get("runtime_signals", "")),
        ]
    )
    gov_hits = contains_any(gov_text, GOVERNANCE_TERMS)
    risk = recall(text, task.get("risk_keywords", []))
    if gov_hits >= (5 if strict else 4) and risk >= (0.5 if strict else 0.4):
        return 2
    if gov_hits >= 2 or risk >= 0.25:
        return 1
    return 0


def score_hallucination(task: dict, parsed, text: str, strict: bool) -> int:
    if not isinstance(parsed, dict):
        return 0
    lower = text.lower()
    disallowed = [item.lower() for item in task.get("disallowed_behavior", [])]
    allowed = [item.lower() for item in task.get("available_evidence", [])]
    disallowed_mentions = sum(1 for item in disallowed if item and item in lower)
    allowed_mentions = sum(1 for item in allowed if item and item in lower)
    boundary_terms = contains_any(text, ["only", "allowed", "approved", "evidence", "source", "must not", "refuse"])
    if disallowed_mentions and boundary_terms < 2:
        return 0
    if allowed_mentions >= (2 if strict else 1) and boundary_terms >= (3 if strict else 2):
        return 2
    if allowed_mentions or boundary_terms >= 2:
        return 1
    return 0


def score(task: dict, pred: dict, strict: bool) -> dict:
    parsed = extract_json(pred.get("response", ""))
    parsed_text = flatten(parsed) if isinstance(parsed, dict) else pred.get("response", "")
    completeness, nonempty = score_slot_coverage(parsed)
    values = {
        "correctness": score_correctness(task, parsed, parsed_text, strict),
        "completeness": completeness,
        "traceability_usefulness": score_traceability(parsed, parsed_text, strict),
        "governance_adequacy": score_governance(task, parsed, parsed_text, strict),
        "hallucination_risk": score_hallucination(task, parsed, parsed_text, strict),
    }
    values["rubric_total"] = sum(values.values())
    values["parse_ok"] = int(isinstance(parsed, dict))
    values["slot_nonempty"] = nonempty
    return values


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", required=True)
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    tasks = {row["task_id"]: row for row in read_jsonl(Path(args.tasks))}
    rows = []
    for pred in read_jsonl(Path(args.predictions)):
        task = tasks[pred["task_id"]]
        rater_a = score(task, pred, strict=True)
        rater_b = score(task, pred, strict=False)
        row = {
            "task_id": pred["task_id"],
            "system_type": task["system_type"],
            "model": pred["model"],
            "error": pred.get("error"),
        }
        for key, value in rater_a.items():
            row[f"rater_a_{key}"] = value
        for key, value in rater_b.items():
            row[f"rater_b_{key}"] = value
        for dim in [
            "correctness",
            "completeness",
            "traceability_usefulness",
            "governance_adequacy",
            "hallucination_risk",
            "rubric_total",
        ]:
            row[dim] = round((rater_a[dim] + rater_b[dim]) / 2, 4)
        rows.append(row)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
