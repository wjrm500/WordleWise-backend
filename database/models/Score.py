from sqlalchemy import Column, Date, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, relationship

from database.models.base import Base
from database.models.User import User

class Score(Base):
    __tablename__ = 'score'
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date)
    user_id = Column(Integer, ForeignKey('user.id'))  # Foreign Key
    score = Column(Integer)
    
    __table_args__ = (UniqueConstraint('date', 'user_id', name='uq_score_date_user'),)

    # Relationship to User
    user: Mapped['User'] = relationship('User', back_populates='scores')