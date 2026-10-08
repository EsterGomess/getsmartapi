"""CRUD operations for the Topic model."""
from sqlalchemy import func, select, exists
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete

from app.crud.note import get_note_by_user_by_id
from app.models import Topic


async def get_topics_paginated_by_user(
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
) -> tuple[list[Topic], int]:
    """Fetch a paginated list of items for a specific user."""
    skip = (page - 1) * page_size

    total_result = await db.execute(
        select(func.count()).select_from(Topic).where(Topic.user_id == user_id)
    )
    total = total_result.scalar_one()

    result = await db.execute(
        select(Topic)
        .where(Topic.user_id == user_id)
        .order_by(Topic.created_at.desc())
        .offset(skip)
        .limit(page_size)
    )
    topics = list(result.scalars().all())
    return topics, total


async def create_topic(
        db: AsyncSession,
        user_id: int,
        payload: dict,
) -> Topic:
    """Create a new topic for a specific user."""
    topic = Topic(
        title=payload.title,
        description=payload.description,
        user_id=user_id
    )
    db.add(topic)
    await db.flush()
    await db.refresh(topic)
    return topic


async def delete_topic(
        db: AsyncSession,
        topic_id: int,
        user_id: int,
) -> bool:
    """Delete a topic by ID, scoped to a user. Returns True if deleted."""
    result = await db.execute(
        delete(Topic)
        .where(Topic.id == topic_id, Topic.user_id == user_id)
        .returning(Topic.id)
    )
    deleted_id = result.scalar_one_or_none()
    return deleted_id is not None


async def update_topic(
        db: AsyncSession,
        topic_id: int,
        user_id: int,
        note_id: int | None = None,
        title: str | None = None,
        description: str | None = None
) -> Topic | None:
    """Update a topic's title and/or description."""
    result = await db.execute(
        select(Topic).where(Topic.id == topic_id, Topic.user_id == user_id)
    )
    topic = result.scalar_one_or_none()
    if topic is None:
        return None

    if title is not None:
        topic.title = title
    if description is not None:
        topic.description = description
    if note_id is not None:
        note_result = await get_note_by_user_by_id(db=db, user_id=user_id, note_id=note_id)
        if note_result is None:
            raise ValueError(f"Note {note_id} not found for this user")
        note_result.topic_id = topic_id

    await db.flush()
    await db.refresh(topic)
    return topic


async def topic_name_exists_for_user(
        db: AsyncSession,
        user_id: int,
        name: str,
) -> bool:
    """Check whether a topic title already exists for the user."""
    result = await db.execute(
        select(
            exists().where(Topic.user_id == user_id, Topic.title == name)
        )
    )
    return result.scalar_one()

async def get_topic_by_user_and_id(
    db: AsyncSession,
    topic_id: int,
    user_id: int,
) -> Topic | None:
    result = await db.execute(
        select(Topic).where(Topic.id == topic_id, Topic.user_id == user_id)
    )
    return result.scalar_one_or_none()
