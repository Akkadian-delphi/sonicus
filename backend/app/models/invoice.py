from sqlalchemy import Column, Integer, ForeignKey, DateTime, Float, String
from sqlalchemy.orm import relationship
from app.db.base import Base

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    amount = Column(Float, nullable=False)
    issue_date = Column(DateTime, nullable=False)
    status = Column(String, nullable=False)

    # Temporarily commented out relationships to avoid circular import issues
    # user = relationship("User", back_populates="invoices")
    # subscription = relationship("Subscription", back_populates="invoices")
