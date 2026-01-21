"""Project Pydantic models for API requests/responses."""

from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime


class ProjectCreate(BaseModel):
    """Project creation model."""
    name: str
    template_id: str
    template_inputs: Dict[str, str]


class ProjectResponse(BaseModel):
    """Project response model."""
    id: str
    name: str
    template_id: str
    template_inputs: Dict[str, str]
    status: str
    public_id: Optional[str] = None
    published_url: Optional[str] = None
    created_at: str
    updated_at: str


class PublishResponse(BaseModel):
    """Publish response model."""
    publicId: str
    publishedAt: str
    url: str
