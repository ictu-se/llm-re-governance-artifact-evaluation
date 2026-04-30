import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def base_model(model: str) -> str:
    return model.replace("__schema", "").replace("__no_schema", "")


def mode(model: str) -> str:
    return "no_schema" if model.endswith("__no_schema") else "schema"


def mean(vals: list[float]) -> float:
    return sum(vals) / len(vals) if vals else float("nan")


def paired_t(schema: dict[str, float], no_schema: dict[str, float]) -> tuple[int, float, float]:
    task_ids = sorted(set(schema) & set(no_schema))
    diffs = [schema[t] - no_schema[t] for t in task_ids]
    n = len(diffs)
    if n < 2:
        return n, float("nan"), float("nan")
    md = mean(diffs)
    sd = math.sqrt(sum((d - md) ** 2 for d in diffs) / (n - 1))
    t = md / (sd / math.sqrt(n)) if sd else 0.0
    # Normal approximation is sufficient for pipeline reporting; manuscript can recompute exact p in R/Python.
    p = math.erfc(abs(t) / math.sqrt(2))
    return n, md, p


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rubric-glob", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    rows = []
    for path in sorted(Path(".").glob(args.rubric_glob)):
        rows.extend(read_csv(path))

    grouped = defaultdict(lambda: defaultdict(list))
    by_task = defaultdict(lambda: defaultdict(dict))
    for row in rows:
        bm = base_model(row["model"])
        m = mode(row["model"])
        score = float(row["rubric_total"])
        grouped[bm][m].append(score)
        by_task[bm][m][row["task_id"]] = score

    out_rows = []
    for bm in sorted(grouped):
        schema_scores = grouped[bm].get("schema", [])
        no_schema_scores = grouped[bm].get("no_schema", [])
        n, diff, p = paired_t(by_task[bm].get("schema", {}), by_task[bm].get("no_schema", {}))
        out_rows.append(
            {
                "model": bm,
                "n_schema": len(schema_scores),
                "n_no_schema": len(no_schema_scores),
                "mean_schema": round(mean(schema_scores), 4),
                "mean_no_schema": round(mean(no_schema_scores), 4),
                "paired_n": n,
                "mean_schema_minus_no_schema": round(diff, 4) if not math.isnan(diff) else "",
                "paired_p_normal_approx": round(p, 6) if not math.isnan(p) else "",
            }
        )

    write_csv(Path(args.out), out_rows)


if __name__ == "__main__":
    main()
