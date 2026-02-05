from __future__ import annotations

import argparse
import random
import time
from pathlib import Path

from .crypto import sign
from .evidence import evidence_note
from .ledger import AppendOnlyLedger, canonical_dumps, compute_merkle_root, sha3
from .ohash_runtime import generate_ohash
from .projection_gate import projection_gate


def generate_state() -> dict[str, float]:
    return {
        "psi": random.uniform(0.86, 0.98),
        "cvar": random.uniform(0.005, 0.04),
        "theta": random.uniform(0.72, 0.95),
    }


def create_block(
    ledger: AppendOnlyLedger,
    orcid: str,
    previous_ohash: str,
) -> tuple[dict, str]:
    state = generate_state()
    projection_gate(state)

    parent_hash = ledger.last_hash()
    artifact_hash = sha3(canonical_dumps(state).encode("utf-8"))
    ohash, ohash_payload = generate_ohash(
        orcid=orcid,
        artifact_hash=artifact_hash,
        metadata={"source": "constitutional_runtime", "psi": state["psi"]},
        prev_ohash=previous_ohash,
    )

    payload = {
        "parent_hash": parent_hash,
        "state": state,
        "ohash_payload": ohash_payload,
    }
    raw_payload = canonical_dumps(payload).encode("utf-8")
    block_hash = sha3(raw_payload)

    signature = sign(raw_payload)
    existing_hashes = [b["hash"] for b in ledger.read_blocks()]
    merkle_root = compute_merkle_root(existing_hashes + [block_hash])

    block = {
        "hash": block_hash,
        "payload": payload,
        "ohash": ohash,
        "evidence_note": evidence_note(state_hash=block_hash, ohash=ohash),
        "signature": signature,
        "merkle_root": merkle_root,
    }
    return block, ohash


def run_loop(ledger_file: str, orcid: str, tick_seconds: float, max_blocks: int | None = None) -> None:
    ledger = AppendOnlyLedger(ledger_file)
    previous_ohash = ""
    if ledger.read_blocks():
        previous_ohash = ledger.read_blocks()[-1].get("ohash", "")

    print("MATVERSE CONSTITUTIONAL RUNTIME STARTED")

    count = 0
    while True:
        block, previous_ohash = create_block(ledger, orcid, previous_ohash)
        ledger.append(block)

        print(
            f"[BLOCK] hash={block['hash'][:10]} "
            f"ohash={block['ohash'][:10]} "
            f"psi={block['payload']['state']['psi']:.3f} "
            f"mr={block['merkle_root'][:10]} "
            f"evidence_ts={block['evidence_note']['timestamp_utc']}"
        )

        count += 1
        if max_blocks is not None and count >= max_blocks:
            break

        time.sleep(tick_seconds)


def _default_ledger_path() -> str:
    return str(Path(__file__).resolve().parent / "ledger.jsonl")


def main() -> None:
    parser = argparse.ArgumentParser(description="MatVerse secure constitutional runtime")
    parser.add_argument("--ledger", default=_default_ledger_path(), help="Path for append-only ledger file")
    parser.add_argument("--orcid", default="0009-0008-2973-4047", help="ORCID identity for OHASH")
    parser.add_argument("--tick", type=float, default=1.0, help="Seconds between blocks")
    parser.add_argument("--max-blocks", type=int, default=None, help="Stop after N blocks")
    args = parser.parse_args()

    run_loop(
        ledger_file=args.ledger,
        orcid=args.orcid,
        tick_seconds=args.tick,
        max_blocks=args.max_blocks,
    )


if __name__ == "__main__":
    main()
