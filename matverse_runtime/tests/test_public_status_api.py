import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from public_status_api import ledger_head, latest_block, psi, read_ledger, replay_status


def _write_ledger(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def test_status_helpers_with_missing_ledger(tmp_path: Path):
    ledger = tmp_path / "ledger.jsonl"

    assert read_ledger(ledger) == []
    assert latest_block(ledger) == {}
    assert ledger_head(ledger)["height"] == -1
    assert psi(ledger)["psi"] is None
    assert replay_status(ledger)["replay_ready"] is False


def test_status_helpers_with_valid_ledger(tmp_path: Path):
    ledger = tmp_path / "ledger.jsonl"
    rows = [
        {"index": 0, "timestamp": "2026-01-01T00:00:00+00:00", "hash": "genesis"},
        {
            "index": 1,
            "timestamp": "2026-01-01T00:01:00+00:00",
            "hash": "abc123",
            "state": {"psi": 0.93, "cvar": 0.02},
        },
    ]
    _write_ledger(ledger, rows)

    assert latest_block(ledger)["index"] == 1
    assert ledger_head(ledger)["hash"] == "abc123"
    assert psi(ledger)["psi"] == 0.93
    replay = replay_status(ledger)
    assert replay["replay_ready"] is True
    assert replay["latest_height"] == 1
