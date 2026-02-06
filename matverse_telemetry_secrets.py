#!/usr/bin/env python3
"""MatVerse v3.3 - Telemetria segura com gerenciamento de segredos."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import queue
import secrets
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional


TELEMETRY_ENABLED = os.getenv("MATVERSE_TELEMETRY_ENABLED", "true").lower() == "true"
TELEMETRY_SECURE = os.getenv("MATVERSE_TELEMETRY_SECURE", "true").lower() == "true"
TELEMETRY_ENDPOINT = os.getenv(
    "MATVERSE_TELEMETRY_ENDPOINT",
    "https://telemetry.matverse.science/secure-ingest",
)
SECRETS_ROTATION_INTERVAL = int(os.getenv("MATVERSE_SECRETS_ROTATION", "3600"))
SECRETS_ALLOWED_KEYS = {
    key.strip() for key in os.getenv("MATVERSE_SECRETS_ALLOWED", "api_key,auth_token,session_token").split(",") if key.strip()
}


@dataclass
class VaultEntry:
    nonce_b64: str
    ciphertext_b64: str
    created_at: float
    ttl: int


class SecretsVault:
    """Vault em memória com criptografia simétrica e rotação opcional."""

    def __init__(self, master_key: Optional[bytes] = None, rotation_interval: int = SECRETS_ROTATION_INTERVAL):
        self.master_key = master_key or secrets.token_bytes(32)
        self.rotation_interval = rotation_interval
        self._entries: Dict[str, VaultEntry] = {}
        self._lock = threading.RLock()
        self._running = True
        self._rotation_thread = threading.Thread(target=self._auto_rotate, daemon=True)
        self._rotation_thread.start()

    def stop(self) -> None:
        self._running = False
        self._rotation_thread.join(timeout=0.2)

    def add_secret(self, key: str, value: str, ttl: int = 86400) -> bool:
        if key not in SECRETS_ALLOWED_KEYS:
            return False
        nonce = secrets.token_bytes(12)
        ciphertext = self._xor_stream(value.encode("utf-8"), nonce)
        entry = VaultEntry(
            nonce_b64=base64.b64encode(nonce).decode("utf-8"),
            ciphertext_b64=base64.b64encode(ciphertext).decode("utf-8"),
            created_at=time.time(),
            ttl=ttl,
        )
        with self._lock:
            self._entries[key] = entry
        return True

    def get_secret(self, key: str) -> Optional[str]:
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return None
            if self._is_expired(entry):
                del self._entries[key]
                return None
        nonce = base64.b64decode(entry.nonce_b64.encode("utf-8"))
        ciphertext = base64.b64decode(entry.ciphertext_b64.encode("utf-8"))
        plaintext = self._xor_stream(ciphertext, nonce)
        return plaintext.decode("utf-8", errors="ignore")

    def get_secret_hash(self, key: str) -> Optional[str]:
        secret = self.get_secret(key)
        if secret is None:
            return None
        return hashlib.sha256(secret.encode("utf-8")).hexdigest()

    def rotate_secret(self, key: str, new_value: Optional[str] = None) -> bool:
        with self._lock:
            current = self._entries.get(key)
            if current is None or self._is_expired(current):
                return False
            ttl = current.ttl
        return self.add_secret(key, new_value or secrets.token_hex(32), ttl=ttl)

    def _is_expired(self, entry: VaultEntry) -> bool:
        return (time.time() - entry.created_at) > entry.ttl

    def _auto_rotate(self) -> None:
        while self._running:
            time.sleep(max(self.rotation_interval, 1))
            with self._lock:
                keys = list(self._entries.keys())
            for key in keys:
                self.rotate_secret(key)

    def _xor_stream(self, data: bytes, nonce: bytes) -> bytes:
        out = bytearray()
        counter = 0
        while len(out) < len(data):
            block = hmac.new(self.master_key, nonce + counter.to_bytes(4, "big"), hashlib.sha256).digest()
            out.extend(block)
            counter += 1
        return bytes(a ^ b for a, b in zip(data, out[: len(data)]))


class SecureTelemetry:
    """Telemetria assíncrona com sanitização e envio seguro simulado."""

    def __init__(self, enabled: bool = TELEMETRY_ENABLED, secure_channel: bool = TELEMETRY_SECURE, endpoint: str = TELEMETRY_ENDPOINT):
        self.enabled = enabled
        self.secure_channel = secure_channel
        self.endpoint = endpoint
        self.metrics_queue: queue.Queue[Dict[str, Any]] = queue.Queue()
        self.sent_payloads: list[Dict[str, Any]] = []
        self._running = True
        self._worker = threading.Thread(target=self._drain_queue, daemon=True)
        self._worker.start()

    def stop(self) -> None:
        self._running = False
        self._worker.join(timeout=0.5)

    def record_metric(self, metric_type: str, data: Dict[str, Any]) -> None:
        if not self.enabled:
            return
        packet = {
            "type": metric_type,
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "data": self._sanitize(data),
        }
        self.metrics_queue.put(packet)

    def _sanitize(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        redacted = {}
        for k, v in payload.items():
            low = k.lower()
            if any(tok in low for tok in ["secret", "token", "password", "private_key", "api_key"]):
                redacted[k] = "[SECURE_REDACTED]"
            elif isinstance(v, dict):
                redacted[k] = self._sanitize(v)
            else:
                redacted[k] = v
        return redacted

    def _drain_queue(self) -> None:
        while self._running:
            try:
                packet = self.metrics_queue.get(timeout=0.1)
            except queue.Empty:
                continue
            self._secure_send(packet)

    def _secure_send(self, packet: Dict[str, Any]) -> None:
        # Stub de envio; preserva payloads para auditoria/testes.
        self.sent_payloads.append({"endpoint": self.endpoint, "secure": self.secure_channel, **packet})


class SecureTelemetryWithSecrets(SecureTelemetry):
    """Telemetria com integração a vault, emitindo apenas metadados/hashes."""

    def __init__(self, vault: SecretsVault, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.vault = vault

    def record_secret_metric(self, key: str, metric_type: str, additional_data: Optional[Dict[str, Any]] = None) -> None:
        if not self.enabled:
            return
        secret_hash = self.vault.get_secret_hash(key)
        if secret_hash is None:
            return
        data = {
            "secret_key": key,
            "secret_hash": secret_hash,
            "additional_data": additional_data or {},
        }
        self.record_metric(f"secret_{metric_type}", data)


class ThreeBodyMotorWithTelemetry:
    """Skeleton compatível para processamento + telemetria."""

    def __init__(self, telemetry: Optional[SecureTelemetry] = None):
        self.telemetry = telemetry or SecureTelemetry()

    def process_artifact(self, artifact_data: Dict[str, Any]) -> Dict[str, Any]:
        self.telemetry.record_metric("artifact_processed", {"artifact_id": artifact_data.get("id", "anon")})
        return {"processed": True, "artifact": artifact_data}


class ThreeBodyMotorWithSecrets(ThreeBodyMotorWithTelemetry):
    """Motor dos Três Corpos com segredos de sessão e telemetria segura."""

    def __init__(self):
        self.secrets_vault = SecretsVault()
        telemetry = SecureTelemetryWithSecrets(self.secrets_vault, enabled=TELEMETRY_ENABLED, secure_channel=TELEMETRY_SECURE)
        super().__init__(telemetry=telemetry)

    def process_artifact(self, artifact_data: Dict[str, Any]) -> Dict[str, Any]:
        token = secrets.token_hex(16)
        self.secrets_vault.add_secret("session_token", token, ttl=300)
        result = super().process_artifact(artifact_data)
        assert isinstance(self.telemetry, SecureTelemetryWithSecrets)
        self.telemetry.record_secret_metric("session_token", "created", {"artifact_id": artifact_data.get("id", "anon")})
        result["session_secret_hash"] = self.secrets_vault.get_secret_hash("session_token")
        return result


if __name__ == "__main__":
    motor = ThreeBodyMotorWithSecrets()
    print(json.dumps(motor.process_artifact({"id": "demo"}), indent=2, ensure_ascii=False))
    time.sleep(0.2)
    print("✅ Motor MatVerse v3.3 pronto com segredos via telemetria segura!")
