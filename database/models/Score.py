from sqlalchemy import Column, Date, ForeignKey, Integer
from sqlalchemy.orm import Mapped, relationship

from database.models import Base
from database.models.User import User

class Score(Base):
    __tablename__ = 'score'
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date)
    user_id = Column(Integer, ForeignKey('user.id'))  # Foreign Key
    score = Column(Integer)

    # Relationship to User
    user: Mapped['User'] = relationship('User', back_populates='scores')