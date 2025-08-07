from pydantic import BaseModel
from datetime import datetime

class SubscriptionCreateSchema(BaseModel):
    sound_id: int

class SubscriptionReadSchema(BaseModel):
    id: int
    start_date: datetime
    end_date: datetime
    status: str

    class Config:
        from_attributes = True  # Updated from orm_mode to from_attributes
