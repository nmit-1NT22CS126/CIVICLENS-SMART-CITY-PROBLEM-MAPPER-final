from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# User Schemas
class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    name: str
    password: str

class UserLogin(UserBase):
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    created_at: Optional[str] = None

    class Config:
        from_attributes = True

# Complaint Schemas
class ComplaintBase(BaseModel):
    title: Optional[str] = None
    description: str
    latitude: float
    longitude: float

class ComplaintCreate(ComplaintBase):
    pass

class ComplaintResponse(BaseModel):
    id: int
    tracking_id: str
    user_id: int
    title: Optional[str] = None
    description: str
    category: Optional[str] = None
    classification_result: Optional[str] = None
    status: str
    image_url: Optional[str] = None
    latitude: float
    longitude: float
    lat_img: Optional[float] = None
    long_img: Optional[float] = None
    after_image_url: Optional[str] = None
    verification_confidence: Optional[float] = None
    verified_at: Optional[str] = None
    verified_by: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True

class ComplaintStatusUpdate(BaseModel):
    status: str

class AdminNoteCreate(BaseModel):
    message: str

class AdminLogResponse(BaseModel):
    id: int
    complaint_id: int
    admin_id: int
    message: str
    timestamp: Optional[str] = None

    class Config:
        from_attributes = True

# Token Schema
class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    user_id: int

class TokenData(BaseModel):
    email: str | None = None
    role: str | None = None

