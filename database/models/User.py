from typing import List, Type

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from database.models import Base

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String)
    password_hash = Column(String)
    admin = Column(Integer)
    
    # Relationship to Score
    scores: 'List[Score]' = relationship('Score', back_populates='user')