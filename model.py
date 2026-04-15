
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
    
    is_deleted = Column(Boolean, default=False)
    images = relationship("Image", back_populates="user", cascade="all, delete")


class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    image_url = Column(String)

    user_id = Column(Integer, ForeignKey("users.id"))

    # 🔗 relationship
    user = relationship("User", back_populates="images")
    
    # create table
Base.metadata.create_all(bind=engine)