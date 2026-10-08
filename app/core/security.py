"""Security utilities for the API."""

from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.crud.user import get_user_by_id
from app.crud.api_client import get_api_client_by_username

from app.database import get_session
from app.models import APIClient, User
from app.schemas import TokenData


password_hash = PasswordHash.recommended()

oauth2_scheme_client = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/token",
    scheme_name="APIClientAuth",
)

user_token_scheme = APIKeyHeader(name="X-User-Token", auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return password_hash.hash(password)


# ---------------------------------------------------------------------------
# Token creation
# ---------------------------------------------------------------------------

def create_access_token(data: dict, token_type: str = "api_client") -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expiration_minutes = (
        settings.API_CLIENT_ACCESS_TOKEN_EXPIRE_MINUTES
        if token_type == "api_client"
        else settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expiration_minutes
    )
    to_encode.update({"exp": expire, "type": token_type})
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def create_user_access_token(user_id: int) -> str:
    """Create a JWT access token for a human User."""
    return create_access_token(data={"sub": str(user_id)}, token_type="user")


# ---------------------------------------------------------------------------
# APIClient authentication (camada 1)
# ---------------------------------------------------------------------------

async def get_current_api_client(
    token: Annotated[str, Depends(oauth2_scheme_client)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> APIClient:
    """Get the current API client based on the provided JWT token."""

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        if payload.get("type") != "api_client":
            raise credentials_exception

        username = payload.get("sub")
        if username is None:
            raise credentials_exception

        token_data = TokenData(username=username)

    except InvalidTokenError  as exc:
        raise credentials_exception from exc

    api_client = await get_api_client_by_username(
        db=db,
        username=token_data.username,
    )
    if api_client is None:
        raise credentials_exception

    return api_client


async def get_current_active_api_client(
    current_api_client: Annotated[
        APIClient,
        Depends(get_current_api_client),
    ],
) -> APIClient:
    """Get the current active API client."""
    if not current_api_client.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive API client",
        )
    return current_api_client


# ---------------------------------------------------------------------------
# User authentication (camada 2)
# ---------------------------------------------------------------------------

async def get_current_user(
    token: Annotated[str | None, Depends(user_token_scheme)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    """Get the current human User based on the X-User-Token header."""

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate user credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if token is None:
        raise credentials_exception

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        if payload.get("type") != "user":
            raise credentials_exception

        user_id_raw = payload.get("sub")
        if user_id_raw is None:
            raise credentials_exception

        user_id = int(user_id_raw)

    except (InvalidTokenError, ValueError) as exc:
        raise credentials_exception from exc

    user = await get_user_by_id(db=db, user_id=user_id)
    if user is None:
        raise credentials_exception
    return user
