from config.database import Base
from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey


class User(Base):

    __tablename__ = "Users"

    user_id = Column(Integer, primary_key = True, unique = True)
    email = Column(String, unique = True)
    password = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    birth_date = Column(DateTime)

class Quick(User):

    __tablename__ = "Quick"

    quick_id = Column(Integer, primary_key = True, unique = True)
    content = Column (String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    by = Column(JSON, ForeignKey('Users.user_id'))
    
