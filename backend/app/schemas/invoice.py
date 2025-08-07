from pydantic import BaseModel
from datetime import datetime

class InvoiceReadSchema(BaseModel):
    id: int
    amount: float
    issue_date: datetime
    status: str

    class Config:
        from_attributes = True  # Updated from orm_mode to from_attributes
