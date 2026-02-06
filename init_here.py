#!/usr/bin/env python3
"""Inicializa publicação diretamente no repositório de papers atual."""

from __future__ import annotations

import argparse
import asyncio

from matverse_fortified_publisher import FortifiedPublisher, PaperRepository


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-path", default=".")
    parser.add_argument("--title", default="Primeiro Paper")
    parser.add_argument("--abstract", default="Teste no repo remoto")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo = PaperRepository(repo_path=args.repo_path)
    created = repo.create_paper(
        title=args.title,
        authors=[{"name": "Equipe"}],
        abstract=args.abstract,
        category="draft",
    )
    publisher = FortifiedPublisher(repo_path=args.repo_path)
    result = asyncio.run(publisher.publish_paper(created["paper_id"], ["zenodo", "github"]))
    print("OK:", created["paper_id"], result.get("success"))


if __name__ == "__main__":
    main()
