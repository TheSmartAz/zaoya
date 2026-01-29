"""Pydantic schemas for experiments API."""

from typing import Optional, Any, Literal
from pydantic import BaseModel, Field, field_validator, model_validator


class ConversionGoal(BaseModel):
    """Conversion goal definition for experiments."""
    type: Literal["page_view", "cta_click", "form_submit"]
    url: Optional[str] = None
    element_id: Optional[str] = None
    form_id: Optional[str] = None

    @model_validator(mode="after")
    def validate_goal(self) -> "ConversionGoal":
        if self.type == "page_view" and not self.url:
            raise ValueError("page_view goal requires url")
        if self.type == "cta_click" and not self.element_id:
            raise ValueError("cta_click goal requires element_id")
        if self.type == "form_submit" and not self.form_id:
            raise ValueError("form_submit goal requires form_id")
        return self


class ExperimentCreateRequest(BaseModel):
    """Request to create a new experiment."""
    name: str = Field(..., min_length=3)
    traffic_split: list[float]
    conversion_goal: ConversionGoal

    @field_validator("traffic_split")
    @classmethod
    def validate_split(cls, value: list[float]) -> list[float]:
        if not value or len(value) < 2:
            raise ValueError("traffic_split must include at least two variants")
        if any(v < 0 for v in value):
            raise ValueError("traffic_split values must be non-negative")
        if abs(sum(value) - 100) > 0.01:
            raise ValueError("traffic_split must total 100%")
        return value


class ExperimentUpdateRequest(BaseModel):
    """Request to update an experiment."""
    name: Optional[str] = Field(None, min_length=3)
    traffic_split: Optional[list[float]] = None
    conversion_goal: Optional[ConversionGoal] = None

    @field_validator("traffic_split")
    @classmethod
    def validate_split(cls, value: Optional[list[float]]) -> Optional[list[float]]:
        if value is None:
            return value
        if not value or len(value) < 2:
            raise ValueError("traffic_split must include at least two variants")
        if any(v < 0 for v in value):
            raise ValueError("traffic_split values must be non-negative")
        if abs(sum(value) - 100) > 0.01:
            raise ValueError("traffic_split must total 100%")
        return value


class VariantCreateRequest(BaseModel):
    """Request to add a variant to an experiment."""
    name: str = Field(..., min_length=1)
    is_control: bool = False
    snapshot_id: Optional[str] = None
    page_content: Optional[dict[str, Any]] = None


class VariantUpdateRequest(BaseModel):
    """Request to update a variant."""
    name: Optional[str] = None
    page_content: Optional[dict[str, Any]] = None


class TrackConversionRequest(BaseModel):
    """Request to track a conversion."""
    goal_type: str
    goal_metadata: Optional[dict[str, Any]] = None
