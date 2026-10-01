"""
API routes for authentication.
This module contains the API routes for handling user authentication.
"""
from fastapi import (
    APIRouter,
    status,
    Depends,
    HTTPException,
    BackgroundTasks
)
import structlog
from typing import Annotated

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    get_current_active_api_client,
    create_user_access_token,
    get_current_user,
)
from app.models import APIClient, User
from app.schemas import (
    UserCreateSchema,
    UserResponseCreateSchema,
    UserLoginSchema,
    UserLoginResponseSchema,
    ForgotUserPasswordRequestSchema,
    ResetUserPasswordRequestSchema,
    MessageResponseSchema,
    UpdateEmailRequestSchema,
    UserReadSchema
)
from app.database import get_session
from app.services import (
    register_user,
    login_user,
    reset_user_password,
    request_password_reset,
    change_user_email
)

logger = structlog.get_logger()
router = APIRouter(prefix="/customers", tags=["Login and Registration"])


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=UserLoginResponseSchema,
)
async def login(
        payload: UserLoginSchema,
        db: Annotated[AsyncSession, Depends(get_session)],
        _client: Annotated[APIClient, Depends(get_current_active_api_client)],
) -> UserLoginResponseSchema:
    """
    Authenticate the user and return a JWT plus the user data.
    Use the token in the `X-User-Token` header on protected routes.
    """
    user = await login_user(db, payload)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    token = create_user_access_token(user.id)

    logger.info("User logged in", username=user.username)
    return UserLoginResponseSchema(
        access_token=token,
        token_type="bearer",
        username=user.username
    )


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=UserResponseCreateSchema
)
async def register(
        payload: UserCreateSchema,
        db: Annotated[AsyncSession, Depends(get_session)],
        current_api_client: APIClient = Depends(get_current_active_api_client),  # noqa: FBT001
) -> UserResponseCreateSchema:
    """
    Handle user registration.
    :param payload: The registration request payload.
    :param db: The database session.
    :return: The created user.
    """
    created_user = await register_user(db, payload)

    if not created_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists.")

    return UserResponseCreateSchema.model_validate(created_user)


@router.post(
    "/forgot-password",
    status_code=status.HTTP_200_OK,
    response_model=MessageResponseSchema,
)
async def forgot_password(
        payload: ForgotUserPasswordRequestSchema,
        background: BackgroundTasks,
        db: Annotated[AsyncSession, Depends(get_session)],
        _client: Annotated[APIClient, Depends(get_current_active_api_client)],
) -> MessageResponseSchema:
    return await request_password_reset(
        db=db,
        email=payload.email,
        background=background,
    )


@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    response_model=MessageResponseSchema,
)
async def reset_password_endpoint(
        payload: ResetUserPasswordRequestSchema,
        db: Annotated[AsyncSession, Depends(get_session)],
        _client: Annotated[APIClient, Depends(get_current_active_api_client)],
) -> MessageResponseSchema:
    return await reset_user_password(db=db, payload=payload)


@router.patch(
    "/me/email",
    status_code=status.HTTP_200_OK,
    response_model=UserReadSchema,
    summary="Change the authenticated user's email",
    responses={
        400: {"description": "Invalid password"},
        409: {"description": "Email already in use"},
    },
)
async def update_my_email(
        payload: UpdateEmailRequestSchema,
        background: BackgroundTasks,
        db: Annotated[AsyncSession, Depends(get_session)],
        _client: Annotated[APIClient, Depends(get_current_active_api_client)],
        user: Annotated[User, Depends(get_current_user)],
) -> UserReadSchema:
    return await change_user_email(
        db=db,
        user_id=user.id,
        payload=payload,
        background=background
    )


@router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    response_model=UserReadSchema,
    summary="Get the authenticated user's profile",
)
async def read_my_profile(
        _client: Annotated[APIClient, Depends(get_current_active_api_client)],
        user: Annotated[User, Depends(get_current_user)],
) -> UserReadSchema:
    return UserReadSchema.model_validate(user)
