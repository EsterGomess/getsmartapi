"""Note schemas."""
from datetime import datetime
from typing import Annotated

from pydantic import Field

from app.models.note import NoteType
from app.schemas.base import BaseSchema


class NoteReadSchema(BaseSchema):
    id: int
    title: Annotated[str, Field(examples=["My Note"])]
    content: Annotated[str, Field(examples=["Lorem ipsum..."])]
    source: Annotated[str | None, Field(examples=["https://..."])] = None
    note_type: Annotated[NoteType, Field(examples=["PERMANENT"])]
    user_id: int
    created_at: datetime
    updated_at: datetime
    topic_id: int | None = Field(None, examples=[1])


class NotesPageSchema(BaseSchema):
    """Schema for paginated notes."""
    items: list[NoteReadSchema]
    total: int
    page: int
    page_size: int
    pages: int


class NoteLinkReadSchema(BaseSchema):
    """Schema for reading a note link."""
    id: int
    source_note_id: int
    target_note_id: int


class NoteReadDetailedSchema(BaseSchema):
    """Schema for reading a note with its links."""
    id: int
    title: Annotated[str, Field(examples=["My Note"])]
    content: Annotated[str, Field(examples=["This is the content of my note."])]
    source: Annotated[str | None, Field(examples=["https://example.com"])] = None
    note_type: Annotated[NoteType, Field(examples=[NoteType.PERMANENT])]
    user_id: Annotated[int, Field(examples=[1])]
    created_at: datetime
    updated_at: datetime
    outgoing_links: list[NoteLinkReadSchema] = []
    incoming_links: list[NoteLinkReadSchema] = []
    topic_id: int | None = Field(None, examples=[1])


class NoteCreateSchema(BaseSchema):
    """Payload for creating a note."""
    title: str = Field(..., min_length=1, max_length=255, examples=["My Note"])
    content: str = Field(..., min_length=1, examples=["This is the content of my note."])
    source: str | None = Field(None, max_length=255, examples=["https://example.com"])
    note_type: NoteType = NoteType.PERMANENT
    topic_id: int | None = Field(None, examples=[1])


class NoteUpdateSchema(BaseSchema):
    """Payload for updating a note. All fields are optional."""
    title: str | None = Field(None, min_length=1, max_length=255, examples=["Updated Note Title"])
    content: str | None = Field(None, min_length=1, examples=["This is the updated content of my note."])
    source: str | None = Field(None, max_length=255, examples=["https://updated-example.com"])
    topic_id: int | None = Field(None, examples=[1])
    note_type: NoteType | None = None


class GraphNodeSchema(BaseSchema):
    id: int
    title: str
    note_type: NoteType
    link_count: int


class GraphEdgeSchema(BaseSchema):
    id: int
    source: int
    target: int


class NoteGraphSchema(BaseSchema):
    nodes: list[GraphNodeSchema]
    edges: list[GraphEdgeSchema]