"""This module contains the endpoints for the notes."""
from typing import Annotated
from fastapi import Response

from fastapi import APIRouter, status, Depends, Query
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    get_current_active_api_client,
    get_current_user,
)
from app.models import APIClient, User

from app.database import get_session
from app.services import (
    list_notes_by_user,
    get_note_for_user,
    create_note_for_user,
    update_note_for_user,
    delete_note_for_user,
    get_note_graph,
    suggest_connections
)
from app.schemas import (
    NotesPageSchema,
    NoteReadDetailedSchema,
    NoteCreateSchema,
    NoteReadSchema,
    NoteUpdateSchema,
    NoteGraphSchema,
    SuggestConnectionsRequest,
    SuggestionsSchema
)

logger = structlog.get_logger()
router = APIRouter(prefix="/notes", tags=["Notes"])


@router.post(
    "/create",
    status_code=status.HTTP_201_CREATED,
    response_model=NoteReadSchema,
    summary="Create a new note",
)
async def create_note(
        payload: NoteCreateSchema,
        db: Annotated[AsyncSession, Depends(get_session)],
        _client: Annotated[APIClient, Depends(get_current_active_api_client)],
        user: Annotated[User, Depends(get_current_user)],
) -> NoteReadSchema:
    """Create a new note for the current user."""
    note = await create_note_for_user(
        db=db,
        user_id=user.id,
        payload=payload,
    )
    await db.commit()
    await db.refresh(note)

    logger.info("note_created", user_id=user.id, note_id=note.id)
    return NoteReadSchema.model_validate(note)


@router.get(
    "/list",
    status_code=status.HTTP_200_OK,
    response_model=NotesPageSchema,
    summary="List notes for the current user",
)
async def list_notes(
        db: Annotated[AsyncSession, Depends(get_session)],
        _client: Annotated[APIClient, Depends(get_current_active_api_client)],
        user: Annotated[User, Depends(get_current_user)],
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(20, ge=1, description="Items per page"),
) -> NotesPageSchema:
    """List all notes for the current user, paginated."""
    return await list_notes_by_user(
        db=db,
        user_id=user.id,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/note/{note_id}",
    status_code=status.HTTP_200_OK,
    response_model=NoteReadDetailedSchema,
    summary="Get note details by ID",
    responses={404: {"description": "Note not found"}},
)
async def get_note_detail(
        note_id: int,
        db: Annotated[AsyncSession, Depends(get_session)],
        _client: Annotated[APIClient, Depends(get_current_active_api_client)],
        user: Annotated[User, Depends(get_current_user)],
) -> NoteReadDetailedSchema:
    """Get the details of a note by its ID (scoped to the current user)."""
    note = await get_note_for_user(
        db=db,
        user_id=user.id,
        note_id=note_id,
    )
    return NoteReadDetailedSchema.model_validate(note)


@router.delete(
    "/note/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a note by ID",
    responses={404: {"description": "Note not found"}},
)
async def delete_note(
        note_id: int,
        db: Annotated[AsyncSession, Depends(get_session)],
        _client: Annotated[APIClient, Depends(get_current_active_api_client)],
        user: Annotated[User, Depends(get_current_user)],
) -> Response:
    """Delete a note by its ID (scoped to the current user)."""
    await delete_note_for_user(
        db=db,
        user_id=user.id,
        note_id=note_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/note/{note_id}",
    status_code=status.HTTP_200_OK,
    response_model=NoteReadSchema,
    summary="Update a note by ID",
    responses={404: {"description": "Note not found"}},
)
async def update_note(
        note_id: int,
        payload: NoteUpdateSchema,
        db: Annotated[AsyncSession, Depends(get_session)],
        _client: Annotated[APIClient, Depends(get_current_active_api_client)],
        user: Annotated[User, Depends(get_current_user)],
) -> NoteReadSchema:
    """Update a note by its ID (scoped to the current user)."""
    note = await update_note_for_user(
        db=db,
        user_id=user.id,
        note_id=note_id,
        payload=payload,
    )
    await db.commit()
    return NoteReadSchema.model_validate(note)


@router.get(
    "/graph",
    status_code=status.HTTP_200_OK,
    response_model=NoteGraphSchema,
    summary="Get the full note graph for the current user",
)
async def get_graph(
        db: Annotated[AsyncSession, Depends(get_session)],
        _client: Annotated[APIClient, Depends(get_current_active_api_client)],
        user: Annotated[User, Depends(get_current_user)],
) -> NoteGraphSchema:
    return await get_note_graph(db=db, user_id=user.id)


@router.post(
    "/suggest-connections",
    status_code=status.HTTP_200_OK,
    response_model=SuggestionsSchema,
)
async def suggest_connections_endpoint(
        payload: SuggestConnectionsRequest,
        db: Annotated[AsyncSession, Depends(get_session)],
        _client: Annotated[APIClient, Depends(get_current_active_api_client)],
        user: Annotated[User, Depends(get_current_user)],
) -> SuggestionsSchema:
    """Suggest connections based on the provided title and content."""
    return await suggest_connections(
        db=db,
        user_id=user.id,
        title=payload.title,
        content=payload.content
    )
