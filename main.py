from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session,declarative_base
from db import SessionLocal
from model import User
from schemas import ResetPassword, UserResponse, UserCreate, UserUpdate
from utils import hash_password, verify_password

app = FastAPI(
    title="User Management API",
    description="A simple User Management API with FastAPI and SQLAlchemy"
)


# -------------------- DB Dependency --------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------------------- GET ALL USERS --------------------
@app.get("/users", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).filter(User.is_deleted == False).all()

    # Filter out soft-deleted users

    # Optional safety: invalid data skip karega
    valid_users = []
    for user in users:
        try:
            valid_users.append(UserResponse.model_validate(user))
        except:
            pass

    return valid_users


# -------------------- CREATE USER --------------------
@app.post("/users", response_model=UserResponse, status_code=201)
def create_user(user: UserCreate, db: Session = Depends(get_db)):

    # Check duplicate email
    existing_user = db.query(User).filter(User.email == user.email, User.is_deleted == False).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    db_user = User(name=user.name, email=user.email, password=hash_password(user.password))
    
    db.add(db_user)

    try:
        db.commit()
        db.refresh(db_user)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

    return db_user



# -------------------- UPDATE USER (PATCH) --------------------
@app.patch("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user: UserUpdate, db: Session = Depends(get_db)):

    db_user = db.query(User).filter(User.id == user_id, User.is_deleted == False).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update name (if provided)
    if user.name is not None:
        db_user.name = user.name

    # Update email (if provided)
    if user.email is not None:
        email_exists = db.query(User).filter(User.email == user.email, User.is_deleted == False).first()

        if email_exists and email_exists.id != user_id:
            raise HTTPException(status_code=400, detail="Email already in use")

        db_user.email = user.email

    # Update password (if provided)
    if user.password is not None:
        db_user.password = hash_password(user.password)

    try:
        db.commit()
        db.refresh(db_user)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error during update")

    return db_user


# -------------------- DELETE USER --------------------
@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):

    db_user = db.query(User).filter(User.id == user_id, User.is_deleted == False).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    # soft delete approach
    db_user.is_deleted = True
    db.commit()

    return {"detail": "User  deleted successfully"}



# -------------------- GET SINGLE USER --------------------
@app.get("/users/{user_id}", response_model=UserResponse)
def get_single_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id, User.is_deleted == False).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user





@app.post("/users/{user_id}/reset-password")
def reset_password(user_id: int, new_password: str = Query(..., min_length=8), db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id, User.is_deleted == False).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    db_user.password = hash_password(new_password)
    try:
        db.commit()
        db.refresh(db_user)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error during password reset")

    return {"detail": "Password reset successfully"}