"""
Merkle Ledger - Immutable Scientific Evidence Chain
Implements Merkle trees for cryptographic proof of scientific records
"""

import hashlib
import json
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from merkletools import MerkleTools


@dataclass
class LedgerEntry:
    """Entry in the scientific ledger"""
    entry_id: str
    entry_type: str  # paper, review, funding, decision, etc.
    timestamp: float
    author_orcid: str
    content_hash: str
    metadata: Dict[str, Any]
    previous_hash: str = ""
    signature: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

    def compute_hash(self) -> str:
        """Compute hash of this entry"""
        data = self.to_json().encode("utf-8")
        return hashlib.sha3_256(data).hexdigest()


class ScientificMerkleLedger:
    """
    Merkle-based ledger for scientific evidence
    Provides O(log n) verification and immutable proof
    """

    def __init__(self, hash_type: str = "sha3_256"):
        self.ledger = []
        self.merkle_tools = MerkleTools(hash_type=hash_type)
        self.rebuild_tree()

    def add_entry(self, entry: LedgerEntry) -> str:
        """
        Add entry to ledger and rebuild Merkle tree
        Returns: entry_id
        """
        # Set previous hash if exists
        if self.ledger:
            entry.previous_hash = self.ledger[-1].compute_hash()

        # Add to ledger
        self.ledger.append(entry)

        # Rebuild Merkle tree
        self.rebuild_tree()

        return entry.entry_id

    def rebuild_tree(self):
        """Rebuild Merkle tree from current ledger"""
        self.merkle_tools.reset_tree()

        for entry in self.ledger:
            entry_hash = entry.compute_hash()
            self.merkle_tools.add_leaf(entry_hash, do_hash=False)

        if self.ledger:
            self.merkle_tools.make_tree()

    def get_merkle_root(self) -> Optional[str]:
        """Get current Merkle root"""
        if self.ledger:
            return self.merkle_tools.get_merkle_root()
        return None

    def get_proof(self, entry_index: int) -> Optional[List[Dict[str, Any]]]:
        """
        Get Merkle proof for entry at index
        Returns: Proof path for verification
        """
        if 0 <= entry_index < len(self.ledger):
            return self.merkle_tools.get_proof(entry_index)
        return None

    def verify_entry(self, entry_index: int) -> bool:
        """
        Verify entry integrity using Merkle proof
        """
        if entry_index < 0 or entry_index >= len(self.ledger):
            return False

        entry = self.ledger[entry_index]
        entry_hash = entry.compute_hash()
        proof = self.get_proof(entry_index)

        if not proof:
            return False

        return self.merkle_tools.validate_proof(
            proof, entry_hash, self.get_merkle_root()
        )

    def verify_chain(self) -> bool:
        """Verify entire chain integrity"""
        # Check Merkle root consistency
        if not self.ledger:
            return True

        # Verify each entry
        for i, entry in enumerate(self.ledger):
            if not self.verify_entry(i):
                return False

            # Verify previous hash chain
            if i > 0:
                prev_hash = self.ledger[i - 1].compute_hash()
                if entry.previous_hash != prev_hash:
                    return False

        return True

    def find_entries(self, criteria: Dict[str, Any]) -> List[LedgerEntry]:
        """Find entries matching criteria"""
        results = []

        for entry in self.ledger:
            match = True

            for key, value in criteria.items():
                if key in entry.metadata:
                    if entry.metadata[key] != value:
                        match = False
                        break
                elif hasattr(entry, key):
                    if getattr(entry, key) != value:
                        match = False
                        break
                else:
                    match = False
                    break

            if match:
                results.append(entry)

        return results

    def create_evidence_receipt(self, entry_index: int) -> Dict[str, Any]:
        """
        Create evidence receipt for an entry
        Includes Merkle proof, chain position, and verification data
        """
        if entry_index < 0 or entry_index >= len(self.ledger):
            return {}

        entry = self.ledger[entry_index]
        proof = self.get_proof(entry_index)

        receipt = {
            "receipt_id": hashlib.sha3_256(
                f"{entry.entry_id}:{time.time()}".encode()
            ).hexdigest(),
            "entry": entry.to_dict(),
            "merkle_proof": proof,
            "merkle_root": self.get_merkle_root(),
            "chain_position": {
                "index": entry_index,
                "total_entries": len(self.ledger)
            },
            "timestamp": time.time(),
            "verification_data": {
                "entry_hash": entry.compute_hash(),
                "proof_valid": self.verify_entry(entry_index),
                "chain_valid": self.verify_chain()
            }
        }

        return receipt

    def export_ledger(self, format: str = "json") -> str:
        """Export entire ledger"""
        data = {
            "ledger": [entry.to_dict() for entry in self.ledger],
            "merkle_root": self.get_merkle_root(),
            "total_entries": len(self.ledger),
            "exported_at": time.time()
        }

        if format == "json":
            return json.dumps(data, indent=2)
        raise ValueError(f"Unsupported format: {format}")


