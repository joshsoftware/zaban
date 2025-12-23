import os
from typing import Optional
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


class EmailService:
    """Service for sending emails via SendGrid"""

    def __init__(self):
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        self.from_email = os.getenv("SENDGRID_FROM_EMAIL")

    def _build_email_bodies(self, reset_link: str) -> tuple[str, str]:
        """Return (text_body, html_body) for the reset email."""
        text_body = f"""
        Password Reset Request

        Hello,

        We received a request to reset your password for your Zaban account.

        Click the link below to reset your password:
        {reset_link}

        This link will expire in 1 hour.

        If you didn't request a password reset, please ignore this email.

        Best regards,
        The Zaban Team
        """

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .button {{ display: inline-block; padding: 12px 24px; background-color: #f97316; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .button:hover {{ background-color: #ea580c; }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Password Reset Request</h2>
                <p>Hello,</p>
                <p>We received a request to reset your password for your Zaban account.</p>
                <p>Click the button below to reset your password:</p>
                <a href="{reset_link}" class="button">Reset Password</a>
                <p>This link will expire in 1 hour.</p>
                <p>If you didn't request a password reset, please ignore this email.</p>
                <div class="footer">
                    <p>Best regards,<br>The Zaban Team</p>
                </div>
            </div>
        </body>
        </html>
        """
        return text_body, html_body

    def send_password_reset_email(self, to_email: str, reset_token: str) -> bool:
        """
        Send password reset email to user via SendGrid

        Args:
            to_email: Recipient email address
            reset_token: Password reset token

        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.sendgrid_api_key or not self.from_email:
            print("⚠️  SendGrid is not configured. Email sending disabled.")
            print("   Set SENDGRID_API_KEY and SENDGRID_FROM_EMAIL to enable email.")
            return False

        reset_link = f"{self.frontend_url}/reset-password?token={reset_token}"
        text_body, html_body = self._build_email_bodies(reset_link)

        message = Mail(
            from_email=self.from_email,
            to_emails=to_email,
            subject='Reset Your Password - Zaban',
            html_content=html_body,
            plain_text_content=text_body
        )

        try:
            sg = SendGridAPIClient(self.sendgrid_api_key)
            response = sg.send(message)
            
            if response.status_code in (200, 201, 202):
                print(f"✅ Password reset email sent to {to_email} via SendGrid")
                return True
            else:
                print(f"❌ Failed to send email. Status Code: {response.status_code}")
                # print(response.body)
                return False

        except Exception as e:
            print(f"❌ Failed to send password reset email to {to_email}: {e}")
            return False


# Singleton instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get or create email service instance"""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
