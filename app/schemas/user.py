"""Schema for user information."""
from datetime import datetime

from typing import Annotated, Self
from pydantic import EmailStr, Field, SecretStr, model_validator

from app.core.password import validate_password_complexity
from app.schemas.base import BaseSchema


class UserCreateSchema(BaseSchema):
    """Schema for user information."""
    username: Annotated[str, Field(examples=["cool_username"])]
    email: Annotated[EmailStr, Field(examples=["email@example.com"])]
    password: Annotated[SecretStr, Field(
        min_length=8,
        max_length=128,
        description="Plan password for the user."
                    "Must be at least 8 characters long "
                    "and contain at least one uppercase letter, "
                    "one lowercase letter, one digit, and one special character.",
        examples=["Mypassword123!"],
    )]

    @model_validator(mode="after")
    def validate_password_complexity(self) -> "UserCreateSchema":
        """Validate the documented password complexity policy."""
        password = self.password.get_secret_value()
        validate_password_complexity(password)
        return self


class UserResponseCreateSchema(BaseSchema):
    """Schema for user information."""
    username: Annotated[str, Field(examples=["cool_username"])]
    email: Annotated[EmailStr, Field(examples=["ester@example.com"])]


class UserPasswordResetResponseSchema(BaseSchema):
    """Safe response returned after a password reset."""
    username: Annotated[str, Field(examples=["cool_username"])]
    email: Annotated[EmailStr, Field(examples=["ester@example.com"])]


class UserLoginSchema(BaseSchema):
    """Schema for user login information."""
    username: Annotated[str, Field(examples=["cool_username"])]
    password: Annotated[SecretStr, Field(examples=["Mypassword123!"])]


class UserLoginResponseSchema(BaseSchema):
    """Schema for user login response."""
    username: Annotated[str, Field(examples=["cool_username"])]
    access_token: Annotated[str, Field(examples=["seu_token_de_acesso"])]
    token_type: Annotated[str, Field(examples=["bearer"])] = "bearer"


class UpdateEmailRequestSchema(BaseSchema):
    """Payload for changing the authenticated user's email."""

    new_email: Annotated[EmailStr, Field(examples=["new@example.com"])]

class UserReadSchema(BaseSchema):
    """Public representation of a user. No secrets, no tokens."""

    id: int
    username: str
    email: EmailStr | None = None
    is_active: bool
    created_at: datetime

class CustomerOut(BaseSchema):
    id: int
    username: str
    email: EmailStr



class ForgotUserPasswordRequestSchema(BaseSchema):
    """Payload used to request a password recovery email."""
    email: Annotated[EmailStr, Field(examples=["email@example.com"])]


class ResetUserPasswordRequestSchema(BaseSchema):
    """Payload used to set a new password with a recovery token."""
    token: Annotated[str, Field(min_length=1, examples=["recovery-token"])]
    new_password: Annotated[
        SecretStr,
        Field(
            min_length=8,
            max_length=128,
            description=(
                "Must contain uppercase and lowercase letters, a digit, "
                "and a special character."
            ),
            examples=["Mypassword123!"],
        ),
    ]
    confirm_password: Annotated[
        SecretStr,
        Field(examples=["Mypassword123!"]),
    ]

    @model_validator(mode="after")
    def validate_passwords(self) -> Self:
        """Validate password complexity and confirmation."""
        password = self.new_password.get_secret_value()
        confirmation = self.confirm_password.get_secret_value()

        validate_password_complexity(password)
        if password != confirmation:
            raise ValueError("Password confirmation does not match.")
        return self

class MessageResponseSchema(BaseSchema):
    """Generic message response (no user data leaked)."""

    detail: str
