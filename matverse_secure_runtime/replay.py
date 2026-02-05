from __future__ import annotations

from .crypto import verify
from .ledger import AppendOnlyLedger, canonical_dumps, compute_merkle_root, sha3


def replay_verify(ledger_file: str) -> None:
    ledger = AppendOnlyLedger(ledger_file)
    blocks = ledger.read_blocks()
    parent = "GENESIS"
    hashes: list[str] = []
    prev_ohash = ""

    for i, block in enumerate(blocks):
        payload = block["payload"]
        raw_payload = canonical_dumps(payload).encode("utf-8")

        if sha3(raw_payload) != block["hash"]:
            raise RuntimeError(f"TAMPERING DETECTED at index={i}: invalid hash")

        if payload["parent_hash"] != parent:
            raise RuntimeError(f"CAUSALITY BROKEN at index={i}: invalid parent hash")

        if not verify(raw_payload, block["signature"]):
            raise RuntimeError(f"INVALID SIGNATURE at index={i}")

        if payload["ohash_payload"]["prev_ohash"] != prev_ohash:
            raise RuntimeError(f"OHASH CHAIN BROKEN at index={i}")

        hashes.append(block["hash"])
        expected_root = compute_merkle_root(hashes)
        if block["merkle_root"] != expected_root:
            raise RuntimeError(f"MERKLE ROOT MISMATCH at index={i}")

        parent = block["hash"]
        prev_ohash = block["ohash"]

    print("REPLAY OK — causal chain, signature, OHASH chain and Merkle root intact.")
