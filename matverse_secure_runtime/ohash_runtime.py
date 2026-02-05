from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any


def generate_ohash(orcid: str, artifact_hash: str, metadata: dict[str, Any], prev_ohash: str = "") -> tuple[str, dict[str, Any]]:
    payload = {
        "orcid": orcid,
        "artifact_hash": artifact_hash,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metadata": metadata,
        "prev_ohash": prev_ohash,
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ohash = hashlib.sha3_256(raw).hexdigest()
    return ohash, payload
