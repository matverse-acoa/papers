from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .fail_closed import civilizational_fail
from .ledger import sha3


def current_hash(ledger_file: str | Path) -> str:
    data = Path(ledger_file).read_bytes()
    return sha3(data)


def save_guard(ledger_file: str | Path, guard_file: str | Path) -> dict[str, str]:
    snapshot = {
        "hash": current_hash(ledger_file),
        "time": datetime.now(timezone.utc).isoformat(),
    }
    Path(guard_file).write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    return snapshot


def watchdog(ledger_file: str | Path, guard_file: str | Path) -> bool:
    guard = json.loads(Path(guard_file).read_text(encoding="utf-8"))
    observed = current_hash(ledger_file)
    if observed != guard["hash"]:
        civilizational_fail(
            f"REWRITE DETECTED ledger={ledger_file} expected={guard['hash']} observed={observed}"
        )
    return True
