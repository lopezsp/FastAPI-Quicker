from config.database import Base
from sqlalchemy import Column, String, Integer, DateTime


class User(Base):

    __tablename__ = "Users"

    user_id = Column(Integer, primary_key = True)
    email = Column(String)
    password = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    birth_date = Column(DateTime)
