from sqlalchemy import Column, Date, Integer
from database.models import Base

class Score(Base):
    __tablename__ = 'score'
    id = Column(Integer, primary_key = True, autoincrement = True)
    date = Column(Date)
    user_id = Column(Integer)
    score = Column(Integer)