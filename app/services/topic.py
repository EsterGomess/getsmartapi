from math import ceil

from app.crud.note import get_notes_paginated_by_user
from app.crud.topic import (
    get_topic_by_user_and_id,
    get_topics_paginated_by_user,
    topic_name_exists_for_user
)
from app.crud.topic import create_topic as create_topic_crud
from app.crud.topic import update_topic as update_topic_crud
from app.crud.topic import delete_topic as delete_topic_crud
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import TopicNameAlreadyExistsError
from app.models.topic import Topic
from app.schemas.topic import TopicCreateSchema, TopicUpdateSchema


async def create_topic(
        db: AsyncSession,
        user_id: int,
        payload: TopicCreateSchema,
) -> Topic:
    """Create a topic for a user.

    Raises:
        TopicNameAlreadyExistsError: if the user already has a topic with that title.
    """
    if await topic_name_exists_for_user(db, user_id, payload.title):
        raise TopicNameAlreadyExistsError(
            f"Topic '{payload.title}' already exists."
        )

    topic = await create_topic_crud(db, user_id=user_id, payload=payload)
    return topic


async def get_topics(db: AsyncSession, user_id: int, page: int, page_size: int) -> dict:
    """Get all items for a specific user."""
    topics, total = await get_topics_paginated_by_user(db, user_id=user_id, page=page, page_size=page_size)

    return {
        "items": topics,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": ceil(total / page_size) if total else 0,
    }


async def get_topic_by_id(
        db: AsyncSession,
        topic_id: int,
        user_id: int,
) -> Topic | None:
    """Fetch a single topic."""
    return await get_topic_by_user_and_id(db, topic_id=topic_id, user_id=user_id)


async def get_topic_with_notes(
        db: AsyncSession,
        topic_id: int,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
) -> dict | None:
    """Fetch a topic and its notes paginated."""
    topic = await get_topic_by_id(db, topic_id=topic_id, user_id=user_id)
    if topic is None:
        return None

    notes, total = await get_notes_paginated_by_user(
        db, user_id=user_id, topic_id=topic_id,
        page=page, page_size=page_size,
    )
    return {
        "id": topic.id,
        "title": topic.title,
        "description": topic.description,
        "created_at": topic.created_at,
        "updated_at": topic.updated_at,
        "notes": notes,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": ceil(total / page_size) if total else 0,
        },
    }


async def update_topic(db: AsyncSession,
                       user_id: int,
                       payload: TopicUpdateSchema,
                       topic_id: int):
    """Update a topic for a user."""
    response = await update_topic_crud(
        db,
        user_id=user_id,
        topic_id=topic_id,
        name=payload.title,
        note_id=payload.note_id,
        description=payload.description)
    return response


async def delete_topic(db: AsyncSession, topic_id: int, user_id: int) -> bool:
    """Delete a topic for a user."""
    return await delete_topic_crud(db, topic_id=topic_id, user_id=user_id)
