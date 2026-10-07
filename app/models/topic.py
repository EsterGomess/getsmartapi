
from datetime import datetime
from sqlalchemy import DateTime, func, text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base

class Topic(Base):
    """A topic created by a user."""
    __tablename__ = 'topics'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    description: Mapped[str | None]
    notes: Mapped[list['Note']] = relationship(
        back_populates='topic',
        passive_deletes=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'),
        index=True)
    user: Mapped['User'] = relationship(back_populates='topics',
                                        lazy='selectin')
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
