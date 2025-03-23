from typing import List

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Mapped, relationship

from database.models import Base

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String)
    forename = Column(String)
    password_hash = Column(String)
    admin = Column(Integer)
    
    # Relationship to Score
    scores: Mapped[List['Score']] = relationship('Score', back_populates='user')