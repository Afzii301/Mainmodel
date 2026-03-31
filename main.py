from fastapi import FastAPI,Depends,HTTPException
from pydantic import BaseModel
from sqlalchemy .orm   import Session
from db import SessionLocal
from model import User
from schemas import UserResponse,UserCreate

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



@app.post("/users",response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(name=user.name, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user



 