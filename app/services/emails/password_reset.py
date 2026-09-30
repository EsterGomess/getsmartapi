"""Send a password reset email."""

from app.config import settings
from app.services.email import send_template_email


async def send_password_reset_email(to: str, token: str) -> None:
    """Send a password reset email to the specified address."""
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"

    await send_template_email(
        to=to,
        subject="Reset your password",
        template_name="emails/password_reset.html",
        reset_url=reset_url,
        expires_minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES,
    )
