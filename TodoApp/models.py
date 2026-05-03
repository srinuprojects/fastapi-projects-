from database import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey

class Todos(Base):
    __tablename__ = 'todos'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, index=True)
    completed = Column(Boolean, default=False)
    owner_id = Column(Integer, ForeignKey("users.id"))
    priority = Column(Integer, default=0)
    
    

class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    is_active = Column(Boolean, default=True)
    hashed_password = Column(String)
    role = Column(String, default="user")