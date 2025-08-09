"""
Advanced theme management models for custom themes, scheduling, and templates
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
from enum import Enum
import uuid


class ThemeType(str, Enum):
    PRESET = "preset"
    CUSTOM = "custom"
    TEMPLATE = "template"
    GENERATED = "generated"


class ThemeCategory(str, Enum):
    CORPORATE = "corporate"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    TECHNOLOGY = "technology"
    CREATIVE = "creative"
    FINANCE = "finance"
    WELLNESS = "wellness"
    ACCESSIBILITY = "accessibility"


class OrganizationTheme(Base):
    __tablename__ = "organization_themes"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    
    # Theme identity
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    theme_type = Column(String(20), nullable=False, default=ThemeType.CUSTOM)
    category = Column(String(50), nullable=True)
    
    # Theme configuration
    colors = Column(JSON, nullable=False, comment="Color palette as JSON")
    typography = Column(JSON, nullable=True, comment="Typography settings")
    layout = Column(JSON, nullable=True, comment="Layout and spacing settings")
    custom_css = Column(Text, nullable=True, comment="Custom CSS rules")
    
    # Theme metadata
    is_active = Column(Boolean, default=False, comment="Currently active theme")
    is_favorite = Column(Boolean, default=False, comment="User marked as favorite")
    is_public = Column(Boolean, default=False, comment="Can be shared as template")
    usage_count = Column(Integer, default=0, comment="Times this theme was applied")
    
    # Accessibility features
    high_contrast = Column(Boolean, default=False, comment="High contrast mode")
    large_text = Column(Boolean, default=False, comment="Large text mode")
    reduced_motion = Column(Boolean, default=False, comment="Reduced animation mode")
    
    # Generation metadata (for AI-generated themes)
    source_theme_id = Column(Integer, nullable=True, comment="ID of theme this was generated from")
    generation_algorithm = Column(String(50), nullable=True, comment="Algorithm used for generation")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    organization = relationship("Organization")
    schedules = relationship("ThemeSchedule", back_populates="theme", cascade="all, delete-orphan")
    
    class Config:
        from_attributes = True

    def to_dict(self):
        """Convert theme to dictionary for frontend consumption"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "theme_type": self.theme_type,
            "category": self.category,
            "colors": self.colors,
            "typography": self.typography,
            "layout": self.layout,
            "custom_css": self.custom_css,
            "is_active": self.is_active,
            "is_favorite": self.is_favorite,
            "high_contrast": self.high_contrast,
            "large_text": self.large_text,
            "reduced_motion": self.reduced_motion,
            "usage_count": self.usage_count,
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at is not None else None
        }


class ThemeSchedule(Base):
    __tablename__ = "theme_schedules"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    theme_id = Column(Integer, ForeignKey("organization_themes.id", ondelete="CASCADE"), nullable=False)
    
    # Schedule configuration
    name = Column(String(255), nullable=False, comment="Schedule name")
    is_active = Column(Boolean, default=True, comment="Schedule is active")
    
    # Time-based scheduling
    start_time = Column(Time, nullable=False, comment="Time to activate theme")
    end_time = Column(Time, nullable=False, comment="Time to deactivate theme") 
    
    # Day-based scheduling
    days_of_week = Column(JSON, nullable=False, comment="Days when schedule applies [0-6, 0=Monday]")
    
    # Date range (optional)
    start_date = Column(DateTime(timezone=True), nullable=True, comment="Schedule start date")
    end_date = Column(DateTime(timezone=True), nullable=True, comment="Schedule end date")
    
    # Priority and conditions
    priority = Column(Integer, default=0, comment="Higher priority schedules override lower ones")
    conditions = Column(JSON, nullable=True, comment="Additional conditions (weather, events, etc)")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization")
    theme = relationship("OrganizationTheme", back_populates="schedules")
    
    class Config:
        from_attributes = True

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "theme_id": self.theme_id,
            "is_active": self.is_active,
            "start_time": self.start_time.strftime("%H:%M") if self.start_time is not None else None,
            "end_time": self.end_time.strftime("%H:%M") if self.end_time is not None else None,
            "days_of_week": self.days_of_week,
            "start_date": self.start_date.isoformat() if self.start_date is not None else None,
            "end_date": self.end_date.isoformat() if self.end_date is not None else None,
            "priority": self.priority,
            "conditions": self.conditions,
            "created_at": self.created_at.isoformat() if self.created_at is not None else None
        }


class ThemeTemplate(Base):
    __tablename__ = "theme_templates"

    id = Column(Integer, primary_key=True, index=True)
    
    # Template identity
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False)
    industry = Column(String(100), nullable=True)
    
    # Template configuration
    colors = Column(JSON, nullable=False)
    typography = Column(JSON, nullable=True)
    layout = Column(JSON, nullable=True)
    custom_css = Column(Text, nullable=True)
    
    # Template metadata
    is_premium = Column(Boolean, default=False, comment="Premium template requiring upgrade")
    popularity_score = Column(Integer, default=0, comment="Usage popularity score")
    tags = Column(JSON, nullable=True, comment="Searchable tags")
    preview_image_url = Column(String(512), nullable=True, comment="Template preview image")
    
    # Accessibility variants
    has_dark_variant = Column(Boolean, default=False)
    has_high_contrast_variant = Column(Boolean, default=False)
    accessibility_score = Column(Integer, nullable=True, comment="Accessibility rating 1-100")
    
    # Attribution
    created_by = Column(String(255), nullable=True, comment="Template creator")
    license_type = Column(String(50), default="standard", comment="Usage license")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    class Config:
        from_attributes = True

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "industry": self.industry,
            "colors": self.colors,
            "typography": self.typography,
            "layout": self.layout,
            "custom_css": self.custom_css,
            "is_premium": self.is_premium,
            "tags": self.tags,
            "preview_image_url": self.preview_image_url,
            "has_dark_variant": self.has_dark_variant,
            "has_high_contrast_variant": self.has_high_contrast_variant,
            "accessibility_score": self.accessibility_score,
            "popularity_score": self.popularity_score,
            "created_at": self.created_at.isoformat() if self.created_at is not None else None
        }
