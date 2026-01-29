"""Telemetry helpers for build task estimates."""

from __future__ import annotations

from datetime import datetime


TEMPLATE_ESTIMATES = {
    "planning": 1000,
    "generation": 3000,
    "validation": 1500,
    "assets": 2000,
    "storage": 500,
    "finalization": 800,
}


class BuildTelemetry:
    """Collect data to improve task estimates."""

    def __init__(self, analytics=None) -> None:
        self.analytics = analytics

    async def record_task_duration(
        self,
        task_category: str,
        actual_ms: int,
        page_complexity: str = "medium",
    ) -> None:
        if not self.analytics:
            return
        await self.analytics.record(
            {
                "event": "task_duration",
                "category": task_category,
                "actual_ms": actual_ms,
                "complexity": page_complexity,
                "timestamp": datetime.utcnow(),
            }
        )

    def get_calibrated_estimate(self, category: str, complexity: str = "medium") -> int:
        return TEMPLATE_ESTIMATES.get(category, 2000)
