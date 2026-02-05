import json

from ledger import LEDGER_FILE, compute_merkle, payload_bytes, read_blocks, sha3
from projection_gate import projection_gate


def replay():
    parent = None
    hashes = []

    with LEDGER_FILE.open("rb") as file:
        for line in file:
            block = json.loads(line)

            raw = payload_bytes(block)
            computed = sha3(raw)

            if block["hash"] != computed:
                raise RuntimeError("LEDGER CORRUPTION DETECTED")

            if parent and block["parent_hash"] != parent:
                raise RuntimeError("CAUSALITY BROKEN")

            if block["index"] > 0:
                projection_gate(block["state"])

            hashes.append(block["hash"])
            if block.get("merkle_root") and block["merkle_root"] != compute_merkle(hashes):
                raise RuntimeError("MERKLE ROOT MISMATCH")

            parent = block["hash"]

    print("REPLAY SUCCESS — causal chain intact.")


if __name__ == "__main__":
    replay()
