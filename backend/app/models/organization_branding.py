"""
Organization branding model for customizing organization appearance
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
import uuid


class OrganizationBranding(Base):
    __tablename__ = "organization_branding"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), unique=True, index=True)
    
    # Logo configuration
    logo_url = Column(String(512), nullable=True, comment="URL to organization logo")
    logo_filename = Column(String(255), nullable=True, comment="Original filename of uploaded logo")
    favicon_url = Column(String(512), nullable=True, comment="URL to custom favicon")
    
    # Color scheme
    primary_color = Column(String(7), nullable=True, comment="Primary brand color (hex)")
    secondary_color = Column(String(7), nullable=True, comment="Secondary brand color (hex)")
    accent_color = Column(String(7), nullable=True, comment="Accent color (hex)")
    background_color = Column(String(7), default="#ffffff", comment="Background color (hex)")
    text_color = Column(String(7), default="#333333", comment="Primary text color (hex)")
    
    # Typography
    font_family = Column(String(100), default="Inter, sans-serif", comment="Primary font family")
    heading_font = Column(String(100), nullable=True, comment="Heading font family")
    
    # Layout preferences
    sidebar_style = Column(String(20), default="default", comment="Sidebar style: default, compact, minimal")
    theme_mode = Column(String(10), default="light", comment="Theme mode: light, dark, auto")
    
    # Custom CSS
    custom_css = Column(Text, nullable=True, comment="Custom CSS for advanced customization")
    
    # Metadata
    is_active = Column(Boolean, default=True, comment="Whether branding is active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization", back_populates="branding")

    class Config:
        from_attributes = True

    def to_dict(self):
        """Convert branding to dictionary for frontend consumption"""
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "logo_url": self.logo_url,
            "favicon_url": self.favicon_url,
            "colors": {
                "primary": self.primary_color,
                "secondary": self.secondary_color,
                "accent": self.accent_color,
                "background": self.background_color,
                "text": self.text_color
            },
            "typography": {
                "font_family": self.font_family,
                "heading_font": self.heading_font
            },
            "layout": {
                "sidebar_style": self.sidebar_style,
                "theme_mode": self.theme_mode
            },
            "custom_css": self.custom_css,
            "is_active": self.is_active,
            "updated_at": self.updated_at.isoformat() if self.updated_at is not None else None
        }

    @classmethod
    def get_default_branding(cls):
        """Get default branding configuration"""
        return {
            "colors": {
                "primary": "#3B82F6",  # Blue
                "secondary": "#64748B",  # Slate
                "accent": "#10B981",  # Emerald
                "background": "#FFFFFF",
                "text": "#1F2937"
            },
            "typography": {
                "font_family": "Inter, sans-serif",
                "heading_font": "Inter, sans-serif"
            },
            "layout": {
                "sidebar_style": "default",
                "theme_mode": "light"
            }
        }