class GlobalScientificLedger(ScientificMerkleLedger):
    """
    Global ledger for planetary scientific evidence
    Extends base ledger with cross-chain anchoring
    """

    def __init__(self, hash_type: str = "sha3_256"):
        super().__init__(hash_type)
        self.anchors = []  # Blockchain anchors

    def anchor_to_blockchain(self, blockchain_client, contract_address: str) -> Dict[str, Any]:
        """
        Anchor current Merkle root to blockchain
        Returns: Transaction receipt
        """
        merkle_root = self.get_merkle_root()
        if not merkle_root:
            return {"error": "Empty ledger"}

        # Convert to bytes32 for Ethereum
        root_bytes = bytes.fromhex(
            merkle_root[2:] if merkle_root.startswith("0x") else merkle_root
        )

        # Call smart contract (simplified)
        try:
            tx_hash = blockchain_client.submit_root(
                contract_address,
                root_bytes,
                len(self.ledger)
            )

            anchor = {
                "tx_hash": tx_hash,
                "merkle_root": merkle_root,
                "block_height": blockchain_client.get_block_number(),
                "timestamp": time.time(),
                "entry_count": len(self.ledger)
            }

            self.anchors.append(anchor)
            return anchor

        except Exception as e:
            return {"error": str(e)}

    def verify_with_blockchain(self, blockchain_client, tx_hash: str) -> bool:
        """
        Verify ledger consistency with blockchain anchor
        """
        # Get transaction from blockchain
        tx_data = blockchain_client.get_transaction(tx_hash)
        if not tx_data:
            return False

        # Compare with local Merkle root
        stored_root = tx_data.get("root")
        current_root = self.get_merkle_root()

        return stored_root == current_root

    def create_global_receipt(self, entry_index: int, include_anchor: bool = True) -> Dict[str, Any]:
        """
        Create global evidence receipt with blockchain proof
        """
        base_receipt = super().create_evidence_receipt(entry_index)

        if include_anchor and self.anchors:
            latest_anchor = self.anchors[-1]
            base_receipt["blockchain_anchor"] = latest_anchor

        base_receipt["global_verification"] = {
            "has_blockchain_anchor": len(self.anchors) > 0,
            "anchor_count": len(self.anchors),
            "cross_chain_verified": False  # Would check with oracles
        }

        return base_receipt


# Example usage
if __name__ == "__main__":
    # Create ledger
    ledger = ScientificMerkleLedger()

    # Add some entries
    entry1 = LedgerEntry(
        entry_id="paper_001",
        entry_type="paper_submission",
        timestamp=time.time(),
        author_orcid="0009-0008-2973-4047",
        content_hash="abc123def456",
        metadata={
            "title": "Foundations of Antifragile Systems",
            "version": "1.0",
            "field": "quantum semantics"
        }
    )

    entry2 = LedgerEntry(
        entry_id="review_001",
        entry_type="peer_review",
        timestamp=time.time() + 1,
        author_orcid="0000-0002-1825-0097",
        content_hash="def456ghi789",
        metadata={
            "paper_id": "paper_001",
            "score": 8.5,
            "recommendation": "accept"
        }
    )

    # Add to ledger
    ledger.add_entry(entry1)
    ledger.add_entry(entry2)

    # Get Merkle root
    root = ledger.get_merkle_root()
    print(f"Merkle Root: {root}")

    # Verify entries
    print(f"Entry 0 valid: {ledger.verify_entry(0)}")
    print(f"Entry 1 valid: {ledger.verify_entry(1)}")
    print(f"Chain valid: {ledger.verify_chain()}")

    # Create evidence receipt
    receipt = ledger.create_evidence_receipt(0)
    print(f"Evidence Receipt: {json.dumps(receipt, indent=2)}")
