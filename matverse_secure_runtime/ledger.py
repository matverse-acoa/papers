from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def sha3(payload: bytes) -> str:
    import hashlib

    return hashlib.sha3_256(payload).hexdigest()


def canonical_dumps(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


class AppendOnlyLedger:
    def __init__(self, ledger_path: str | Path):
        self.path = Path(ledger_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, block: dict[str, Any]) -> None:
        line = canonical_dumps(block)
        fd = os.open(self.path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o644)
        with os.fdopen(fd, "a", encoding="utf-8") as file:
            file.write(line + "\n")
            file.flush()
            os.fsync(file.fileno())

    def read_blocks(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as file:
            return [json.loads(line) for line in file if line.strip()]

    def last_hash(self) -> str:
        blocks = self.read_blocks()
        return blocks[-1]["hash"] if blocks else "GENESIS"


def compute_merkle_root(hashes: list[str]) -> str:
    if not hashes:
        return ""

    level = list(hashes)
    while len(level) > 1:
        next_level = []
        for i in range(0, len(level), 2):
            left = level[i]
            right = level[i + 1] if i + 1 < len(level) else left
            next_level.append(sha3((left + right).encode("utf-8")))
        level = next_level
    return level[0]
