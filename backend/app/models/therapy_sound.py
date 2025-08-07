from sqlalchemy import Column, Integer, String, Float, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base

class TherapySound(Base):
    __tablename__ = "therapy_sounds"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    category = Column(String, nullable=True)
    duration = Column(Float, nullable=False)
    secure_storage_path = Column(String, nullable=False)
    file_url = Column(String, nullable=True)  # Public URL for streaming
    thumbnail_url = Column(String, nullable=True)  # Thumbnail image URL
    is_premium = Column(Boolean, default=False)  # Whether requires subscription
    
    # Add relationship
    # Temporarily commented out to avoid circular import issues
    # subscriptions = relationship("Subscription", back_populates="sound")
    # plays = relationship("ContentPlay", back_populates="content")  # Content play records (temporarily disabled)
