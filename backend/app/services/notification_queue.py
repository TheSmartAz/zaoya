"""Notification queue for async email sending."""

import asyncio
from collections import deque
from typing import TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from ..models.submission import FormSubmission


class NotificationQueue:
    """
    Async queue for sending email notifications.

    Processes notifications in the background to avoid blocking
    the main request/response cycle.
    """

    def __init__(self):
        self.queue = deque()
        self._running = False
        self._lock = asyncio.Lock()

    async def add(
        self,
        to_email: str,
        project_name: str,
        project_id: str,
        public_id: str,
        submission_data: dict,
    ) -> None:
        """
        Add a notification to the queue.

        Args:
            to_email: Recipient email address
            project_name: Name of the project
            project_id: Project ID
            public_id: Public ID of the published page
            submission_data: Form submission data
        """
        self.queue.append({
            "to_email": to_email,
            "project_name": project_name,
            "project_id": project_id,
            "public_id": public_id,
            "submission_data": submission_data,
        })

        # Start processing if not already running
        if not self._running:
            asyncio.create_task(self._process())

    async def _process(self) -> None:
        """Process queued notifications."""
        async with self._lock:
            if self._running:
                return
            self._running = True

        try:
            from .email_service import email_service

            while self.queue:
                notification = self.queue.popleft()

                try:
                    await email_service.send_submission_notification(
                        to_email=notification["to_email"],
                        project_name=notification["project_name"],
                        project_id=notification["project_id"],
                        public_id=notification["public_id"],
                        submission_data=notification["submission_data"],
                    )
                except Exception as e:
                    # Log but continue processing
                    print(f"Notification failed: {e}")
                    # Could implement retry logic here

        finally:
            async with self._lock:
                self._running = False

    async def drain(self) -> None:
        """Wait for all queued notifications to be processed."""
        while self.queue or self._running:
            await asyncio.sleep(0.1)


# Global singleton instance
notification_queue = NotificationQueue()
