import base64

import pytest

from matverse_fortified_publisher import run_fortified_publish


def test_run_fortified_publish_success(tmp_path, monkeypatch):
    monkeypatch.delenv("ZENODO_TOKEN", raising=False)
    monkeypatch.delenv("MATVERSE_PAPERS_REPO", raising=False)

    result = run_fortified_publish(
        tx_id="pbse_tx_ok",
        metadata={"title": "Runtime", "description": "Desc", "creators": [{"name": "MatVerse"}]},
        files=[base64.b64encode(b"hello").decode("ascii")],
        repo_path=str(tmp_path / "papers"),
    )

    assert result["doi"].startswith("10.5281/zenodo.")
    assert result["ipfs"].startswith("bafy")
    assert result["evidence_hash"]
    assert result["commit"] == ""


def test_run_fortified_publish_invalid_tx(tmp_path):
    with pytest.raises(PermissionError):
        run_fortified_publish(
            tx_id="invalid",
            metadata={},
            files=[],
            repo_path=str(tmp_path / "papers"),
        )
