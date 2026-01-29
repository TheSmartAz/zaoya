"""Form submission models and storage."""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime


class FormSubmissionRequest(BaseModel):
    """Request model for form submission."""
    form_id: Optional[str] = Field(default="default", description="Form identifier")
    data: Dict[str, Any] = Field(..., description="Form field data")


class FormSubmission(BaseModel):
    """Form submission model."""
    id: str
    project_id: str
    public_id: str
    form_id: str = "default"

    # Sanitized form data
    data: Dict[str, Any]

    # Metadata about the submission
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Notification tracking
    notification_sent: bool = False
    notification_sent_at: Optional[datetime] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "public_id": self.public_id,
            "form_id": self.form_id,
            "data": self.data,
            "metadata": {
                **self.metadata,
                "created_at": self.created_at.isoformat(),
            },
            "notification_sent": self.notification_sent,
        }


# In-memory storage (replace with database in production)
_submissions_storage: Dict[str, FormSubmission] = {}


def generate_submission_id() -> str:
    """Generate a unique submission ID."""
    import time
    import secrets
    return f"sub_{int(time.time())}_{secrets.token_hex(4)}"


def create_submission(
    project_id: str,
    public_id: str,
    form_id: str,
    data: Dict[str, Any],
    metadata: Dict[str, Any],
) -> FormSubmission:
    """Create and store a new form submission."""
    submission_id = generate_submission_id()

    submission = FormSubmission(
        id=submission_id,
        project_id=project_id,
        public_id=public_id,
        form_id=form_id,
        data=data,
        metadata=metadata,
    )

    _submissions_storage[submission_id] = submission
    return submission


def get_submission(submission_id: str) -> Optional[FormSubmission]:
    """Get a submission by ID."""
    return _submissions_storage.get(submission_id)


def get_project_submissions(
    project_id: str,
    form_id: Optional[str] = None,
    offset: int = 0,
    limit: int = 50,
) -> tuple[list[FormSubmission], int]:
    """
    Get all submissions for a project.

    Returns:
        Tuple of (submissions, total_count)
    """
    submissions = [
        s for s in _submissions_storage.values()
        if s.project_id == project_id and (form_id is None or s.form_id == form_id)
    ]

    # Sort by created_at descending
    submissions.sort(key=lambda s: s.created_at, reverse=True)

    total = len(submissions)
    paginated = submissions[offset:offset + limit]

    return paginated, total


def count_submissions(
    project_id: str,
    form_id: Optional[str] = None,
) -> int:
    """Count submissions for a project."""
    count = 0
    for s in _submissions_storage.values():
        if s.project_id == project_id and (form_id is None or s.form_id == form_id):
            count += 1
    return count


def get_all_project_submissions(
    project_id: str,
    form_id: Optional[str] = None,
) -> list[FormSubmission]:
    """Get all submissions for a project (no pagination)."""
    submissions = [
        s for s in _submissions_storage.values()
        if s.project_id == project_id and (form_id is None or s.form_id == form_id)
    ]
    submissions.sort(key=lambda s: s.created_at, reverse=True)
    return submissions
