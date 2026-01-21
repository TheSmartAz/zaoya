"""Email service for sending notifications.

This service uses Resend API as the default email provider.
To use a different provider, implement the _send method accordingly.
"""

import httpx
import os
from typing import Optional
from string import Template


class EmailService:
    """Email service for sending notifications."""

    def __init__(self):
        self.api_key = os.getenv("RESEND_API_KEY") or os.getenv("EMAIL_API_KEY")
        self.from_email = os.getenv("EMAIL_FROM", "noreply@zaoya.app")
        self.from_name = os.getenv("EMAIL_FROM_NAME", "Zaoya")
        self.base_url = os.getenv("EMAIL_API_URL", "https://api.resend.com/emails")

    async def send_submission_notification(
        self,
        to_email: str,
        project_name: str,
        project_id: str,
        public_id: str,
        submission_data: dict,
    ) -> bool:
        """
        Send an email notification for a new form submission.

        Args:
            to_email: Recipient email address
            project_name: Name of the project
            project_id: Project ID
            public_id: Public ID of the published page
            submission_data: Form submission data

        Returns:
            True if email was sent successfully, False otherwise
        """
        if not self.api_key:
            # Silently skip if no API key configured
            return False

        subject = f"New submission on \"{project_name}\""

        # Format submission fields
        fields_text = ""
        for key, value in submission_data.items():
            if value:
                display_key = key.replace("_", " ").replace("-", " ").title()
                if isinstance(value, list):
                    value_str = ", ".join(str(v) for v in value[:5])
                    if len(value) > 5:
                        value_str += f" (+{len(value) - 5} more)"
                else:
                    value_str = str(value)[:200]
                fields_text += f"\n  {display_key}: {value_str}"

        body = f"""You received a new form submission on your Zaoya page "{project_name}".

Submission details:{fields_text}

---
View all submissions: https://zaoya.app/editor/{project_id}/submissions
View your page: https://zaoya.app/p/{public_id}

Zaoya - Describe it. See it. Share it.
"""

        return await self._send(to_email, subject, body)

    async def send_test_email(
        self,
        to_email: str,
    ) -> bool:
        """Send a test email to verify configuration."""
        subject = "Zaoya - Test Email"
        body = """This is a test email from Zaoya.

If you received this, your email notification is configured correctly!

---
Zaoya - Describe it. See it. Share it.
"""
        return await self._send(to_email, subject, body)

    async def _send(self, to: str, subject: str, body: str) -> bool:
        """
        Send an email using the configured provider.

        Default implementation uses Resend API.
        Override this method to use a different provider.
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "from": f"{self.from_name} <{self.from_email}>",
                        "to": [to],
                        "subject": subject,
                        "text": body,
                    },
                )

                if response.status_code == 200:
                    return True

                # Log error but don't raise
                print(f"Email send failed: {response.status_code} {response.text}")
                return False

        except Exception as e:
            # Log error but don't raise - email failures shouldn't break the app
            print(f"Email send error: {e}")
            return False


# Global singleton instance
email_service = EmailService()
