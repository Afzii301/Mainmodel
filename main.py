import uuid
import os
import shutil
from fastapi import FastAPI, Depends, File, HTTPException, Query,Header, UploadFile,File
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session,declarative_base
from db import SessionLocal
from config import SECRET_KEY
from utils import hash_password, verify_password
from model import Image,User
from schemas import LoginSchema,ResetPasswordRequest, UserResponse, UserCreate, UserUpdate, ImageResponse
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
    return db.query(User).filter(User.is_deleted == False).all()
    

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
def reset_password(user_id: int, data: ResetPasswordRequest, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id, User.is_deleted == False).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    db_user.password = hash_password(data.new_password)
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

# ............ image upload ..........
@app.post("/upload-image/{user_id}")
def upload_image(
    user_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # 1. user check
    db_user = db.query(User).filter(
        User.id == user_id,
        User.is_deleted == False
    ).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. extension check
    ALLOWED_EXTENSIONS = [".jpg", ".jpeg", ".png"]
    ext = os.path.splitext(file.filename)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid file type")

    # 3. size check
    MAX_SIZE = 2 * 1024 * 1024
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)

    if size > MAX_SIZE:
        raise HTTPException(status_code=400, detail="File too large")

    # 4. unique name
    unique_name = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join("static/uploads", unique_name)

    # 5. save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 6. save DB
    image = Image(
        image_url=f"/static/uploads/{unique_name}",
        user_id=user_id
    )

    db.add(image)
    db.commit()
    db.refresh(image)

    return image

# ...............delete image.............

@app.delete("/users/{user_id}/images/{image_id}")
def delete_user_image(
    user_id: int,
    image_id: int,
    db: Session = Depends(get_db)
):

    # 1. image find (user verify bhi ho raha hai)
    db_image = db.query(Image).filter(
        Image.id == image_id,
        Image.user_id == user_id
    ).first()

    if not db_image:
        raise HTTPException(status_code=404, detail="Image not found")

    # 2. file delete
    if db_image.image_url and os.path.exists(db_image.image_url):
        os.remove(db_image.image_url)

    # 3. DB delete
    db.delete(db_image)
    db.commit()

    return {"message": "Image deleted successfully"}



@app.delete("/reset_api")
def reset_api(secret_key: str = Header(...), db: Session = Depends(get_db)):

    if secret_key != SECRET_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")

    try:
        db.query(Image).delete()   # 👈 child table first
        db.query(User).delete()    # 👈 parent table
        db.commit()

        return {"message": "All data reset successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
    
    
    
