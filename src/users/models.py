from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from core.common_fields import AtivableAndTimeStamp
from core.database import Base


class User(AtivableAndTimeStamp, Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(12), unique=True, nullable=False)
    password = Column(String(255), nullable=False)

    publications = relationship(
        "Publication",
        back_populates="author",
        cascade="all, delete-orphan",
    )


class UserPreference(Base):
    __tablename__ = "user_preferences"

    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    preferences = Column(JSONB, nullable=False, default=list)
