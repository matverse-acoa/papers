import json
import subprocess
import sys
from pathlib import Path


def test_runtime_and_replay_end_to_end(tmp_path: Path):
    runtime_dir = Path(__file__).resolve().parents[1]
    ledger = runtime_dir / "ledger.jsonl"
    key = runtime_dir / "organism.key"

    for p in [ledger, key]:
        if p.exists():
            p.unlink()

    subprocess.check_call([sys.executable, "runtime.py", "--max-blocks", "2", "--tick", "0"], cwd=runtime_dir)
    subprocess.check_call([sys.executable, "replay.py"], cwd=runtime_dir)

    rows = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 3  # genesis + 2 blocks
    assert rows[-1]["index"] == 2
    assert "ohash" in rows[-1]
    assert "evidence_note" in rows[-1]
