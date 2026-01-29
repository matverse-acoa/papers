from __future__ import annotations

from typing import List

from publishers.github import GitHubPublisher
from publishers.local_archive import LocalArchivePublisher
from publishers.zenodo import ZenodoPublisher


PUBLISHER_REGISTRY = {
    "github": GitHubPublisher,
    "local_archive": LocalArchivePublisher,
    "zenodo": ZenodoPublisher,
}


def load_publishers() -> List[object]:
    names = [name.strip() for name in _publisher_list()]
    publishers: List[object] = []
    for name in names:
        cls = PUBLISHER_REGISTRY.get(name)
        if not cls:
            raise RuntimeError(f"Unknown publisher: {name}")
        publishers.append(cls())
    return publishers


def _publisher_list():
    import os

    configured = os.getenv("MATVERSE_PUBLISHERS", "local_archive")
    return [name for name in configured.split(",") if name.strip()]
