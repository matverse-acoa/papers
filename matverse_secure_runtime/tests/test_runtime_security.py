import json
from pathlib import Path

from matverse_secure_runtime.ledger import AppendOnlyLedger
from matverse_secure_runtime.runtime import run_loop
from matverse_secure_runtime.replay import replay_verify


def test_runtime_generates_evidence_ohash_and_security_chain(tmp_path: Path):
    ledger_path = tmp_path / "ledger.jsonl"

    run_loop(str(ledger_path), orcid="0009-0008-2973-4047", tick_seconds=0.0, max_blocks=3)

    ledger = AppendOnlyLedger(ledger_path)
    blocks = ledger.read_blocks()
    assert len(blocks) == 3

    for block in blocks:
        assert "evidence_note" in block
        assert "ohash" in block
        assert block["evidence_note"]["ohash"] == block["ohash"]
        assert "signature" in block
        assert "merkle_root" in block

    replay_verify(str(ledger_path))

    with ledger_path.open("r", encoding="utf-8") as file:
        rows = [json.loads(line) for line in file if line.strip()]
    assert rows[-1]["payload"]["parent_hash"] == rows[-2]["hash"]
