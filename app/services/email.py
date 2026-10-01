""" Email service for sending HTML emails using SMTP."""
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path
from typing import Any

import structlog
from jinja2 import Environment, FileSystemLoader, select_autoescape
from starlette.concurrency import run_in_threadpool

from app.config import settings

logger = structlog.get_logger()

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html", "xml"]),
    enable_async=False,
)


def render_template(template_name: str, **context: Any) -> str:
    """Render a Jinja2 template with the given context."""
    return _env.get_template(template_name).render(**context)


def _send_email_sync(
    to: str,
    subject: str,
    html: str,
    *,
    from_addr: str | None = None,
) -> None:
    """Send an email via SMTP. Blocking — use `send_email` in async code."""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        raise RuntimeError(
            "SMTP credentials are not configured "
            "(SMTP_USER / SMTP_PASSWORD missing)"
        )

    message = EmailMessage()
    message["From"] = from_addr or settings.SMTP_FROM
    message["To"] = to
    message["Subject"] = subject
    message.set_content("Please use an HTML-capable email client.")
    message.add_alternative(html, subtype="html")

    if settings.SMTP_USE_SSL:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(
            settings.SMTP_HOST,
            settings.SMTP_PORT,
            context=context,
            timeout=15,
        ) as server:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(message)
        return

    with smtplib.SMTP(
        settings.SMTP_HOST,
        settings.SMTP_PORT,
        timeout=15,
    ) as server:
        server.ehlo()
        if settings.SMTP_USE_TLS:
            context = ssl.create_default_context()
            server.starttls(context=context)
            server.ehlo()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(message)


async def send_email(
    to: str,
    subject: str,
    html: str,
    *,
    from_addr: str | None = None,
) -> None:
    """Send an HTML email asynchronously.

    - In `EMAIL_DRY_RUN`, log instead of sending.
    - Runs the blocking `smtplib` in a thread pool.
    - Never raises an exception: failures are logged and swallowed.
    """
    if settings.EMAIL_DRY_RUN:
        logger.info(
            "email_dry_run",
            to=to,
            subject=subject,
            html_preview=html[:200],
        )
        return

    try:
        await run_in_threadpool(
            _send_email_sync, to, subject, html, from_addr=from_addr
        )
        logger.info("email_sent", to=to, subject=subject)
    except Exception as exc:
        logger.error(
            "email_send_failed",
            to=to,
            subject=subject,
            error=str(exc),
        )



async def send_template_email(
    to: str,
    subject: str,
    template_name: str,
    *,
    from_addr: str | None = None,
    **context: Any,
) -> None:
    """Send a templated email asynchronously."""
    html = render_template(template_name, **context)
    await send_email(to, subject, html, from_addr=from_addr)
