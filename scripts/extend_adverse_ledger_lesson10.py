"""Extend the admitted adverse ledger through the Lesson 10 boundary.

Only the exact known 170-row ledger and the exact 198-row cumulative correction
backend are read.  The first 170 correction records are preserved semantically;
rows 171–198 are appended from their registered correction records, with a
canonical UTF-8 JSONL serialization for deterministic replay.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "00_control" / "ADVERSE_LEDGER.jsonl"
CUMULATIVE = ROOT / "backend" / "through_lesson10_corrections.jsonl"


def load(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    current = load(LEDGER)
    cumulative = load(CUMULATIVE)
    expected_prefix = [f"O006-PSU-ADV-{i:04d}" for i in range(1, 171)]
    expected_all = [f"O006-PSU-ADV-{i:04d}" for i in range(1, 199)]
    if [row.get("correction_id") for row in current] != expected_prefix:
        raise RuntimeError("existing adverse ledger is not the exact 170-row prefix")
    if [row.get("correction_id") for row in cumulative] != expected_all:
        raise RuntimeError("cumulative correction backend is not the exact 198-row sequence")
    extended = current + cumulative[170:]
    LEDGER.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in extended),
        encoding="utf-8",
        newline="\n",
    )
    print(f"wrote {LEDGER} with {len(extended)} rows")


if __name__ == "__main__":
    main()
