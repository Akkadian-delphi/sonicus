"""
Script to populate theme templates for the advanced theme system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.theme_management import ThemeTemplate, ThemeCategory
import json


def create_theme_templates():
    """Create initial theme templates"""
    
    db = next(get_db())
    
    # Healthcare Templates
    healthcare_templates = [
        {
            "name": "Medical Professional",
            "description": "Clean, professional theme for healthcare organizations",
            "category": ThemeCategory.HEALTHCARE,
            "industry": "healthcare",
            "colors": {
                "mode": "light",
                "primary": "#0ea5e9",
                "secondary": "#06b6d4",
                "accent": "#10b981",
                "success": "#059669",
                "warning": "#d97706",
                "error": "#dc2626",
                "background": "#ffffff",
                "surface": "#f8fafc",
                "text": "#0f172a",
                "text_secondary": "#475569"
            },
            "typography": {
                "primary_font": "Inter",
                "secondary_font": "system-ui",
                "font_scale": 1.0,
                "line_height": 1.6
            },
            "layout": {
                "border_radius": "8px",
                "spacing_scale": 1.2,
                "container_max_width": "1200px"
            },
            "has_dark_variant": True,
            "has_high_contrast_variant": True,
            "accessibility_score": 95,
            "tags": ["medical", "professional", "clean", "accessible"]
        },
        {
            "name": "Wellness Spa",
            "description": "Calming, organic theme for wellness centers",
            "category": ThemeCategory.WELLNESS,
            "industry": "healthcare",
            "colors": {
                "mode": "light",
                "primary": "#059669",
                "secondary": "#0d9488",
                "accent": "#7c3aed",
                "success": "#16a34a",
                "warning": "#ea580c",
                "error": "#dc2626",
                "background": "#f0fdf4",
                "surface": "#ecfdf5",
                "text": "#064e3b",
                "text_secondary": "#047857"
            },
            "typography": {
                "primary_font": "Poppins",
                "secondary_font": "Inter",
                "font_scale": 1.1,
                "line_height": 1.7
            },
            "layout": {
                "border_radius": "12px",
                "spacing_scale": 1.3,
                "container_max_width": "1200px"
            },
            "has_dark_variant": True,
            "has_high_contrast_variant": True,
            "accessibility_score": 92,
            "tags": ["wellness", "spa", "calming", "organic"]
        }
    ]
    
    # Corporate Templates
    corporate_templates = [
        {
            "name": "Corporate Blue",
            "description": "Professional corporate theme with trust-inspiring blue palette",
            "category": ThemeCategory.CORPORATE,
            "industry": "corporate",
            "colors": {
                "mode": "light",
                "primary": "#1e40af",
                "secondary": "#1e3a8a",
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
                "secondary_font": "Georgia",
                "font_scale": 1.0,
                "line_height": 1.5
            },
            "layout": {
                "border_radius": "4px",
                "spacing_scale": 1.0,
                "container_max_width": "1400px"
            },
            "has_dark_variant": True,
            "has_high_contrast_variant": True,
            "accessibility_score": 98,
            "tags": ["corporate", "professional", "business", "trust"]
        },
        {
            "name": "Executive Suite",
            "description": "Premium theme for executive-level organizations",
            "category": ThemeCategory.CORPORATE,
            "industry": "corporate",
            "colors": {
                "mode": "light",
                "primary": "#0f172a",
                "secondary": "#1e293b",
                "accent": "#991b1b",
                "success": "#059669",
                "warning": "#d97706",
                "error": "#dc2626",
                "background": "#ffffff",
                "surface": "#f1f5f9",
                "text": "#0f172a",
                "text_secondary": "#475569"
            },
            "typography": {
                "primary_font": "Inter",
                "secondary_font": "Georgia",
                "font_scale": 0.95,
                "line_height": 1.5
            },
            "layout": {
                "border_radius": "2px",
                "spacing_scale": 0.9,
                "container_max_width": "1200px"
            },
            "has_dark_variant": True,
            "has_high_contrast_variant": True,
            "accessibility_score": 96,
            "tags": ["executive", "premium", "sophisticated", "minimal"]
        }
    ]
    
    # Technology Templates
    technology_templates = [
        {
            "name": "Tech Startup",
            "description": "Modern, innovative theme for technology companies",
            "category": ThemeCategory.TECHNOLOGY,
            "industry": "technology",
            "colors": {
                "mode": "light",
                "primary": "#6366f1",
                "secondary": "#8b5cf6",
                "accent": "#06b6d4",
                "success": "#10b981",
                "warning": "#f59e0b",
                "error": "#ef4444",
                "background": "#ffffff",
                "surface": "#fafbfe",
                "text": "#1e293b",
                "text_secondary": "#64748b"
            },
            "typography": {
                "primary_font": "Inter",
                "secondary_font": "JetBrains Mono",
                "font_scale": 0.95,
                "line_height": 1.5
            },
            "layout": {
                "border_radius": "6px",
                "spacing_scale": 1.1,
                "container_max_width": "1600px"
            },
            "has_dark_variant": True,
            "has_high_contrast_variant": True,
            "accessibility_score": 94,
            "tags": ["technology", "startup", "modern", "innovative"]
        }
    ]
    
    # Creative Templates
    creative_templates = [
        {
            "name": "Creative Studio",
            "description": "Vibrant, artistic theme for creative agencies",
            "category": ThemeCategory.CREATIVE,
            "industry": "creative",
            "colors": {
                "mode": "light",
                "primary": "#ec4899",
                "secondary": "#f97316",
                "accent": "#8b5cf6",
                "success": "#10b981",
                "warning": "#f59e0b",
                "error": "#ef4444",
                "background": "#fefefe",
                "surface": "#fdf4ff",
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
                "border_radius": "12px",
                "spacing_scale": 1.3,
                "container_max_width": "1600px"
            },
            "has_dark_variant": True,
            "has_high_contrast_variant": True,
            "accessibility_score": 89,
            "tags": ["creative", "artistic", "vibrant", "agency"]
        }
    ]
    
    # Finance Templates
    finance_templates = [
        {
            "name": "Financial Trust",
            "description": "Conservative, trustworthy theme for financial institutions",
            "category": ThemeCategory.FINANCE,
            "industry": "finance",
            "colors": {
                "mode": "light",
                "primary": "#065f46",
                "secondary": "#047857",
                "accent": "#1e40af",
                "success": "#059669",
                "warning": "#d97706",
                "error": "#dc2626",
                "background": "#ffffff",
                "surface": "#f7f9fa",
                "text": "#0f172a",
                "text_secondary": "#374151"
            },
            "typography": {
                "primary_font": "Inter",
                "secondary_font": "Georgia",
                "font_scale": 0.95,
                "line_height": 1.5
            },
            "layout": {
                "border_radius": "2px",
                "spacing_scale": 0.9,
                "container_max_width": "1200px"
            },
            "has_dark_variant": True,
            "has_high_contrast_variant": True,
            "accessibility_score": 99,
            "tags": ["finance", "banking", "conservative", "trust"]
        }
    ]
    
    # Accessibility Templates
    accessibility_templates = [
        {
            "name": "High Contrast Pro",
            "description": "High contrast theme optimized for accessibility",
            "category": ThemeCategory.ACCESSIBILITY,
            "industry": "universal",
            "colors": {
                "mode": "high_contrast",
                "primary": "#000000",
                "secondary": "#1a1a1a",
                "accent": "#0066cc",
                "success": "#008000",
                "warning": "#ff8c00",
                "error": "#cc0000",
                "background": "#ffffff",
                "surface": "#f5f5f5",
                "text": "#000000",
                "text_secondary": "#333333"
            },
            "typography": {
                "primary_font": "Inter",
                "secondary_font": "system-ui",
                "font_scale": 1.2,
                "line_height": 1.8,
                "font_weight": "600"
            },
            "layout": {
                "border_radius": "0px",
                "spacing_scale": 1.5,
                "container_max_width": "1200px",
                "border_width": "2px",
                "focus_ring_width": "4px"
            },
            "has_dark_variant": True,
            "has_high_contrast_variant": False,
            "accessibility_score": 100,
            "tags": ["accessibility", "high-contrast", "wcag", "inclusive"]
        }
    ]
    
    all_templates = (
        healthcare_templates + 
        corporate_templates + 
        technology_templates + 
        creative_templates + 
        finance_templates + 
        accessibility_templates
    )
    
    # Create template records
    for template_data in all_templates:
        existing = db.query(ThemeTemplate).filter(
            ThemeTemplate.name == template_data["name"]
        ).first()
        
        if not existing:
            template = ThemeTemplate(**template_data)
            db.add(template)
            print(f"Created template: {template_data['name']}")
        else:
            print(f"Template already exists: {template_data['name']}")
    
    db.commit()
    print(f"\nTemplate population complete! Created {len(all_templates)} templates.")


if __name__ == "__main__":
    create_theme_templates()
