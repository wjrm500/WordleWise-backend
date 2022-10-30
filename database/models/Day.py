from sqlalchemy import Column, Date, Integer
from database.models import Base

class Day(Base):
    __tablename__ = 'day'
    id = Column(Integer, primary_key = True, autoincrement = True)
    date = Column(Date)
    kate_score = Column(Integer)
    will_score = Column(Integer)