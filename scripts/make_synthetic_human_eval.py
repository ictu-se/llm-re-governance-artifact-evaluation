import argparse
import csv
import hashlib
import random
from pathlib import Path


DIMENSIONS = [
    "correctness_0_2",
    "completeness_0_2",
    "traceability_usefulness_0_2",
    "governance_adequacy_0_2",
    "hallucination_risk_0_2",
]

RUBRIC_MAP = {
    "correctness_0_2": "correctness",
    "completeness_0_2": "completeness",
    "traceability_usefulness_0_2": "traceability_usefulness",
    "governance_adequacy_0_2": "governance_adequacy",
    "hallucination_risk_0_2": "hallucination_risk",
}


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def stable_rng(*parts: str) -> random.Random:
    raw = "|".join(parts).encode("utf-8")
    seed = int(hashlib.sha256(raw).hexdigest()[:16], 16)
    return random.Random(seed)


def clamp_score(value: int) -> int:
    return max(0, min(2, value))


def perturb(base: float, reviewer_idx: int, task_id: str, model: str, dim: str) -> int:
    rng = stable_rng(str(reviewer_idx), task_id, model, dim)
    rounded = int(round(base))
    # Conservative synthetic variation: most reviewers agree with the proxy score,
    # some differ by one point, and very few differ by two points.
    roll = rng.random()
    if roll < 0.76:
        delta = 0
    elif roll < 0.91:
        delta = -1
    elif roll < 0.985:
        delta = 1
    else:
        delta = -2 if rounded >= 1 else 2
    # Slightly stricter reviewers every fourth profile.
    if reviewer_idx % 4 == 0 and rng.random() < 0.18:
        delta -= 1
    return clamp_score(rounded + delta)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--template", required=True)
    parser.add_argument("--rubric-glob", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--reviewers", type=int, default=12)
    args = parser.parse_args()

    template_rows = read_csv(Path(args.template))
    rubric_by_key = {}
    for path in sorted(Path(".").glob(args.rubric_glob)):
        for row in read_csv(path):
            rubric_by_key[(row["model"], row["task_id"])] = row

    out_rows = []
    for row in template_rows:
        rubric = rubric_by_key.get((row["model"], row["task_id"]))
        if rubric is None:
            continue
        for idx in range(1, args.reviewers + 1):
            out = dict(row)
            out["reviewer_id"] = f"SYNTHETIC_EXPERT_{idx:02d}"
            out["synthetic_data"] = "1"
            out["replacement_required_before_submission"] = "1"
            for dim in DIMENSIONS:
                base = float(rubric[RUBRIC_MAP[dim]])
                out[dim] = perturb(base, idx, row["task_id"], row["model"], dim)
            out["notes"] = "SYNTHETIC PLACEHOLDER - replace with independent human reviewer rating before submission."
            out_rows.append(out)

    if not out_rows:
        raise SystemExit("No rows generated. Check template and rubric paths.")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(out_rows[0].keys())
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"wrote={out_path}")
    print(f"rows={len(out_rows)}")
    print("synthetic_data=1")


if __name__ == "__main__":
    main()
