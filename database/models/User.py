from typing import List

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, relationship

from database.models.base import Base

class User(Base):
    __tablename__ = 'user'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    forename = Column(String(50))
    password_hash = Column(String(255), nullable=False)
    default_group_id = Column(Integer, ForeignKey('group.id', ondelete='SET NULL'), nullable=True)
    
    # Relationships
    scores: Mapped[List['Score']] = relationship('Score', back_populates='user')
    group_memberships: Mapped[List['GroupMember']] = relationship('GroupMember', back_populates='user')
    default_group: Mapped['Group'] = relationship('Group', foreign_keys=[default_group_id])
    