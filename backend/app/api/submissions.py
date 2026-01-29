"""Form submission API endpoints."""

from fastapi import APIRouter, HTTPException, Request, Response, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import csv
import io

from ..models.submission import (
    FormSubmissionRequest,
    create_submission,
    get_submission,
    get_project_submissions,
    get_all_project_submissions,
    count_submissions,
)
from ..models.user import get_current_user
from ..services.rate_limiter import form_submission_limiter
from ..services.notification_queue import notification_queue

router = APIRouter()


def sanitize_form_data(data: dict) -> dict:
    """
    Remove potentially dangerous content from form data.

    Args:
        data: Raw form data

    Returns:
        Sanitized form data
    """
    import bleach

    sanitized = {}
    for key, value in data.items():
        # Sanitize keys too (limit length)
        safe_key = str(key)[:100]

        if isinstance(value, str):
            # Strip HTML, limit length
            sanitized[safe_key] = bleach.clean(value[:10000], tags=[], strip=True)
        elif isinstance(value, (int, float, bool)):
            sanitized[safe_key] = value
        elif isinstance(value, list):
            # Limit list size and sanitize each item
            safe_list = []
            for item in value[:100]:
                if isinstance(item, str):
                    safe_list.append(bleach.clean(str(item)[:1000], tags=[], strip=True))
                else:
                    safe_list.append(str(item)[:1000])
            sanitized[safe_key] = safe_list
        elif value is None:
            sanitized[safe_key] = None
        else:
            # Convert other types to string and sanitize
            sanitized[safe_key] = bleach.clean(str(value)[:10000], tags=[], strip=True)

    return sanitized


@router.post("/submissions/{public_id}")
async def submit_form(
    public_id: str,
    request: Request,
    form_data: FormSubmissionRequest,
):
    """
    Submit a form for a published page.

    Rate limited: 10 submissions per hour per IP per page.
    """
    # Import here to avoid circular imports
    from .projects import _published_pages, _projects_storage

    # Verify project exists and is published
    page_data = _published_pages.get(public_id)
    if not page_data:
        raise HTTPException(status_code=404, detail="Page not found")

    project_id = page_data.get("projectId")

    # Rate limit check (by IP + public_id)
    client_ip = request.client.host
    rate_limit_key = f"{client_ip}:{public_id}"

    is_limited, remaining = await form_submission_limiter.check_and_record(
        identifier=rate_limit_key,
        max_attempts=10,
        window_seconds=3600,  # 1 hour
    )

    if is_limited:
        raise HTTPException(
            status_code=429,
            detail="Too many form submissions. Please try again later.",
            headers={
                "Retry-After": "3600",
                "X-RateLimit-Remaining": "0",
            }
        )

    # Sanitize form data
    sanitized_data = sanitize_form_data(form_data.data)

    # Create submission
    submission = create_submission(
        project_id=project_id,
        public_id=public_id,
        form_id=form_data.form_id or "default",
        data=sanitized_data,
        metadata={
            "ip": client_ip,
            "user_agent": request.headers.get("user-agent", "")[:500],
            "referer": request.headers.get("referer", "")[:500],
            "submitted_at": datetime.utcnow().isoformat(),
        }
    )

    # Queue notification if enabled
    project_data = _projects_storage.get(project_id, {})
    if project_data.get("notification_enabled") and project_data.get("notification_email"):
        await notification_queue.add(
            to_email=project_data["notification_email"],
            project_name=project_data.get("name", "Untitled Page"),
            project_id=project_id,
            public_id=public_id,
            submission_data=sanitized_data,
        )

    return {
        "success": True,
        "submission_id": submission.id,
        "message": "Form submitted successfully",
    }


