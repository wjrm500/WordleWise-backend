from sqlalchemy import Column, Date, Integer
from database.models import db

class Day(db.Model):
    __tablename__ = 'day'
    id = Column(Integer, primary_key = True, autoincrement = True)
    date = Column(Date)
    kate_score = Column(Integer)
    will_score = Column(Integer)