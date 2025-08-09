"""
Pydantic schemas for organization branding management
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime
import re


class BrandingColorsSchema(BaseModel):
    primary: Optional[str] = Field(None, description="Primary brand color (hex)")
    secondary: Optional[str] = Field(None, description="Secondary brand color (hex)")
    accent: Optional[str] = Field(None, description="Accent color (hex)")
    background: Optional[str] = Field("#ffffff", description="Background color (hex)")
    text: Optional[str] = Field("#333333", description="Primary text color (hex)")

    @validator('primary', 'secondary', 'accent', 'background', 'text', allow_reuse=True)
    def validate_hex_color(cls, v):
        if v is not None and not re.match(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$', v):
            raise ValueError('Color must be a valid hex color (e.g., #FF5722 or #F57)')
        return v


class BrandingTypographySchema(BaseModel):
    font_family: Optional[str] = Field("Inter, sans-serif", description="Primary font family")
    heading_font: Optional[str] = Field(None, description="Heading font family")


class BrandingLayoutSchema(BaseModel):
    sidebar_style: Optional[str] = Field("default", description="Sidebar style")
    theme_mode: Optional[str] = Field("light", description="Theme mode")

    @validator('sidebar_style', allow_reuse=True)
    def validate_sidebar_style(cls, v):
        allowed = ['default', 'compact', 'minimal']
        if v not in allowed:
            raise ValueError(f'Sidebar style must be one of: {allowed}')
        return v

    @validator('theme_mode', allow_reuse=True)
    def validate_theme_mode(cls, v):
        allowed = ['light', 'dark', 'auto']
        if v not in allowed:
            raise ValueError(f'Theme mode must be one of: {allowed}')
        return v


class OrganizationBrandingCreate(BaseModel):
    """Schema for creating organization branding"""
    logo_url: Optional[str] = Field(None, description="URL to organization logo")
    favicon_url: Optional[str] = Field(None, description="URL to custom favicon")
    colors: Optional[BrandingColorsSchema] = Field(default_factory=BrandingColorsSchema)
    typography: Optional[BrandingTypographySchema] = Field(default_factory=BrandingTypographySchema)
    layout: Optional[BrandingLayoutSchema] = Field(default_factory=BrandingLayoutSchema)
    custom_css: Optional[str] = Field(None, description="Custom CSS for advanced customization")

    class Config:
        json_schema_extra = {
            "example": {
                "logo_url": "https://example.com/logo.png",
                "favicon_url": "https://example.com/favicon.ico",
                "colors": {
                    "primary": "#3B82F6",
                    "secondary": "#64748B",
                    "accent": "#10B981",
                    "background": "#FFFFFF",
                    "text": "#1F2937"
                },
                "typography": {
                    "font_family": "Roboto, sans-serif",
                    "heading_font": "Roboto Slab, serif"
                },
                "layout": {
                    "sidebar_style": "compact",
                    "theme_mode": "light"
                },
                "custom_css": ".custom-header { background: linear-gradient(45deg, #3B82F6, #10B981); }"
            }
        }


class OrganizationBrandingUpdate(BaseModel):
    """Schema for updating organization branding"""
    logo_url: Optional[str] = Field(None, description="URL to organization logo")
    favicon_url: Optional[str] = Field(None, description="URL to custom favicon")
    colors: Optional[BrandingColorsSchema] = None
    typography: Optional[BrandingTypographySchema] = None
    layout: Optional[BrandingLayoutSchema] = None
    custom_css: Optional[str] = Field(None, description="Custom CSS for advanced customization")
    is_active: Optional[bool] = Field(None, description="Whether branding is active")


class OrganizationBrandingResponse(BaseModel):
    """Schema for organization branding response"""
    id: int
    organization_id: int
    logo_url: Optional[str]
    favicon_url: Optional[str]
    colors: Dict[str, Optional[str]]
    typography: Dict[str, Optional[str]]
    layout: Dict[str, str]
    custom_css: Optional[str]
    is_active: bool
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class LogoUploadResponse(BaseModel):
    """Response schema for logo upload"""
    success: bool
    message: str
    logo_url: Optional[str] = None
    filename: Optional[str] = None


class BrandingPreviewRequest(BaseModel):
    """Schema for branding preview request"""
    colors: Optional[BrandingColorsSchema] = None
    typography: Optional[BrandingTypographySchema] = None
    layout: Optional[BrandingLayoutSchema] = None
    custom_css: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "colors": {
                    "primary": "#FF5722",
                    "secondary": "#795548",
                    "accent": "#FF9800"
                },
                "typography": {
                    "font_family": "Poppins, sans-serif"
                },
                "layout": {
                    "theme_mode": "dark"
                }
            }
        }


class BrandingThemePreset(BaseModel):
    """Predefined branding theme presets"""
    name: str
    description: str
    colors: BrandingColorsSchema
    typography: BrandingTypographySchema
    layout: BrandingLayoutSchema

    @classmethod
    def get_presets(cls):
        """Get all available theme presets"""
        return {
            "corporate_blue": cls(
                name="Corporate Blue",
                description="Professional blue theme perfect for corporate environments",
                colors=BrandingColorsSchema(
                    primary="#1E40AF",
                    secondary="#64748B",
                    accent="#3B82F6",
                    background="#FFFFFF",
                    text="#1F2937"
                ),
                typography=BrandingTypographySchema(
                    font_family="Inter, sans-serif",
                    heading_font="Inter, sans-serif"
                ),
                layout=BrandingLayoutSchema(
                    sidebar_style="default",
                    theme_mode="light"
                )
            ),
            "wellness_green": cls(
                name="Wellness Green",
                description="Calming green theme ideal for healthcare and wellness organizations",
                colors=BrandingColorsSchema(
                    primary="#059669",
                    secondary="#6B7280",
                    accent="#10B981",
                    background="#F9FAFB",
                    text="#111827"
                ),
                typography=BrandingTypographySchema(
                    font_family="Nunito, sans-serif",
                    heading_font="Nunito, sans-serif"
                ),
                layout=BrandingLayoutSchema(
                    sidebar_style="minimal",
                    theme_mode="light"
                )
            ),
            "creative_purple": cls(
                name="Creative Purple",
                description="Vibrant purple theme for creative and design-focused organizations",
                colors=BrandingColorsSchema(
                    primary="#7C3AED",
                    secondary="#8B5CF6",
                    accent="#A78BFA",
                    background="#FFFFFF",
                    text="#374151"
                ),
                typography=BrandingTypographySchema(
                    font_family="Poppins, sans-serif",
                    heading_font="Poppins, sans-serif"
                ),
                layout=BrandingLayoutSchema(
                    sidebar_style="compact",
                    theme_mode="light"
                )
            ),
            "dark_mode": cls(
                name="Dark Professional",
                description="Sleek dark theme for modern, tech-savvy organizations",
                colors=BrandingColorsSchema(
                    primary="#3B82F6",
                    secondary="#64748B",
                    accent="#06B6D4",
                    background="#111827",
                    text="#F9FAFB"
                ),
                typography=BrandingTypographySchema(
                    font_family="JetBrains Mono, monospace",
                    heading_font="Inter, sans-serif"
                ),
                layout=BrandingLayoutSchema(
                    sidebar_style="minimal",
                    theme_mode="dark"
                )
            )
        }
