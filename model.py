
from sqlalchemy import  Boolean, Column, Integer, String,ForeignKey
from db import Base, engine
from sqlalchemy.orm import relationship

# Model
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)
    path=Column(String, nullable=True)
    is_deleted = Column(Boolean, default=False)
    file_name=Column(String, nullable=True)
    image=relationship("Image", back_populates="user", uselist=False)


class Image(Base):
    __tablename__="images"
    id=Column(Integer,primary_key=True,index=True)
    path=Column(String, nullable=True)
    file_name=Column(String, nullable=True)
    
    user_id=Column(Integer,ForeignKey("users.id"))
    user=relationship("User", back_populates="image")


# create table
Base.metadata.create_all(bind=engine)
    