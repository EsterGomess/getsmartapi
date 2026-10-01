"""Send a notification email when a user's email is changed."""
from app.config import settings
from app.services.email import send_template_email


async def send_email_changed_notification(
    to: str,
    old_email: str,
    new_email: str,
) -> None:
    """Send an email notification to the user when their email address is changed."""
    await send_template_email(
        to=to,
        subject="Your email was changed",
        template_name="emails/email_changed.html",
        forgot_url=f"{settings.FRONTEND_URL}/forgot-password",
        old_email=old_email,
        new_email=new_email,
    )