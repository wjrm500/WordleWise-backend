from typing import TYPE_CHECKING, List

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Mapped, relationship

from database.models import Base

if TYPE_CHECKING:
    from database.models.Score import Score
    from database.models.GroupMember import GroupMember


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, unique=True)
    forename = Column(String(50))
    password_hash = Column(String(255), nullable=False)
    admin = Column(Integer, nullable=False, default=0)  # Site-wide admin flag

    # Relationships
    scores: Mapped[List['Score']] = relationship('Score', back_populates='user')
    group_memberships: Mapped[List['GroupMember']] = relationship('GroupMember', back_populates='user')
