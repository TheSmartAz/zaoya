"""Pydantic schemas for multi-page API requests/responses."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID


# ============= Design System =============

class DesignSystem(BaseModel):
    colors: Dict[str, str] = Field(default_factory=dict)
    typography: Dict[str, str] = Field(default_factory=dict)
    spacing: Dict[str, str] = Field(default_factory=dict)
    components: Dict[str, Any] = Field(default_factory=dict)


class NavigationConfig(BaseModel):
    header: Dict[str, Any] = Field(default_factory=dict)
    footer: Dict[str, Any] = Field(default_factory=dict)
    pages: List[Dict[str, Any]] = Field(default_factory=list)


# ============= Draft =============

class DraftResponse(BaseModel):
    id: UUID
    project_id: UUID
    version_number: int
    summary: Optional[str] = None
    design_system: DesignSystem
    navigation: NavigationConfig
    created_at: datetime

    class Config:
        from_attributes = True


class DraftUpdate(BaseModel):
    design_system: Optional[DesignSystem] = None
    navigation: Optional[NavigationConfig] = None
    summary: Optional[str] = None


# ============= Pages =============

class PageCreate(BaseModel):
    slug: str = Field(..., pattern=r'^[a-z0-9]([a-z0-9-]*[a-z0-9])?$')
    title: str
    html: str
    js: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_home: bool = False


class PageUpdate(BaseModel):
    slug: Optional[str] = Field(None, pattern=r'^[a-z0-9]([a-z0-9-]*[a-z0-9])?$')
    title: Optional[str] = None
    html: Optional[str] = None
    js: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    display_order: Optional[int] = None


class PageResponse(BaseModel):
    id: UUID
    slug: str
    title: str
    html: str
    js: Optional[str]
    metadata: Dict[str, Any]
    is_home: bool
    display_order: int
    created_at: datetime

    class Config:
        from_attributes = True


class ReorderPagesRequest(BaseModel):
    page_ids: List[UUID]


# ============= Snapshots =============

class SnapshotResponse(BaseModel):
    id: UUID
    project_id: UUID
    version_number: int
    summary: Optional[str]
    design_system: DesignSystem
    navigation: NavigationConfig
    is_draft: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SnapshotWithPages(SnapshotResponse):
    pages: List[PageResponse]


class CreateSnapshotRequest(BaseModel):
    summary: Optional[str] = None


class RestoreSnapshotRequest(BaseModel):
    snapshot_id: UUID


# ============= Versions =============

class VersionChangeSummary(BaseModel):
    files_changed: int = 0
    lines_added: int = 0
    lines_deleted: int = 0
    tasks_completed: List[str] = Field(default_factory=list)
    description: str = ""


class VersionPage(BaseModel):
    id: UUID
    name: str
    slug: Optional[str] = None
    path: str
    is_home: bool
    content: Dict[str, Any] = Field(default_factory=dict)
    design_system: Dict[str, Any] = Field(default_factory=dict)
    sort_order: int = 0
    lines_added: Optional[int] = None
    lines_deleted: Optional[int] = None
    is_missing: Optional[bool] = None


class VersionResponse(BaseModel):
    id: UUID
    project_id: UUID
    parent_version_id: Optional[UUID] = None
    branch_id: Optional[UUID] = None
    branch_label: Optional[str] = None
    created_at: datetime
    trigger_message_id: Optional[UUID] = None
    snapshot_id: Optional[UUID] = None
    change_summary: VersionChangeSummary
    validation_status: str
    is_pinned: bool

    class Config:
        from_attributes = True


class VersionDetailResponse(VersionResponse):
    pages: List[VersionPage]


class VersionQuota(BaseModel):
    limit: int
    used: int
    warning: bool
    can_create: bool


class VersionListResponse(BaseModel):
    versions: List[VersionResponse]
    quota: Optional[VersionQuota] = None


class VersionRollbackRequest(BaseModel):
    page_ids: List[UUID]


# ============= Branches =============

class BranchResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    label: Optional[str] = None
    parent_branch_id: Optional[UUID] = None
    created_from_version_id: Optional[UUID] = None
    is_default: bool
    created_at: datetime

    class Config:
        from_attributes = True


class BranchListResponse(BaseModel):
    branches: List[BranchResponse]
    active_branch_id: Optional[UUID] = None


class BranchCreateRequest(BaseModel):
    name: str
    label: Optional[str] = None
    set_active: bool = True
