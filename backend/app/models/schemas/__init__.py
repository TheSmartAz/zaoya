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
