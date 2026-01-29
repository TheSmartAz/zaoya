"""Snapshot tools for build runtime."""

from __future__ import annotations

from app.services.snapshot_service import get_snapshot_service


class SnapshotTools:
    def __init__(self, project_id: str):
        self.project_id = project_id

    async def create(self, reason: str, metadata: dict | None = None) -> str:
        svc = get_snapshot_service()
        return await svc.create(project_id=self.project_id, reason=reason, metadata=metadata)

    async def restore(self, snapshot_id: str) -> bool:
        svc = get_snapshot_service()
        try:
            await svc.restore(snapshot_id, self.project_id)
            return True
        except Exception:
            return False
