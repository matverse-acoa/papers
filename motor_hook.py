#!/usr/bin/env python3
"""Hook mínimo para integrar produtor de artefatos ao pipeline fortificado v11."""

from __future__ import annotations

import asyncio
import json

from matverse_v11 import MatVerseIntegratedSystemV11


async def main() -> None:
    system = MatVerseIntegratedSystemV11()

    health = await system.health_check()
    print("health:", json.dumps(health, ensure_ascii=False))

    work = {
        "id": "engine-001",
        "title": "Teste do Motor",
        "authors": [{"name": "Equipe"}],
        "abstract": "Artefato produzido pelo motor de processamento.",
        "content": {"demo": True},
        "metadata": {"orcid": "0000-0000-0000-0000"},
    }

    result = await system.publish_scientific_work(work)
    print("success:", result.get("success"))
    print("evidence:", json.dumps(result.get("evidence_chain", {}), ensure_ascii=False))
    print("doi_ready:", json.dumps(result.get("doi_ready_artifact", {}), ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
