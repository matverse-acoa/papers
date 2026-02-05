from __future__ import annotations

import argparse
from pathlib import Path

from .auditor import build_audit_report, write_audit_report
from .btc_anchor import anchor_bitcoin
from .integrity import save_guard
from .notary import notarize_ledger
from .runtime import run_loop
from .zenodo_export import build_zenodo_package


def main() -> None:
    parser = argparse.ArgumentParser(description="Run civilizational evidence pipeline")
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--blocks", type=int, default=128)
    parser.add_argument("--tick", type=float, default=0.0)
    parser.add_argument("--orcid", default="0009-0008-2973-4047")
    parser.add_argument("--anchor-address", default="bc1qexample")
    parser.add_argument("--live-anchor", action="store_true")
    parser.add_argument("--output-dir", default=".")
    args = parser.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    ledger_file = Path(args.ledger)
    run_loop(str(ledger_file), orcid=args.orcid, tick_seconds=args.tick, max_blocks=args.blocks)

    guard_file = out / "guardian.json"
    save_guard(ledger_file, guard_file)

    anchor_file = out / "bitcoin_anchor.json"
    anchor_bitcoin(
        ledger_file,
        anchor_file,
        address=args.anchor_address,
        dry_run=not args.live_anchor,
    )

    notarization_file = out / "notarization.json"
    notarize_ledger(ledger_file, notarization_file, orcid=args.orcid)

    audit_file = out / "audit_report.json"
    audit = build_audit_report(ledger_file, bitcoin_anchor_file=anchor_file, notarization_file=notarization_file)
    write_audit_report(audit, audit_file)

    zip_file = out / "matverse_snapshot.zip"
    metadata_file = out / "zenodo_metadata.json"
    build_zenodo_package(
        [ledger_file, out / "guardian.json", anchor_file, notarization_file, audit_file],
        zip_file,
        metadata_file,
    )

    print(f"PACKAGE READY: {zip_file}")
    print(f"METADATA READY: {metadata_file}")


if __name__ == "__main__":
    main()
