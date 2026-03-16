from fastapi import FastAPI,Depends
from pydantic import BaseModel
from sqlalchemy .orm   import Session
from db import SessionLocal
from model import User
from schemas import UserResponse

app=FastAPI()

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
@app.get("/users",response_model=list[UserResponse])
def get_users(db:Session=Depends(get_db)):
    users=db.query(User).all()
    return users