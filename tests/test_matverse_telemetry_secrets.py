import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from matverse_telemetry_secrets import SecretsVault, SecureTelemetryWithSecrets, ThreeBodyMotorWithSecrets


def test_vault_store_and_read_secret():
    vault = SecretsVault(rotation_interval=3600)
    try:
        assert vault.add_secret("session_token", "abc123", ttl=60) is True
        assert vault.get_secret("session_token") == "abc123"
        assert vault.get_secret_hash("session_token") is not None
    finally:
        vault.stop()


def test_telemetry_never_sends_raw_secret():
    vault = SecretsVault(rotation_interval=3600)
    telemetry = SecureTelemetryWithSecrets(vault=vault, enabled=True, secure_channel=True)
    try:
        vault.add_secret("session_token", "super-secret-value", ttl=60)
        telemetry.record_secret_metric("session_token", "created", {"api_key": "should-not-leak"})
        time.sleep(0.2)
        payload_blob = str(telemetry.sent_payloads)
        assert "super-secret-value" not in payload_blob
        assert "should-not-leak" not in payload_blob
        assert "[SECURE_REDACTED]" in payload_blob
    finally:
        telemetry.stop()
        vault.stop()


def test_motor_with_secrets_records_hash_only():
    motor = ThreeBodyMotorWithSecrets()
    try:
        out = motor.process_artifact({"id": "a1"})
        assert out["processed"] is True
        assert out["session_secret_hash"] is not None
        time.sleep(0.2)
        sent = str(motor.telemetry.sent_payloads)
        assert "secret_created" in sent
        assert "[SECURE_REDACTED]" in sent
    finally:
        motor.telemetry.stop()
        motor.secrets_vault.stop()
