from fastapi import FastAPI,Depends,HTTPException
from pydantic import BaseModel
from sqlalchemy .orm   import Session
from db import SessionLocal
from model import User
from schemas import UserCreate, UserResponse

app=FastAPI()

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
@app.get("/user",response_model=list[UserResponse])
def get_users(db:Session=Depends(get_db)):
    users=db.query(User).all()
    return users



@app.post("/users")
def create_user(user: UserCreate, db: Session = Depends(get_db)):

    existing_user = db.query(User).filter(User.email == user.email).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Bad Request")

    db_user = User(name=user.name, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user





