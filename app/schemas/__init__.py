""" Schema package initialization file."""
from app.schemas.auth import Token, TokenData, UserTokenSchema

from app.schemas.user import (
    UserCreateSchema,
    UserResponseCreateSchema,
    UserPasswordResetResponseSchema,
    UserLoginSchema,
    UserLoginResponseSchema,
    UpdateEmailRequestSchema,
    UserReadSchema,
    CustomerOut,
    ForgotUserPasswordRequestSchema,
    ResetUserPasswordRequestSchema,
    MessageResponseSchema
)
from app.schemas.note import (
    NoteReadSchema,
    NotesPageSchema,
    NoteLinkReadSchema,
    NoteReadDetailedSchema,
    NoteCreateSchema,
    NoteUpdateSchema,
    GraphEdgeSchema,
    NoteGraphSchema,
    GraphNodeSchema
)
from app.schemas.notes_ai import (
    SuggestConnectionsRequest,
    ConnectionSuggestion,
    SuggestionsSchema
)

from app.schemas.topic import (
    TopicReadSchema,
    TopicCreateSchema,
    TopicUpdateSchema,
    TopicListSchema,
    TopicDeleteSchema,
    TopicDeleteResponseSchema
)
from app.schemas.pagination import (
    PaginationMeta,
    PaginatedResponse
)
__all__ = [
    "Token",
    "TokenData",
    "UserTokenSchema",
    "ForgotUserPasswordRequestSchema",
    "ResetUserPasswordRequestSchema",
    "UserCreateSchema",
    "UserResponseCreateSchema",
    "UserPasswordResetResponseSchema",
    "UserLoginSchema",
    "UserLoginResponseSchema",
    "NoteReadSchema",
    "NotesPageSchema",
    "NoteLinkReadSchema",
    "NoteReadDetailedSchema",
    "NoteCreateSchema",
    "NoteUpdateSchema",
    "GraphEdgeSchema",
    "GraphNodeSchema",
    "NoteGraphSchema",
    "SuggestConnectionsRequest",
    "ConnectionSuggestion",
    "SuggestionsSchema",
    "MessageResponseSchema",
    "UserReadSchema",
    "UpdateEmailRequestSchema",
    "SuggestionsSchema",
    "TopicReadSchema",
    "TopicCreateSchema",
    "TopicUpdateSchema",
    "TopicListSchema",
    "TopicDeleteSchema",
    "TopicDeleteResponseSchema",
    "PaginationMeta",
    "PaginatedResponse"
]

