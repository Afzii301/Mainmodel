from email.mime import image
import os
from fastapi import FastAPI, Depends, HTTPException, Query,UploadFile,File
from sqlalchemy.orm import Session,declarative_base,relationship
from db import SessionLocal
from model import User,Image
from schemas import ResetPassword, UserResponse, UserCreate, UserUpdate
from utils import hash_password, verify_password
from fastapi.staticfiles import StaticFiles
from schemas import LoginSchema
app = FastAPI(
    title="User Management API",
    description="A simple User Management API with FastAPI and SQLAlchemy"
)
app.mount("/static", StaticFiles(directory="static"), name="static")


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





@app.post("/login")
def login(user: LoginSchema, db: Session = Depends(get_db)):

    # Step 1: user find karo
    db_user = db.query(User).filter(
        User.email == user.email,
        User.is_deleted == False
    ).first()

    # Step 2: agar user exist nahi karta
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Step 3: password verify karo
    if not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Step 4: success
    return {
        "message": "Login successful",
        "user_id": db_user.id,
        "email": db_user.email
    }



@app.post("/upload/{user_id}")
def upload_file(user_id:int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    
    db_user =db.query(User).filter(User.id==user_id, User.is_deleted==False).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    upload_dir = "static"
    os.makedirs(upload_dir, exist_ok=True)
    
    
    file_path=os.path.join(upload_dir, file.filename)
    
    with open(file_path, "wb") as f:
     f.write(file.file.read())
    
    new_image=Image(
        path=file_path,
        file_name=file.filename,
        user_id=user_id
    )
        
    db.add(new_image)
    db.commit()
    db.refresh(db_user)
        
    file_url=f"/static/{file.filename}"
        
    return {"file_url": file_url, "detail": "File uploaded successfully"}


