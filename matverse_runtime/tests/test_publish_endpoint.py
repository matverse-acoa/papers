import base64

from fastapi.testclient import TestClient

from matverse_runtime.main import app


def test_publish_fortified_success(monkeypatch):
    def fake_validate(tx_id: str) -> bool:
        return tx_id == "pbse_ok"

    def fake_publish(tx_id: str, metadata: dict, files: list[str]):
        assert tx_id == "pbse_ok"
        assert metadata["title"] == "T"
        assert files
        return {
            "doi": "10.5281/zenodo.123",
            "ipfs": "bafy123",
            "evidence_hash": "0xabc",
            "commit": "a1b2c3d",
        }

    monkeypatch.setattr("matverse_runtime.publish_endpoint.validate_tx_id", fake_validate)
    monkeypatch.setattr("matverse_runtime.publish_endpoint.run_fortified_publish", fake_publish)

    client = TestClient(app)
    response = client.post(
        "/publish/fortified",
        json={
            "tx_id": "pbse_ok",
            "metadata": {"title": "T"},
            "files": [base64.b64encode(b"x").decode("ascii")],
        },
    )

    assert response.status_code == 200
    assert response.json()["doi"] == "10.5281/zenodo.123"


def test_publish_fortified_forbidden(monkeypatch):
    monkeypatch.setattr("matverse_runtime.publish_endpoint.validate_tx_id", lambda _tx: False)
    client = TestClient(app)

    response = client.post(
        "/publish/fortified",
        json={"tx_id": "bad", "metadata": {}, "files": []},
    )

    assert response.status_code == 403
