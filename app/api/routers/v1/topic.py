from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import TopicNameAlreadyExistsError
from app.schemas.topic import (
    TopicCreateSchema,
    TopicListSchema,
    TopicUpdateSchema,
    TopicWithNotesSchema
)
from app.services import topic as topic_service
from app.database import get_session
from app.core.security import (
    get_current_active_api_client,
    get_current_user,
)
from app.models import APIClient, User

router = APIRouter(prefix="/Topics", tags=["topics"])


@router.post(
    "/",
    response_model=TopicCreateSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_topic(
        payload: TopicCreateSchema,
        db: Annotated[AsyncSession, Depends(get_session)],
        _client: Annotated[APIClient, Depends(get_current_active_api_client)],
        user: User = Depends(get_current_user),
):
    """Create a new topic for the authenticated user."""
    try:
        topic = await topic_service.create_topic(db, user_id=user.id, payload=payload)
    except TopicNameAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    await db.commit()
    return topic


@router.get("/",
            response_model=TopicListSchema,
            status_code=status.HTTP_200_OK)
async def get_topics(
        db: Annotated[AsyncSession, Depends(get_session)],
        _client: Annotated[APIClient, Depends(get_current_active_api_client)],
        user: User = Depends(get_current_user),
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(20, ge=1, description="Items per page"),
):
    """Get all items for the authenticated user."""
    topics = await topic_service.get_topics(db, user_id=user.id, page=page, page_size=page_size)
    return TopicListSchema.model_validate(topics)


@router.patch("/{topic_id}",
              response_model=TopicUpdateSchema,
              status_code=status.HTTP_200_OK)
async def update_topic(
        db: Annotated[AsyncSession, Depends(get_session)],
        topic_id: int,
        payload: TopicUpdateSchema,
        _client: Annotated[APIClient, Depends(get_current_active_api_client)],
        user: User = Depends(get_current_user),
):
    """Update a topic for the authenticated user."""
    response = await topic_service.update_topic(db, user_id=user.id, payload=payload, topic_id=topic_id)
    await db.commit()
    return TopicUpdateSchema.model_validate(response)


@router.delete(
    "/",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_topic(
    db: Annotated[AsyncSession, Depends(get_session)],
    topic_id: int,
    _client: Annotated[APIClient, Depends(get_current_active_api_client)],
    user: User = Depends(get_current_user),
):
    """Delete a topic for the authenticated user."""
    deleted = await topic_service.delete_topic(
        db, topic_id=topic_id, user_id=user.id
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found or not owned by the user.",
        )
    await db.commit()


@router.get("/{topic_id}",
            response_model=TopicWithNotesSchema,
            status_code=status.HTTP_200_OK)
async def get_topic(
        topic_id: int,
        db: Annotated[AsyncSession, Depends(get_session)],
        _client: Annotated[APIClient, Depends(get_current_active_api_client)],
        user: User = Depends(get_current_user),
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(20, ge=1, description="Items per page"),
):
    """Get a specific topic for the authenticated user."""

    response = await topic_service.get_topic_with_notes(db, user_id=user.id,
                                             topic_id=topic_id,
                                             page=page,
                                             page_size=page_size)
    return TopicWithNotesSchema.model_validate(response)