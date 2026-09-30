"""
CRUD operations for the User model.
This module contains functions for performing CRUD operations on the User model.
"""

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from app.models import PasswordResetToken
from app.config import settings
from app.models.user import User


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    """
    Get a user by their username.
    :param db: The database session.
    :param username: The user's username.
    :return: The user if found, otherwise None.
    """
    statement = select(User).where(User.username == username)
    result = await db.execute(statement)
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Get a user by their email address."""
    statement = select(User).where(User.email == email)
    result = await db.execute(statement)
    return result.scalar_one_or_none()


async def create_user(
        db: AsyncSession,
        username: str,
        email: str,
        hashed_password: str,
) -> User:
    """
    Create a new user in the database.
    :param db: The database session.
    :param username: The user's username.
    :param email: The user's unique email address.
    :param hashed_password: The user's hashed password.
    :return: The created user.
    """
    user = User(
        username=username,
        hashed_password=hashed_password,
    )
    user.set_email(email)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_registered_user(db: AsyncSession, username: str, hashed_password: str) -> User | None:
    """
    Get a registered user by their username and hashed password.
    :param db: The database session.
    :param username: The user's username.
    :param hashed_password: The user's hashed password.
    :return: The user if found, otherwise None.
    """
    statement = select(User).where(User.username == username,
                                   User.hashed_password == hashed_password)
    result = await db.execute(statement)
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    """Get a user by their ID.
    :param db: The database session.
    :param user_id: The user's ID.
    :return: The user if found, otherwise None.
    """
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def update_user_password(
        db: AsyncSession,
        user: User,
        hashed_password: str,
) -> User:
    """Persist a user's new hashed password."""
    user.hashed_password = hashed_password
    await db.commit()
    await db.refresh(user)
    return user


async def update_user_email(
        db: AsyncSession,
        user_id: int,
        new_email: str,
) -> User | None:
    """Change the email of a user. Returns None if the user doesn't exist."""
    user = await db.get(User, user_id)
    if user is None:
        return None

    user.email = new_email
    await db.flush()
    return user


def _hash_token(raw: str) -> str:
    """SHA-256 of the raw token. Deterministic, safe to store."""
    return hashlib.sha256(raw.encode()).hexdigest()


async def create_reset_token(db: AsyncSession, user_id: int) -> str:
    """
    Create a new reset token for a user.

    - Invalidates any previous unused tokens (only the latest counts).
    - Returns the RAW token (the caller emails it; we only store the hash).
    """
    # 1. Invalidate previous unused tokens for this user
    await db.execute(
        update(PasswordResetToken)
        .where(
            PasswordResetToken.user_id == user_id,
            PasswordResetToken.used_at.is_(None),
        )
        .values(used_at=datetime.now(timezone.utc))
    )

    # 2. Generate a new random token
    raw = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(
        minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
    )

    token = PasswordResetToken(
        user_id=user_id,
        token_hash=_hash_token(raw),
        expires_at=expires,
    )
    db.add(token)
    await db.flush()
    return raw


async def get_valid_token(db: AsyncSession, raw: str) -> PasswordResetToken | None:
    """Return the token row if valid (not used, not expired), else None."""
    result = await db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == _hash_token(raw)
        )
    )
    token = result.scalar_one_or_none()
    if token is None or token.used_at is not None or token.expires_at < datetime.now(timezone.utc):
        return None

    return token


async def mark_token_used(db: AsyncSession, token: PasswordResetToken) -> None:
    """Mark a token as used. Caller must commit."""
    token.used_at = datetime.now(timezone.utc)
    await db.flush()
