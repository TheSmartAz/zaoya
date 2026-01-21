"""Pydantic models for API requests/responses"""
from pydantic import BaseModel
from typing import List, Optional, Dict


class Message(BaseModel):
    """Chat message"""
    role: str
    content: str
    id: Optional[str] = None
    timestamp: Optional[int] = None


class TemplateContext(BaseModel):
    """Template context for prompt building"""
    id: str
    name: str
    systemPromptAddition: str


class ChatRequest(BaseModel):
    """Chat API request"""
    messages: List[Message]
    model: Optional[str] = None
    stream: bool = True
    template: Optional[TemplateContext] = None
    templateInputs: Optional[Dict[str, str]] = None
    interviewAnswers: Optional[Dict[str, str]] = None
    isQuickAction: bool = False


class VersionMetadata(BaseModel):
    """Version metadata"""
    prompt: str
    timestamp: int
    changeType: str


class Version(BaseModel):
    """Code snapshot version"""
    id: str
    projectId: str
    number: int
    html: str
    js: Optional[str] = None
    metadata: VersionMetadata


class CreateVersionRequest(BaseModel):
    """Request to create a new version"""
    projectId: str
    html: str
    js: Optional[str] = None
    metadata: VersionMetadata


class RestoreVersionRequest(BaseModel):
    """Request to restore a version"""
    versionId: str


class ListVersionsResponse(BaseModel):
    """Response with all versions for a project"""
    versions: List[Version]
    currentVersionId: Optional[str] = None
