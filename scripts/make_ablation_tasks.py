import argparse
import json
from collections import defaultdict
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--per-system", type=int, default=3)
    args = parser.parse_args()

    selected = []
    counts = defaultdict(int)
    for line in Path(args.tasks).read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        system_type = row["system_type"]
        if counts[system_type] < args.per_system:
            selected.append(line)
            counts[system_type] += 1

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(selected) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(out), "tasks": len(selected), "systems": len(counts)}, indent=2))


if __name__ == "__main__":
    main()
