"""
OHASH Engine - Cryptographic Scientific Identity
Generates DNA-like hash for scientific authorship
"""

import hashlib
import json
import time
from typing import Tuple, Dict, Any
from dataclasses import dataclass, asdict
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization


@dataclass
class OHashPayload:
    """Payload for OHASH generation"""
    orcid: str
    artifact_hash: str
    timestamp: float
    metadata: Dict[str, Any]
    prev_ohash: str = ""  # For chaining
    author_signature: str = ""

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(asdict(self), sort_keys=True)

    def to_bytes(self) -> bytes:
        """Convert to bytes for hashing"""
        return self.to_json().encode("utf-8")


class OHashEngine:
    """
    OHASH: Cryptographic DNA for scientific authorship
    Generates: H(ORCID || artifact_hash || timestamp || metadata || prev_ohash)
    """

    def __init__(self, hash_algorithm: str = "sha3_256"):
        self.hash_algorithm = hash_algorithm

    def generate_ohash(self, payload: OHashPayload) -> Tuple[str, Dict[str, Any]]:
        """
        Generate OHASH from payload
        Returns: (ohash_string, full_payload_dict)
        """
        # Convert payload to bytes
        payload_bytes = payload.to_bytes()

        # Generate hash
        if self.hash_algorithm == "sha3_256":
            hash_obj = hashlib.sha3_256(payload_bytes)
        elif self.hash_algorithm == "blake2b":
            hash_obj = hashlib.blake2b(payload_bytes)
        else:
            hash_obj = hashlib.sha256(payload_bytes)

        ohash = hash_obj.hexdigest()

        # Prepare full payload
        full_payload = {
            "ohash": ohash,
            "payload": asdict(payload),
            "algorithm": self.hash_algorithm,
            "generated_at": time.time()
        }

        return ohash, full_payload

    def create_author_chain(self, orcid: str, artifacts: list) -> list:
        """
        Create a chain of OHASHes for multiple artifacts
        """
        chain = []
        prev_ohash = ""

        for i, artifact in enumerate(artifacts):
            artifact_hash = self._hash_artifact(artifact)

            payload = OHashPayload(
                orcid=orcid,
                artifact_hash=artifact_hash,
                timestamp=time.time(),
                metadata={
                    "artifact_index": i,
                    "artifact_type": type(artifact).__name__,
                    "total_artifacts": len(artifacts)
                },
                prev_ohash=prev_ohash
            )

            ohash, full_payload = self.generate_ohash(payload)
            chain.append(full_payload)
            prev_ohash = ohash

        return chain

    def verify_chain(self, chain: list) -> bool:
        """
        Verify integrity of OHASH chain
        """
        if not chain:
            return False

        for i in range(len(chain)):
            current = chain[i]

            # Verify hash calculation
            payload_data = current["payload"]
            payload = OHashPayload(**payload_data)

            expected_ohash, _ = self.generate_ohash(payload)
            if expected_ohash != current["ohash"]:
                return False

            # Verify chain links
            if i > 0:
                if payload.prev_ohash != chain[i - 1]["ohash"]:
                    return False

        return True

    def generate_keypair(self) -> Tuple[ed25519.Ed25519PrivateKey, ed25519.Ed25519PublicKey]:
        """
        Generate Ed25519 keypair for author signing
        """
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        return private_key, public_key

    def sign_payload(self, private_key: ed25519.Ed25519PrivateKey, payload: bytes) -> bytes:
        """
        Sign payload with private key
        """
        return private_key.sign(payload)

    def verify_signature(
        self,
        public_key: ed25519.Ed25519PublicKey,
        signature: bytes,
        payload: bytes
    ) -> bool:
        """
        Verify signature with public key
        """
        try:
            public_key.verify(signature, payload)
            return True
        except:
            return False

    def _hash_artifact(self, artifact: Any) -> str:
        """
        Hash an artifact (paper, code, data, etc.)
        """
        if isinstance(artifact, str):
            artifact_bytes = artifact.encode("utf-8")
        elif isinstance(artifact, dict):
            artifact_bytes = json.dumps(artifact, sort_keys=True).encode("utf-8")
        else:
            artifact_bytes = str(artifact).encode("utf-8")

        return hashlib.sha3_256(artifact_bytes).hexdigest()


# Example usage
if __name__ == "__main__":
    # Example: Generate OHASH for a paper
    engine = OHashEngine()

    # Create payload
    payload = OHashPayload(
        orcid="0009-0008-2973-4047",
        artifact_hash="abc123def456",
        timestamp=time.time(),
        metadata={
            "title": "Foundations of Antifragile Quantum-Semantic Systems",
            "authors": ["Mateus Alves Arêas"],
            "version": "1.0.0"
        }
    )

    # Generate OHASH
    ohash, full_payload = engine.generate_ohash(payload)
    print(f"OHASH: {ohash}")
    print(f"Payload: {json.dumps(full_payload, indent=2)}")

    # Generate keypair for signing
    private_key, public_key = engine.generate_keypair()

    # Sign the payload
    signature = engine.sign_payload(private_key, payload.to_bytes())
    print(f"Signature: {signature.hex()}")

    # Verify signature
    is_valid = engine.verify_signature(public_key, signature, payload.to_bytes())
    print(f"Signature valid: {is_valid}")
