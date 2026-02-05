import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
LEDGER_FILE = BASE_DIR / "ledger.jsonl"
GENESIS_FILE = BASE_DIR / "genesis.json"


def sha3(data: bytes) -> str:
    return hashlib.sha3_256(data).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _payload_for_hash(block: dict[str, Any]) -> dict[str, Any]:
    return {
        "index": block["index"],
        "timestamp": block["timestamp"],
        "parent_hash": block["parent_hash"],
        "state": block["state"],
        "ohash": block.get("ohash", ""),
    }


def ensure_ledger() -> None:
    if LEDGER_FILE.exists():
        return

    genesis_hash = sha3(GENESIS_FILE.read_bytes())
    timestamp = datetime.now(timezone.utc).isoformat()
    genesis_block = {
        "index": 0,
        "timestamp": timestamp,
        "parent_hash": None,
        "state": "GENESIS",
        "ohash": genesis_hash,
    }
    raw = canonical_json(_payload_for_hash(genesis_block)).encode("utf-8")
    genesis_block["hash"] = sha3(raw)
    genesis_block["signature"] = "GENESIS"
    genesis_block["merkle_root"] = genesis_block["hash"]
    genesis_block["evidence_note"] = {
        "timestamp_utc": timestamp,
        "runtime": "MatVerse Constitutional Runtime",
        "evidence_hash": genesis_block["hash"],
    }
    append_block(genesis_block)


def last_block() -> dict[str, Any]:
    with LEDGER_FILE.open("rb") as file:
        lines = file.readlines()
    return json.loads(lines[-1])


def append_block(block: dict[str, Any]) -> None:
    line = canonical_json(block)
    fd = os.open(LEDGER_FILE, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o644)
    with os.fdopen(fd, "a", encoding="utf-8") as file:
        file.write(line + "\n")
        file.flush()
        os.fsync(file.fileno())


def read_blocks() -> list[dict[str, Any]]:
    if not LEDGER_FILE.exists():
        return []
    with LEDGER_FILE.open("r", encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def read_hashes() -> list[str]:
    return [block["hash"] for block in read_blocks()]


def compute_merkle(hashes: list[str]) -> str:
    if not hashes:
        return ""
    level = list(hashes)
    while len(level) > 1:
        nxt = []
        for i in range(0, len(level), 2):
            left = level[i]
            right = level[i + 1] if i + 1 < len(level) else left
            nxt.append(sha3((left + right).encode("utf-8")))
        level = nxt
    return level[0]


def payload_bytes(block: dict[str, Any]) -> bytes:
    return canonical_json(_payload_for_hash(block)).encode("utf-8")
