"""CRUD operations for the Note model."""
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.note import Note, NoteLink
from app.schemas import NoteCreateSchema, NoteUpdateSchema
from app.crud.note_link import sync_links_for_note
from app.core.pagination import paginate


async def get_notes_paginated_by_user(
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        topic_id: int | None = None
) -> tuple[list[Note], int]:
    """Fetch a paginated list of notes for a specific user."""
    stmt = (
        select(Note)
        .where(Note.user_id == user_id)
        .options(selectinload(Note.user))
        .order_by(Note.created_at.desc(), Note.id.desc())
    )

    if topic_id is not None:
        stmt = stmt.where(Note.topic_id == topic_id)

    return await paginate(db, stmt, page=page, page_size=page_size)



async def get_note_by_user_by_id(
        db: AsyncSession,
        note_id: int,
        user_id: int,
) -> Note | None:
    """Fetch a note by its ID and user ID."""
    result = await db.execute(
        select(Note)
        .where(Note.id == note_id, Note.user_id == user_id)
        .options(
            selectinload(Note.user),
            selectinload(Note.outgoing_links),
            selectinload(Note.incoming_links),
        )
    )

    return result.scalar_one_or_none()


async def create_note(
        db: AsyncSession,
        user_id: int,
        payload: NoteCreateSchema,
) -> Note:
    """Create a new note for a specific user."""
    note = Note(
        title=payload.title,
        content=payload.content,
        source=payload.source,
        note_type=payload.note_type,
        user_id=user_id,
        topic_id=payload.topic_id
    )

    db.add(note)
    await db.flush()  # generates note.id via RETURNING
    await sync_links_for_note(db, note)  # note.user_id used internally
    return note


async def update_note(
        db: AsyncSession,
        user_id: int,
        note_id: int,
        payload: NoteUpdateSchema,
) -> Note | None:
    """Update a note. Flushes and re-syncs links. Returns None if not found.

    The caller is responsible for committing the transaction.
    """
    result = await db.execute(
        select(Note).where(Note.id == note_id, Note.user_id == user_id)
    )
    note = result.scalar_one_or_none()
    if note is None:
        return None

    if payload.topic_id is not None:
        from app.crud.topic import get_topic_by_user_and_id
        topic = await get_topic_by_user_and_id(db, topic_id=payload.topic_id, user_id=user_id)
        if topic is None:
            raise ValueError(f"Topic {payload.topic_id} not found for this user")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(note, field, value)

    await db.flush()  # emits UPDATE, keeps transaction open
    await sync_links_for_note(db, note)  # rebuilds note_links from content
    await db.refresh(note)
    return note


async def delete_note(
        db: AsyncSession,
        user_id: int,
        note_id: int,
) -> Note | None:
    """Delete a note. Returns None if not found.

    The caller is responsible for committing the transaction.
    """
    result = await db.execute(
        select(Note).where(Note.id == note_id, Note.user_id == user_id)
    )
    note = result.scalar_one_or_none()
    if note is None:
        return None
    await db.delete(note)
    await db.flush()  # emits DELETE, keeps transaction open
    return note


async def get_graph_for_user(
        db: AsyncSession,
        user_id: int,
) -> tuple[list[Note], list[NoteLink]]:
    """Return all notes and all links for a user, for graph rendering."""
    notes_result = await db.execute(
        select(Note).where(Note.user_id == user_id).order_by(Note.id)
    )
    notes = list(notes_result.scalars().all())

    if not notes:
        return [], []

    note_ids = [n.id for n in notes]

    links_result = await db.execute(
        select(NoteLink).where(
            NoteLink.source_note_id.in_(note_ids),
            NoteLink.target_note_id.in_(note_ids),
        )
    )
    links = list(links_result.scalars().all())
    return notes, links


async def get_candidate_notes(
        db: AsyncSession,
        user_id: int,
        exclude_note_id: int | None = None,
        limit: int = 40,
) -> list[Note]:
    """
    Fetch the most recent notes for a user, optionally excluding one.

    Used to build the candidate list for AI connection suggestions.
    Returns the notes ordered by creation date (newest first).
    """
    stmt = (
        select(Note)
        .where(Note.user_id == user_id)
        .order_by(Note.created_at.desc())
        .limit(limit)
    )

    if exclude_note_id is not None:
        stmt = stmt.where(Note.id != exclude_note_id)

    result = await db.execute(stmt)
    return list(result.scalars().all())
