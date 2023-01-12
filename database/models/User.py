from sqlalchemy import Column, Integer, String
from database.models import Base

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key = True, autoincrement = True)
    username = Column(String)
    password_hash = Column(String)