from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship
from app.db.base import Base

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sound_id = Column(Integer, ForeignKey("therapy_sounds.id"), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)
    status = Column(String, nullable=False)

    # Temporarily commented out relationships to avoid circular import issues
    # user = relationship("User", back_populates="subscriptions")
    # sound = relationship("TherapySound", back_populates="subscriptions")
    # invoices = relationship("Invoice", back_populates="subscription")
