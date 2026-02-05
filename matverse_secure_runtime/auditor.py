from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .crypto import sign
from .ledger import AppendOnlyLedger, compute_merkle_root, sha3
from .replay import replay_verify


def build_audit_report(
    ledger_file: str | Path,
    bitcoin_anchor_file: str | Path | None = None,
    notarization_file: str | Path | None = None,
) -> dict:
    ledger = AppendOnlyLedger(ledger_file)
    blocks = ledger.read_blocks()
    hashes = [block["hash"] for block in blocks]

    replay_verify(str(ledger_file))

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ledger_file": str(ledger_file),
        "ledger_sha3_256": sha3(Path(ledger_file).read_bytes()),
        "ledger_blocks": len(blocks),
        "first_hash": hashes[0] if hashes else None,
        "last_hash": hashes[-1] if hashes else None,
        "merkle_root": compute_merkle_root(hashes),
    }

    if bitcoin_anchor_file and Path(bitcoin_anchor_file).exists():
        report["bitcoin_anchor"] = json.loads(Path(bitcoin_anchor_file).read_text(encoding="utf-8"))

    if notarization_file and Path(notarization_file).exists():
        report["notarization"] = json.loads(Path(notarization_file).read_text(encoding="utf-8"))

    report_bytes = json.dumps(report, sort_keys=True, separators=(",", ":")).encode("utf-8")
    report["audit_signature"] = sign(report_bytes)
    return report


def write_audit_report(report: dict, output_file: str | Path) -> None:
    Path(output_file).write_text(json.dumps(report, indent=2), encoding="utf-8")
