from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from core.common_fields import AtivableAndTimeStamp
from core.database import Base


class Publication(AtivableAndTimeStamp, Base):
    __tablename__ = "publications"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    document = Column(JSONB, nullable=False)
    presentation = Column(JSONB, nullable=False)
    thumbnail_url = Column(String(500), nullable=True)
    is_published = Column(Boolean, default=False, nullable=False)
    like = Column(Integer, default=0)
    dislike = Column(Integer, default=0)
    author = relationship("User", back_populates="publications")


class PublicationTag(Base):
    __tablename__ = "publication_tags"

    publication_id = Column(
        Integer,
        ForeignKey("publications.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag = Column(String(80), primary_key=True)


class PublicationReadHistory(Base):
    __tablename__ = "publication_read_history"

    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    publication_id = Column(
        Integer,
        ForeignKey("publications.id", ondelete="CASCADE"),
        primary_key=True,
    )
    last_viewed_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    read_count = Column(Integer, nullable=False, default=1, server_default="1")


class PublicationReaction(Base):
    __tablename__ = "publication_reactions"
    __table_args__ = (
        CheckConstraint("reaction IN ('like', 'dislike')", name="ck_publication_reaction"),
    )

    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    publication_id = Column(
        Integer,
        ForeignKey("publications.id", ondelete="CASCADE"),
        primary_key=True,
    )
    reaction = Column(String(7), nullable=False)
