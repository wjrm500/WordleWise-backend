from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, relationship

from database.models import Base

if TYPE_CHECKING:
    from database.models.User import User
    from database.models.GroupMember import GroupMember


class Group(Base):
    __tablename__ = 'group'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    invite_code = Column(String(8), unique=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by_user_id = Column(Integer, ForeignKey('user.id'))
    include_historical_data = Column(Integer, nullable=False, default=1)

    # Relationships
    created_by: Mapped['User'] = relationship('User', foreign_keys=[created_by_user_id])
    members: Mapped[List['GroupMember']] = relationship(
        'GroupMember',
        back_populates='group',
        cascade='all, delete-orphan'
    )
