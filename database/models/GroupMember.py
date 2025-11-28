from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, relationship

from database.models.base import Base

class GroupMember(Base):
    __tablename__ = 'group_member'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(Integer, ForeignKey('group.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    role = Column(String(10), nullable=False, default='member')  # 'admin' or 'member'
    joined_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    __table_args__ = (UniqueConstraint('group_id', 'user_id'),)
    
    # Relationships
    group: Mapped['Group'] = relationship('Group', back_populates='members')
    user: Mapped['User'] = relationship('User', back_populates='group_memberships')
