from pydantic import BaseModel, EmailStr, Field
from typing import Optional

# Base schema for shared fields
class UserBase(BaseModel):
    # min_length=1 ensures the name is NOT an empty string ""
    name: str = Field(..., min_length=1)
    email: EmailStr 
    password: str = Field(..., min_length=8)  # Password must be at least 8 characters long

# Used for creating a user (POST)
class UserCreate(UserBase):
    pass    

# Used for updating a user (PATCH)
class UserUpdate(BaseModel):
    # Here, min_length=1 ensures that IF they provide a name, it isn't empty
    name: Optional[str] = Field(None, min_length=1)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)  # Password must be at least 8 characters long
    
    
class ResetPassword(BaseModel):
    new_password: str = Field(..., min_length=8)  # New password must be at least 8 characters long
    
    
class LoginSchema(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)  # Password must be at least 8 characters long

# Used for returning user data (Response)
class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True
        
        
        
        
 
        
        