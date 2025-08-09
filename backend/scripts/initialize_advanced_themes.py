"""
Initialize theme templates and create database tables for advanced theme management
"""

import asyncio
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine
from app.db.base import Base
from app.models.theme_management import ThemeTemplate, OrganizationTheme, ThemeSchedule
from app.models.organization import Organization  # Import to ensure table exists
import json


def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully")


def create_theme_templates(db: Session):
    """Create initial theme templates"""
    
    templates = [
        {
            "name": "Corporate Professional",
            "description": "Clean and professional theme perfect for corporate environments",
            "category": "corporate",
            "industry": "business",
            "colors": {
                "mode": "light",
                "primary": "#1e40af",
                "secondary": "#64748b",
                "accent": "#3730a3",
                "success": "#059669",
                "warning": "#d97706",
                "error": "#dc2626",
                "background": "#ffffff",
                "surface": "#f8fafc",
                "text": "#1e293b",
                "text_secondary": "#64748b"
            },
            "typography": {
                "primary_font": "Inter",
                "secondary_font": "system-ui",
                "font_scale": 1.0,
                "line_height": 1.5
            },
            "layout": {
                "border_radius": "6px",
                "spacing_scale": 1.0,
                "container_max_width": "1200px"
            },
            "has_dark_variant": True,
            "has_high_contrast_variant": True,
            "accessibility_score": 95,
            "tags": ["professional", "corporate", "clean", "modern"],
            "popularity_score": 100
        },
        {
            "name": "Healthcare Calm",
            "description": "Soothing colors and gentle design for healthcare applications",
            "category": "healthcare",
            "industry": "healthcare",
            "colors": {
                "mode": "light",
                "primary": "#0d9488",
                "secondary": "#64748b",
                "accent": "#06b6d4",
                "success": "#10b981",
                "warning": "#f59e0b",
                "error": "#ef4444",
                "background": "#fefefe",
                "surface": "#f0fdfa",
                "text": "#134e4a",
                "text_secondary": "#6b7280"
            },
            "typography": {
                "primary_font": "Inter",
                "secondary_font": "system-ui",
                "font_scale": 1.1,
                "line_height": 1.6
            },
            "layout": {
                "border_radius": "12px",
                "spacing_scale": 1.2,
                "container_max_width": "1200px"
            },
            "has_dark_variant": True,
            "has_high_contrast_variant": True,
            "accessibility_score": 98,
            "tags": ["healthcare", "calming", "accessible", "wellness"],
            "popularity_score": 85
        },
        {
            "name": "Creative Vibrant",
            "description": "Bold and colorful theme for creative agencies and startups",
            "category": "creative",
            "industry": "creative",
            "colors": {
                "mode": "light",
                "primary": "#7c3aed",
                "secondary": "#64748b",
                "accent": "#ec4899",
                "success": "#10b981",
                "warning": "#f59e0b",
                "error": "#ef4444",
                "background": "#ffffff",
                "surface": "#faf5ff",
                "text": "#1e293b",
                "text_secondary": "#64748b"
            },
            "typography": {
                "primary_font": "Poppins",
                "secondary_font": "Inter",
                "font_scale": 1.1,
                "line_height": 1.6
            },
            "layout": {
                "border_radius": "16px",
                "spacing_scale": 1.3,
                "container_max_width": "1400px"
            },
            "has_dark_variant": True,
            "has_high_contrast_variant": False,
            "accessibility_score": 88,
            "tags": ["creative", "vibrant", "modern", "startup"],
            "popularity_score": 75
        },
        {
            "name": "Technology Dark",
            "description": "Sleek dark theme optimized for tech companies and developers",
            "category": "technology",
            "industry": "technology",
            "colors": {
                "mode": "dark",
                "primary": "#3b82f6",
                "secondary": "#64748b",
                "accent": "#06b6d4",
                "success": "#10b981",
                "warning": "#f59e0b",
                "error": "#ef4444",
                "background": "#0f172a",
                "surface": "#1e293b",
                "text": "#f1f5f9",
                "text_secondary": "#94a3b8"
            },
            "typography": {
                "primary_font": "Inter",
                "secondary_font": "JetBrains Mono",
                "font_scale": 0.95,
                "line_height": 1.5
            },
            "layout": {
                "border_radius": "8px",
                "spacing_scale": 1.1,
                "container_max_width": "1600px"
            },
            "has_dark_variant": False,
            "has_high_contrast_variant": True,
            "accessibility_score": 92,
            "tags": ["technology", "dark", "developer", "modern"],
            "popularity_score": 90
        },
        {
            "name": "Finance Conservative",
            "description": "Traditional and trustworthy design for financial institutions",
            "category": "finance",
            "industry": "finance",
            "colors": {
                "mode": "light",
                "primary": "#1e40af",
                "secondary": "#64748b",
                "accent": "#059669",
                "success": "#059669",
                "warning": "#d97706",
                "error": "#dc2626",
                "background": "#ffffff",
                "surface": "#f9fafb",
                "text": "#111827",
                "text_secondary": "#6b7280"
            },
            "typography": {
                "primary_font": "Inter",
                "secondary_font": "Georgia",
                "font_scale": 0.95,
                "line_height": 1.5
            },
            "layout": {
                "border_radius": "4px",
                "spacing_scale": 0.9,
                "container_max_width": "1200px"
            },
            "has_dark_variant": True,
            "has_high_contrast_variant": True,
            "accessibility_score": 96,
            "tags": ["finance", "conservative", "trustworthy", "traditional"],
            "popularity_score": 70
        },
        {
            "name": "Education Friendly",
            "description": "Warm and approachable theme for educational institutions",
            "category": "education",
            "industry": "education",
            "colors": {
                "mode": "light",
                "primary": "#ea580c",
                "secondary": "#64748b",
                "accent": "#0ea5e9",
                "success": "#16a34a",
                "warning": "#eab308",
                "error": "#dc2626",
                "background": "#fffbeb",
                "surface": "#fef3c7",
                "text": "#92400e",
                "text_secondary": "#a8a29e"
            },
            "typography": {
                "primary_font": "Poppins",
                "secondary_font": "Inter",
                "font_scale": 1.05,
                "line_height": 1.6
            },
            "layout": {
                "border_radius": "12px",
                "spacing_scale": 1.15,
                "container_max_width": "1300px"
            },
            "has_dark_variant": True,
            "has_high_contrast_variant": True,
            "accessibility_score": 94,
            "tags": ["education", "friendly", "warm", "approachable"],
            "popularity_score": 65
        },
        {
            "name": "Wellness Zen",
            "description": "Peaceful and mindful design for wellness and meditation apps",
            "category": "wellness",
            "industry": "wellness",
            "colors": {
                "mode": "light",
                "primary": "#059669",
                "secondary": "#64748b",
                "accent": "#8b5cf6",
                "success": "#10b981",
                "warning": "#f59e0b",
                "error": "#ef4444",
                "background": "#f0fdf4",
                "surface": "#dcfce7",
                "text": "#14532d",
                "text_secondary": "#6b7280"
            },
            "typography": {
                "primary_font": "Inter",
                "secondary_font": "system-ui",
                "font_scale": 1.0,
                "line_height": 1.7
            },
            "layout": {
                "border_radius": "20px",
                "spacing_scale": 1.4,
                "container_max_width": "1100px"
            },
            "has_dark_variant": True,
            "has_high_contrast_variant": True,
            "accessibility_score": 97,
            "tags": ["wellness", "zen", "peaceful", "mindful"],
            "popularity_score": 80
        },
        {
            "name": "High Contrast Accessibility",
            "description": "Maximum contrast theme designed for users with visual impairments",
            "category": "accessibility",
            "industry": None,
            "colors": {
                "mode": "high_contrast",
                "primary": "#000000",
                "secondary": "#333333",
                "accent": "#0000ff",
                "success": "#006600",
                "warning": "#996600",
                "error": "#cc0000",
                "background": "#ffffff",
                "surface": "#f5f5f5",
                "text": "#000000",
                "text_secondary": "#333333"
            },
            "typography": {
                "primary_font": "Inter",
                "secondary_font": "system-ui",
                "font_scale": 1.3,
                "line_height": 1.8
            },
            "layout": {
                "border_radius": "2px",
                "spacing_scale": 1.5,
                "container_max_width": "1000px"
            },
            "has_dark_variant": True,
            "has_high_contrast_variant": False,
            "accessibility_score": 100,
            "tags": ["accessibility", "high-contrast", "wcag", "a11y"],
            "popularity_score": 45
        }
    ]
    
    print("Creating theme templates...")
    
    for template_data in templates:
        # Check if template already exists
        existing = db.query(ThemeTemplate).filter(
            ThemeTemplate.name == template_data["name"]
        ).first()
        
        if existing:
            print(f"⏭️  Template '{template_data['name']}' already exists, skipping")
            continue
        
        template = ThemeTemplate(
            name=template_data["name"],
            description=template_data["description"],
            category=template_data["category"],
            industry=template_data.get("industry"),
            colors=template_data["colors"],
            typography=template_data["typography"],
            layout=template_data["layout"],
            has_dark_variant=template_data.get("has_dark_variant", False),
            has_high_contrast_variant=template_data.get("has_high_contrast_variant", False),
            accessibility_score=template_data.get("accessibility_score"),
            tags=template_data.get("tags", []),
            popularity_score=template_data.get("popularity_score", 0)
        )
        
        db.add(template)
        print(f"✅ Created template: {template.name}")
    
    db.commit()
    print("🎨 All theme templates created successfully!")


def main():
    """Main initialization function"""
    print("🚀 Initializing Advanced Theme Management System...")
    
    # Create tables
    create_tables()
    
    # Create session and populate templates
    db = SessionLocal()
    try:
        create_theme_templates(db)
    finally:
        db.close()
    
    print("✅ Advanced Theme Management System initialized successfully!")
    print("\n📋 Summary:")
    print("- Database tables created")
    print("- 8 professional theme templates added")
    print("- Templates include: Corporate, Healthcare, Creative, Technology, Finance, Education, Wellness, and Accessibility themes")
    print("\n🔗 Access the theme builder at: http://localhost:3001/organization/themes")


if __name__ == "__main__":
    main()
