
from sqlalchemy import  Boolean, Column, Integer, String
from db import Base, engine


# Model
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True)
    is_deleted = Column(Boolean, default=False)

# create table
Base.metadata.create_all(bind=engine)