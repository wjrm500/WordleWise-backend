from typing import List

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Mapped, relationship

from database.models.base import Base

class User(Base):
    __tablename__ = 'user'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    forename = Column(String(50))
    password_hash = Column(String(255), nullable=False)
    admin = Column(Integer, nullable=False, default=0)  # Site-wide admin
    
    # Relationships
    scores: Mapped[List['Score']] = relationship('Score', back_populates='user')
    group_memberships: Mapped[List['GroupMember']] = relationship('GroupMember', back_populates='user')