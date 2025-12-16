import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional


class EmailService:
    """Service for sending emails via SMTP"""

    def __init__(self):
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        self.smtp_host = os.getenv("SMTP_HOST", "")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.smtp_from_email = os.getenv("SMTP_FROM_EMAIL", "")

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
        Send password reset email to user via SMTP

        Args:
            to_email: Recipient email address
            reset_token: Password reset token

        Returns:
            True if email sent successfully, False otherwise
        """
        if not all([self.smtp_host, self.smtp_username, self.smtp_password, self.smtp_from_email]):
            print("⚠️  SMTP is not configured. Email sending disabled.")
            print("   Set SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, and SMTP_FROM_EMAIL to enable email.")
            return False

        reset_link = f"{self.frontend_url}/reset-password?token={reset_token}"
        text_body, html_body = self._build_email_bodies(reset_link)

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = "Reset Your Password - Zaban"
            msg['From'] = self.smtp_from_email
            msg['To'] = to_email

            part1 = MIMEText(text_body, 'plain')
            part2 = MIMEText(html_body, 'html')
            msg.attach(part1)
            msg.attach(part2)

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            print(f"✅ Password reset email sent to {to_email} via SMTP")
            return True

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
