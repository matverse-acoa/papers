import argparse
import hashlib
import hmac
import json
import os
import random
import socket
import time
from datetime import datetime, timezone
from pathlib import Path

from ledger import (
    append_block,
    compute_merkle,
    ensure_ledger,
    last_block,
    payload_bytes,
    read_hashes,
    sha3,
)
from projection_gate import projection_gate

BASE_DIR = Path(__file__).resolve().parent
KEY_FILE = BASE_DIR / "organism.key"


def sign(data: bytes) -> str:
    if KEY_FILE.exists():
        key = KEY_FILE.read_bytes()
    else:
        key = os.urandom(32)
        KEY_FILE.write_bytes(key)
    return hmac.new(key, data, digestmod=hashlib.sha3_256).hexdigest()


def generate_state() -> dict:
    psi = random.uniform(0.86, 0.98)
    cvar = random.uniform(0.01, 0.04)
    return {
        "psi": psi,
        "cvar": cvar,
    }


def evidence_note(block_hash: str) -> dict:
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "hostname": socket.gethostname(),
        "pid": os.getpid(),
        "runtime": "MatVerse Constitutional Runtime",
        "evidence_hash": block_hash,
    }


def generate_ohash(orcid: str, state: dict, prev_ohash: str) -> str:
    payload = {
        "orcid": orcid,
        "state_hash": sha3(json.dumps(state, sort_keys=True, separators=(",", ":")).encode("utf-8")),
        "prev_ohash": prev_ohash,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return sha3(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def create_block(state: dict, orcid: str):
    prev = last_block()
    prev_ohash = prev.get("ohash", "")
    ohash = generate_ohash(orcid=orcid, state=state, prev_ohash=prev_ohash)

    payload = {
        "index": prev["index"] + 1,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "parent_hash": prev["hash"],
        "state": state,
        "ohash": ohash,
    }

    raw = payload_bytes(payload)
    payload["hash"] = sha3(raw)
    payload["signature"] = sign(raw)
    payload["evidence_note"] = evidence_note(payload["hash"])
    payload["merkle_root"] = compute_merkle(read_hashes() + [payload["hash"]])

    return payload


def metabolism_loop(orcid: str, tick: float, max_blocks: int | None = None):
    ensure_ledger()
    print("CONSTITUTIONAL RUNTIME STARTED")

    produced = 0
    while True:
        state = generate_state()
        projection_gate(state)

        block = create_block(state, orcid=orcid)
        append_block(block)

        print(
            f"[LEDGER] block={block['index']} "
            f"hash={block['hash'][:8]} "
            f"ohash={block['ohash'][:8]} "
            f"psi={state['psi']:.3f} "
            f"evidence={block['evidence_note']['evidence_hash'][:8]}"
        )

        produced += 1
        if max_blocks is not None and produced >= max_blocks:
            break

        time.sleep(tick)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--orcid", default="0009-0008-2973-4047")
    parser.add_argument("--tick", type=float, default=1.0)
    parser.add_argument("--max-blocks", type=int, default=None)
    args = parser.parse_args()
    metabolism_loop(orcid=args.orcid, tick=args.tick, max_blocks=args.max_blocks)


if __name__ == "__main__":
    main()
