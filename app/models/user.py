"""
User model for the FastAPI application.
This module defines the data model for a user.
"""
from sqlalchemy import Integer, Column
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
    notes = relationship('Note',
                         back_populates='user',
                         cascade='all, delete-orphan')
    topics: Mapped[list['Topic']] = relationship('Topic', back_populates='user')

    def __repr__(self) -> str:
        return f"<Username={self.username}>"
