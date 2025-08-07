from pydantic import BaseModel
from typing import Optional

class SoundReadSchema(BaseModel):
    id: int
    title: str
    description: str
    category: str
    duration: float

    class Config:
        from_attributes = True  # Updated from orm_mode to from_attributes

# New schemas for admin functionality
class TherapySoundResponse(BaseModel):
    id: int
    title: str
    description: str
    category: str
    duration: float
    file_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    is_premium: Optional[bool] = False

    class Config:
        from_attributes = True

class TherapySoundCreate(BaseModel):
    title: str
    description: str
    category: str
    duration: float
    file_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    is_premium: bool = False

class TherapySoundUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    duration: Optional[float] = None
    file_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    is_premium: Optional[bool] = None
