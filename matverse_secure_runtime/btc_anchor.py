from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from .ledger import sha3


def ledger_hash(ledger_file: str | Path) -> str:
    return sha3(Path(ledger_file).read_bytes())


def anchor_payload(ledger_file: str | Path) -> dict[str, str]:
    digest = ledger_hash(ledger_file)
    return {
        "algorithm": "sha3_256",
        "ledger_hash": digest,
        "op_return": digest[:64],
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }


def anchor_bitcoin(
    ledger_file: str | Path,
    output_file: str | Path,
    address: str,
    amount_btc: str = "0.0001",
    *,
    dry_run: bool = True,
) -> dict:
    """
    Create an anchoring record. In dry_run mode, no network call is executed.
    In live mode, requires `electrum` CLI available in PATH.
    """
    payload = anchor_payload(ledger_file)
    result: dict = {"status": "dry_run" if dry_run else "pending", **payload}

    if not dry_run:
        unsigned_tx = subprocess.check_output(
            [
                "electrum",
                "payto",
                address,
                amount_btc,
                "--op_return",
                payload["op_return"],
                "--unsigned",
            ],
            text=True,
        ).strip()
        txid = subprocess.check_output(["electrum", "broadcast", unsigned_tx], text=True).strip()
        result.update({"status": "anchored", "txid": txid, "address": address, "amount_btc": amount_btc})

    Path(output_file).write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result
