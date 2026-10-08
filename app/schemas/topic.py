"""Schemas for topic-related operations."""
from datetime import datetime
from typing import Annotated

from pydantic import Field

from app.schemas.base import BaseSchema
from app.schemas.note import NoteReadSchema
from app.schemas.pagination import PaginationMeta


class TopicWithNotesSchema(BaseSchema):
    """Schema for reading a topic."""
    id: int
    title: Annotated[str, Field(examples=["My Topic"])]
    description: str | None = Field(default=None, examples=["This is a description of my topic."])
    created_at: datetime
    updated_at: datetime
    notes: list[NoteReadSchema] = Field(default_factory=list)
    pagination: PaginationMeta

class TopicCreateSchema(BaseSchema):
    """Payload for creating a topic."""
    title: Annotated[str, Field(min_length=1, max_length=255, examples=["My Topic"])]
    description: str | None = Field(default=None, examples=["This is a description of my topic."])

class TopicUpdateSchema(BaseSchema):
    """Payload for updating a topic."""
    title: Annotated[str | None, Field(min_length=1, max_length=255, examples=["My Topic"])] = None
    description: str | None = Field(default=None, examples=["This is a description of my topic."])
    note_id: int | None = Field(default=None, examples=[1], description="The ID of the note to which this topic belongs.")

class TopicReadSchema(BaseSchema):
    """Schema for listing topics."""
    id: int
    title : Annotated[str, Field(examples=["My Topic"])]
    description: str | None = Field(default=None, examples=["This is a description of my topic."])
    created_at: datetime
    updated_at: datetime | None = Field(default=None, examples=[datetime.now()])

class TopicListSchema(BaseSchema):
    """Schema for listing items."""
    items: list[TopicReadSchema] = Field(default_factory=list)
    total: int
    page: int
    page_size: int
    pages: int

class TopicDeleteSchema(BaseSchema):
    """Payload for deleting a topic."""
    id: int = Field(..., examples=[1], description="The ID of the topic to delete.")

class TopicDeleteResponseSchema(BaseSchema):
    """Response schema for deleting a topic."""
    message: str = Field(..., examples=["Topic deleted successfully."])

