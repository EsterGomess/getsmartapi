"""
User model for the FastAPI application.
This module defines the data model for a user.
"""
from sqlalchemy import Integer, Column, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.authenticatedentity import AuthenticatedEntity


class User(AuthenticatedEntity):
    """
    User model class that represents a user in the database.
    Inherits from the AuthenticatedEntity class which provides common attributes and methods for all authenticated entities.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)

    username: Mapped[str] = mapped_column(unique=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(254), nullable=True) # TODO:Making email non-nullable if required for your application logic.
    notes = relationship('Note',
                         back_populates='user',
                         cascade='all, delete-orphan')
    password_reset_tokens = relationship(
        "PasswordResetToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def set_email(self, email: str) -> None:
        """Normalize and set the user's email address."""
        self.email = email.strip().lower()

    def __repr__(self) -> str:
        return f"<Username={self.username}>"
