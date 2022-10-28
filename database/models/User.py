from sqlalchemy import Column, Integer, String
from database.models import db

class User(db.Model):
    __tablename__ = 'user'
    id = Column(Integer, primary_key = True, autoincrement = True)
    username = Column(String)
    password_hash = Column(String)