@router.get("/projects/{project_id}/submissions")
async def list_submissions(
    project_id: str,
    page: int = 1,
    per_page: int = 50,
    form_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """
    List form submissions for a project.

    Requires authentication and project ownership.
    """
    # Import here to avoid circular imports
    from .projects import get_project

    # Verify project ownership
    project = get_project(project_id, current_user["id"])
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Validate pagination
    page = max(1, page)
    per_page = min(100, max(1, per_page))

    offset = (page - 1) * per_page

    # Get submissions
    submissions, total = get_project_submissions(
        project_id=project_id,
        form_id=form_id,
        offset=offset,
        limit=per_page,
    )

    return {
        "submissions": [s.to_dict() for s in submissions],
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": (total + per_page - 1) // per_page,
        }
    }


@router.get("/projects/{project_id}/submissions/export")
async def export_submissions(
    project_id: str,
    form_id: Optional[str] = None,
    format: str = "csv",
    current_user: dict = Depends(get_current_user),
):
    """
    Export form submissions for a project.

    Supports CSV and JSON formats.
    """
    # Import here to avoid circular imports
    from .projects import get_project

    # Verify project ownership
    project = get_project(project_id, current_user["id"])
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get all submissions
    submissions = get_all_project_submissions(
        project_id=project_id,
        form_id=form_id,
    )

    if format == "csv":
        output = generate_csv(submissions, project.get("name", "project"))
        filename = f"{project.get('name', 'project')}-submissions-{datetime.now().strftime('%Y%m%d')}.csv"

        return StreamingResponse(
            io.StringIO(output),
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    else:  # JSON format
        return {
            "project_id": project_id,
            "project_name": project.get("name"),
            "exported_at": datetime.utcnow().isoformat(),
            "submissions": [s.to_dict() for s in submissions],
        }


def generate_csv(submissions: List, project_name: str) -> str:
    """
    Generate CSV from form submissions.

    Handles dynamic form fields by collecting all unique keys.
    """
    if not submissions:
        return "No submissions"

    # Collect all unique keys from all submissions
    all_keys = set()
    for s in submissions:
        all_keys.update(s.data.keys())
    sorted_keys = sorted(all_keys)

    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    headers = ["Submitted At", "Form ID"] + [k.replace("_", " ").capitalize() for k in sorted_keys]
    writer.writerow(headers)

    # Data rows
    for s in submissions:
        row = [
            s.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            s.form_id,
        ]
        for key in sorted_keys:
            value = s.data.get(key, "")
            # Handle lists and complex values
            if isinstance(value, list):
                value = ", ".join(str(v) for v in value)
            row.append(str(value) if value else "")
        writer.writerow(row)

    return output.getvalue()


@router.get("/projects/{project_id}/submissions/summary")
async def get_submissions_summary(
    project_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Get a summary of form submissions for a project.
    """
    # Import here to avoid circular imports
    from .projects import get_project

    # Verify project ownership
    project = get_project(project_id, current_user["id"])
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    total = count_submissions(project_id)

    # Get recent submissions (last 7 days)
    from datetime import timedelta
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_count = sum(
        1 for s in get_all_project_submissions(project_id)
        if s.created_at > week_ago
    )

    return {
        "total_submissions": total,
        "recent_submissions": recent_count,
        "last_submission": get_all_project_submissions(project_id)[:1][0].created_at.isoformat() if total > 0 else None,
    }


@router.post("/projects/{project_id}/test-notification")
async def test_notification(
    project_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Send a test notification email to verify email settings.
    """
    # Import here to avoid circular imports
    from .projects import get_project
    from ..services.email_service import email_service

    # Verify project ownership
    project = get_project(project_id, current_user["id"])
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    notification_email = project.get("notification_email") or current_user.get("email")

    if not notification_email:
        raise HTTPException(status_code=400, detail="No email address configured")

    # Send test email
    success = await email_service.send_test_email(notification_email)

    if not success:
        return {
            "success": False,
            "message": "Failed to send test email. Check your email configuration.",
        }

    return {
        "success": True,
        "message": f"Test email sent to {notification_email}",
    }
