from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .crypto import sign
from .ledger import sha3


def notarize_ledger(
    ledger_file: str | Path,
    output_file: str | Path,
    organism: str = "MatVerse",
    jurisdiction: str = "BR",
    orcid: str = "0009-0008-2973-4047",
) -> dict:
    """
    Produce a signed notarization artifact (JSON) with legal/forensic metadata.
    """
    ledger_bytes = Path(ledger_file).read_bytes()
    ledger_digest = sha3(ledger_bytes)

    note = {
        "ledger_hash": ledger_digest,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "organism": organism,
        "jurisdiction": jurisdiction,
        "orcid": orcid,
        "signature": sign(ledger_digest.encode("utf-8")),
        "signature_algorithm": "HMAC-SHA3-256",
    }
    Path(output_file).write_text(json.dumps(note, indent=2), encoding="utf-8")
    return note
