from __future__ import annotations

from typing import Optional


class MetricsCollector:
    def __init__(self, trace_id: str) -> None:
        self.trace_id = trace_id
        self._counter = self._build_counter()
        if self._counter:
            self._counter.labels(trace_id=trace_id).inc()

    def _build_counter(self) -> Optional[object]:
        try:
            from prometheus_client import Counter
        except ImportError:
            return None

        return Counter(
            "matverse_deploy_total",
            "Deploy executions",
            ["trace_id"],
        )
