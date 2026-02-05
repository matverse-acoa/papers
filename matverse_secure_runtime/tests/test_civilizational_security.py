import json
from pathlib import Path

import pytest

from matverse_secure_runtime.auditor import build_audit_report
from matverse_secure_runtime.btc_anchor import anchor_bitcoin
from matverse_secure_runtime.integrity import save_guard, watchdog
from matverse_secure_runtime.notary import notarize_ledger
from matverse_secure_runtime.runtime import run_loop
from matverse_secure_runtime.zenodo_export import build_zenodo_package


def _build_ledger(path: Path, blocks: int = 4) -> None:
    run_loop(str(path), orcid="0009-0008-2973-4047", tick_seconds=0.0, max_blocks=blocks)


def test_integrity_watchdog_detects_rewrite(tmp_path: Path):
    ledger = tmp_path / "ledger.jsonl"
    guard = tmp_path / "guardian.json"
    _build_ledger(ledger, blocks=2)

    save_guard(ledger, guard)
    assert watchdog(ledger, guard) is True

    with ledger.open("a", encoding="utf-8") as file:
        file.write('{"tamper":true}\n')

    with pytest.raises(SystemExit):
        watchdog(ledger, guard)


def test_audit_anchor_notary_and_zenodo_package(tmp_path: Path):
    ledger = tmp_path / "ledger.jsonl"
    _build_ledger(ledger, blocks=3)

    anchor = tmp_path / "bitcoin_anchor.json"
    note = tmp_path / "notarization.json"
    audit_path = tmp_path / "audit_report.json"
    zip_path = tmp_path / "snapshot.zip"
    metadata = tmp_path / "zenodo_metadata.json"

    anchor_data = anchor_bitcoin(ledger, anchor, address="bc1qexample", dry_run=True)
    assert anchor_data["status"] == "dry_run"

    note_data = notarize_ledger(ledger, note)
    assert note_data["orcid"] == "0009-0008-2973-4047"

    report = build_audit_report(ledger, bitcoin_anchor_file=anchor, notarization_file=note)
    audit_path.write_text(json.dumps(report), encoding="utf-8")
    assert report["ledger_blocks"] == 3
    assert report["bitcoin_anchor"]["status"] == "dry_run"

    build_zenodo_package([ledger, anchor, note, audit_path], zip_path, metadata)
    assert zip_path.exists()
    metadata_obj = json.loads(metadata.read_text(encoding="utf-8"))
    assert metadata_obj["creators"][0]["orcid"] == "0009-0008-2973-4047"
