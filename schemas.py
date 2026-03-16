from pydantic import BaseModel

# User create karne ke liye
class UserCreate(BaseModel):
    name: str
    email: str


# Response ke liye schema
class UserResponse(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        orm_mode = True