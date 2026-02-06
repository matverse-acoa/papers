from __future__ import annotations

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
LEDGER_PATH = BASE_DIR / "ledger.jsonl"


def validate_tx_id(tx_id: str, ledger_path: Path = LEDGER_PATH) -> bool:
    """Valida tx_id PBSE no ledger local (stub determinístico para integração runtime)."""
    if not tx_id or not tx_id.strip():
        return False

    normalized = tx_id.strip()
    if normalized.startswith("pbse_"):
        return True

    if not ledger_path.exists():
        return False

    for line in ledger_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("hash") == normalized or row.get("tx_id") == normalized:
            return True
    return False
