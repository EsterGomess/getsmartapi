""" This module defines the Note and NoteLink models for the application."""
from datetime import datetime
from enum import Enum as PyEnum
import sqlalchemy as sa

from sqlalchemy import (
    Column,
    String,
    ForeignKey,
    DateTime,
    func,
    Enum as SAEnum,
    UniqueConstraint, CheckConstraint, Index)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.models import Base, User


class NoteType(str, PyEnum):
    """An enumeration of note types.
    FLEETING: A note that is temporary and may be deleted after a certain period of time.
    LITERATURE: A note that is related to literature or academic work.
    PERMANENT: A note that is permanent and will not be deleted.
    """
    FLEETING = "FLEETING"
    LITERATURE = "LITERATURE"
    PERMANENT = "PERMANENT"


note_type = Column(
    SAEnum(NoteType, name="note_type_enum", native_enum=True),
    nullable=False,
    default=NoteType.FLEETING,
)


class Note(Base):
    """A note created by a user."""
    __tablename__ = 'notes'
    __table_args__ = (
        Index('ix_notes_topic_created', 'topic_id', sa.desc('created_at'), sa.desc('id')),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str]
    source: Mapped[str | None] = mapped_column(String(255))
    note_type: Mapped[NoteType] = mapped_column(
        SAEnum(NoteType, name="note_type_enum"),
        default=NoteType.FLEETING,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'),
        index=True)
    user: Mapped['User'] = relationship(back_populates='notes',
                                        lazy='selectin')

    outgoing_links: Mapped[list['NoteLink']] = relationship(
        'NoteLink',
        foreign_keys='NoteLink.source_note_id',
        back_populates='source_note',
        cascade='all, delete-orphan',
        passive_deletes=True,
    )
    incoming_links: Mapped[list['NoteLink']] = relationship(
        'NoteLink',
        foreign_keys='NoteLink.target_note_id',
        back_populates='target_note',
        cascade='all, delete-orphan',
        passive_deletes=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now())

    topic_id: Mapped[int | None] = mapped_column(
        ForeignKey('topics.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
    )
    topic: Mapped['Topic | None'] = relationship('Topic', back_populates='notes')

    def __repr__(self) -> str:
        return f"<Note id={self.id} title={self.title}>"


class NoteLink(Base):
    """A link between two notes."""
    __tablename__ = 'note_links'
    __table_args__ = (
        UniqueConstraint('source_note_id', 'target_note_id', name='uq_note_link_pair'),
        CheckConstraint('source_note_id != target_note_id', name='ck_note_link_no_self'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source_note_id: Mapped[int] = mapped_column(
        ForeignKey('notes.id', ondelete='CASCADE'), index=True
    )
    target_note_id: Mapped[int] = mapped_column(
        ForeignKey('notes.id', ondelete='CASCADE'), index=True
    )

    source_note: Mapped['Note'] = relationship(
        'Note',
        foreign_keys=[source_note_id],
        back_populates='outgoing_links',
        lazy='joined',
    )
    target_note: Mapped['Note'] = relationship(
        'Note',
        foreign_keys=[target_note_id],
        back_populates='incoming_links',
        lazy='joined',
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now())

    def __repr__(self) -> str:
        return (
            f"<NoteLink id={self.id} "
            f"source={self.source_note_id} target={self.target_note_id}>"
        )

    def get_target_note(self):
        """Returns the target note of the link."""
        return self.target_note

    def get_source_note(self):
        """Returns the source note of the link."""
        return self.source_note
