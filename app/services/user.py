"""
Authentication service for the FastAPI application.
This module contains functions for user authentication.
"""
from fastapi import HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
import structlog
from starlette import status

from app.models import User
from app.schemas import (
    UserCreateSchema,
    UserLoginSchema,
    UpdateEmailRequestSchema,
    UserReadSchema,
    MessageResponseSchema,
    ResetUserPasswordRequestSchema,
)
from app.core.security import get_password_hash, verify_password
from app.crud.user import (
    create_user,
    get_user_by_email,
    get_user_by_username,
)
from app.crud import (
    create_reset_token,
    get_valid_token,
    mark_token_used,
)
from app.services.emails import (
    send_email_changed_notification,
    send_password_reset_email,
)

logger = structlog.get_logger()


async def login_user(db: AsyncSession, payload: UserLoginSchema) -> User | None:
    """..."""
    user = await get_user_by_username(db, payload.username)

    if user is None:
        return None

    if not verify_password(payload.password.get_secret_value(), user.hashed_password):
        return None
    return user


async def register_user(db: AsyncSession,
                        payload: UserCreateSchema) -> User | bool:
    """..."""
    user = await get_user_by_username(db, payload.username)

    if user:
        return False

    email = str(payload.email)
    user = await get_user_by_email(db, email)
    if user:
        return False

    hashed_password = get_password_hash(
        payload.password.get_secret_value()
    )
    user = await create_user(
        db=db,
        username=payload.username,
        email=email,
        hashed_password=hashed_password,
    )
    logger.info("User registered successfully", user_id=user.id)
    return user


async def change_user_email(
        db: AsyncSession,
        user_id: int,
        payload: UpdateEmailRequestSchema,
        background: BackgroundTasks,
) -> UserReadSchema:
    """..."""
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    old_email = user.email
    new_email = str(payload.new_email).strip().lower()

    if old_email and old_email.lower() == new_email:
        return UserReadSchema.model_validate(user)

    existing = await get_user_by_email(db, new_email)
    if existing is not None and existing.id != user.id:
        logger.info("email_change_conflict", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already in use",
        )

    user.set_email(new_email)
    await db.commit()
    await db.refresh(user)

    # Notifica o endereço ANTIGO (fire-and-forget).
    if old_email and old_email.lower() != new_email:
        background.add_task(
            send_email_changed_notification,
            old_email,   # to
            old_email,   # old_email
            new_email,   # new_email
        )

    logger.info("email_changed", user_id=user.id)
    return UserReadSchema.model_validate(user)


async def request_password_reset(
        db: AsyncSession,
        email: str,
        background: BackgroundTasks,
) -> MessageResponseSchema:
    """..."""
    user = await get_user_by_email(db, email)

    if user is not None:
        raw_token = await create_reset_token(db, user.id)
        await db.commit()

        background.add_task(
            send_password_reset_email,
            str(user.email),
            raw_token,
        )

        logger.info("password_reset_requested", user_id=user.id)
    else:
        logger.info("password_reset_requested_unknown_email")

    return MessageResponseSchema(
        detail="If the email is registered, you will receive a reset link."
    )


async def reset_user_password(
        db: AsyncSession,
        payload: ResetUserPasswordRequestSchema,
) -> MessageResponseSchema:
    """..."""
    token = payload.token
    row = await get_valid_token(db, token)
    if row is None:
        logger.warning("password_reset_invalid_token")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token",
        )

    user = await db.get(User, row.user_id)
    if user is None:
        logger.warning("password_reset_user_missing", user_id=row.user_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token",
        )

    hashed_password = get_password_hash(
        payload.new_password.get_secret_value()
    )
    user.hashed_password = hashed_password

    await mark_token_used(db, row)
    await db.commit()

    logger.info("password_reset_completed", user_id=user.id)
    return MessageResponseSchema(detail="Password reset successfully.")
