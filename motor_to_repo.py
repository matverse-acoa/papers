#!/usr/bin/env python3
"""Executa pipeline fortificada v11 e grava saída versionável no repo."""

from __future__ import annotations

import argparse
import asyncio

from publish_fortified import FortifiedPublicationPipeline, LocalJSONPublisher


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="published")
    return parser.parse_args()


async def _run(output_dir: str) -> None:
    pipeline = FortifiedPublicationPipeline(publishers=[LocalJSONPublisher(output_dir=output_dir)])
    work = {
        "id": "engine-002",
        "title": "Execução Real",
        "authors": [{"name": "Equipe"}],
        "abstract": "Saída do motor v11 gravada no repo.",
        "content": {"ok": True, "references": ["r1"]},
        "evidence": {"dataset": "local"},
    }
    out = await pipeline.execute_publication(work)
    print(out.get("success"), out.get("certificate", {}).get("certificate_version"))


def main() -> None:
    args = parse_args()
    asyncio.run(_run(args.output_dir))


if __name__ == "__main__":
    main()
