"""
Advanced theme service with color intelligence, theme generation, and scheduling
"""

from datetime import datetime, time, timedelta
from typing import List, Dict, Optional, Tuple, Any
import colorsys
import re
import json
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.theme_management import OrganizationTheme, ThemeSchedule, ThemeTemplate, ThemeType, ThemeCategory


class ColorIntelligence:
    """Advanced color manipulation and theme generation"""
    
    @staticmethod
    def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB"""
        hex_color = hex_color.lstrip('#')
        rgb_values = [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]
        return (rgb_values[0], rgb_values[1], rgb_values[2])
    
    @staticmethod
    def rgb_to_hex(r: int, g: int, b: int) -> str:
        """Convert RGB to hex color"""
        return f"#{r:02x}{g:02x}{b:02x}"
    
    @staticmethod
    def rgb_to_hsl(r: int, g: int, b: int) -> Tuple[float, float, float]:
        """Convert RGB to HSL"""
        r_f, g_f, b_f = r/255.0, g/255.0, b/255.0
        return colorsys.rgb_to_hls(r_f, g_f, b_f)
    
    @staticmethod
    def hsl_to_rgb(h: float, s: float, l: float) -> Tuple[int, int, int]:
        """Convert HSL to RGB"""
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        return int(r * 255), int(g * 255), int(b * 255)
    
    @classmethod
    def generate_dark_variant(cls, hex_color: str) -> str:
        """Generate intelligent dark variant of a color"""
        r, g, b = cls.hex_to_rgb(hex_color)
        h, l, s = cls.rgb_to_hsl(r, g, b)
        
        # Intelligent dark conversion
        if l > 0.7:  # Very light colors
            new_l = 0.2 + (l - 0.7) * 0.3  # Map 0.7-1.0 to 0.2-0.35
        elif l > 0.5:  # Medium-light colors
            new_l = 0.15 + (l - 0.5) * 0.25  # Map 0.5-0.7 to 0.15-0.2
        elif l > 0.3:  # Medium colors
            new_l = 0.1 + (l - 0.3) * 0.25   # Map 0.3-0.5 to 0.1-0.15
        else:  # Already dark colors
            new_l = max(0.05, l * 0.5)  # Make even darker but not black
        
        # Increase saturation slightly for better contrast
        new_s = min(1.0, s * 1.2)
        
        r_new, g_new, b_new = cls.hsl_to_rgb(h, new_s, new_l)
        return cls.rgb_to_hex(r_new, g_new, b_new)
    
    @classmethod
    def generate_complementary_palette(cls, base_color: str, count: int = 5) -> List[str]:
        """Generate complementary color palette"""
        r, g, b = cls.hex_to_rgb(base_color)
        h, l, s = cls.rgb_to_hsl(r, g, b)
        
        colors = [base_color]
        
        # Generate variations
        for i in range(1, count):
            # Create variations in hue, saturation, and lightness
            if i == 1:  # Complementary
                new_h = (h + 0.5) % 1.0
                new_s = s * 0.8
                new_l = l * 1.1 if l < 0.5 else l * 0.9
            elif i == 2:  # Triadic 1
                new_h = (h + 0.33) % 1.0
                new_s = s * 0.9
                new_l = l
            elif i == 3:  # Triadic 2
                new_h = (h + 0.67) % 1.0
                new_s = s * 0.9
                new_l = l
            else:  # Analogous
                new_h = (h + (i - 3) * 0.08) % 1.0
                new_s = s * (0.8 + (i - 3) * 0.1)
                new_l = l * (0.9 + (i - 3) * 0.05)
            
            r_new, g_new, b_new = cls.hsl_to_rgb(new_h, new_s, new_l)
            colors.append(cls.rgb_to_hex(r_new, g_new, b_new))
        
        return colors
    
    @classmethod
    def generate_accessibility_colors(cls, base_color: str) -> Dict[str, str]:
        """Generate high contrast accessible color variants"""
        r, g, b = cls.hex_to_rgb(base_color)
        h, l, s = cls.rgb_to_hsl(r, g, b)
        
        # High contrast variants
        high_contrast_dark = cls.rgb_to_hex(*cls.hsl_to_rgb(h, min(1.0, s * 1.3), 0.1))
        high_contrast_light = cls.rgb_to_hex(*cls.hsl_to_rgb(h, s * 0.8, 0.95))
        
        # Text colors that meet WCAG AA standards
        text_on_light = "#1a1a1a"  # Very dark gray
        text_on_dark = "#f5f5f5"   # Very light gray
        
        return {
            "high_contrast_dark": high_contrast_dark,
            "high_contrast_light": high_contrast_light,
            "accessible_text_dark": text_on_light,
            "accessible_text_light": text_on_dark,
            "focus_ring": cls.rgb_to_hex(*cls.hsl_to_rgb(h, 1.0, 0.5))  # Full saturation
        }


class ThemeGenerator:
    """Advanced theme generation algorithms"""
    
    @staticmethod
    def generate_industry_theme(industry: str, base_colors: List[str]) -> Dict[str, Any]:
        """Generate industry-specific theme configuration"""
        
        industry_configs = {
            "healthcare": {
                "primary_index": 0,  # Use first color as primary
                "accent_style": "calming",
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
                }
            },
            "corporate": {
                "primary_index": 0,
                "accent_style": "professional",
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
                }
            },
            "creative": {
                "primary_index": 0,
                "accent_style": "vibrant",
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
                }
            },
            "technology": {
                "primary_index": 0,
                "accent_style": "modern",
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
                }
            },
            "finance": {
                "primary_index": 0,
                "accent_style": "conservative",
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
                }
            }
        }
        
        config = industry_configs.get(industry, industry_configs["corporate"])
        
        # Build color palette
        primary_color = base_colors[config["primary_index"]]
        color_palette = ColorIntelligence.generate_complementary_palette(primary_color, 5)
        
        return {
            "colors": {
                "mode": "light",
                "primary": primary_color,
                "secondary": color_palette[1] if len(color_palette) > 1 else primary_color,
                "accent": color_palette[2] if len(color_palette) > 2 else primary_color,
                "success": "#10b981",
                "warning": "#f59e0b", 
                "error": "#ef4444",
                "background": "#ffffff",
                "surface": "#f8fafc",
                "text": "#1e293b",
                "text_secondary": "#64748b"
            },
            "typography": config["typography"],
            "layout": config["layout"]
        }
    
    @staticmethod
    def generate_accessibility_theme(base_theme: Dict[str, Any]) -> Dict[str, Any]:
        """Generate high contrast accessibility version of theme"""
        colors = base_theme.get("colors", {})
        primary = colors.get("primary", "#3b82f6")
        
        accessibility_colors = ColorIntelligence.generate_accessibility_colors(primary)
        
        return {
            "colors": {
                "mode": "high_contrast",
                "primary": accessibility_colors["high_contrast_dark"],
                "secondary": accessibility_colors["high_contrast_dark"], 
                "accent": accessibility_colors["focus_ring"],
                "success": "#065f46",  # Dark green
                "warning": "#92400e",  # Dark orange
                "error": "#991b1b",    # Dark red
                "background": "#ffffff",
                "surface": "#f9fafb",
                "text": accessibility_colors["accessible_text_dark"],
                "text_secondary": "#374151"
            },
            "typography": {
                **base_theme.get("typography", {}),
                "font_scale": 1.2,  # Larger text
                "line_height": 1.8,  # More line spacing
                "font_weight": "600"  # Bolder text
            },
            "layout": {
                **base_theme.get("layout", {}),
                "spacing_scale": 1.5,  # More spacing
                "border_width": "2px",  # Thicker borders
                "focus_ring_width": "3px"  # Prominent focus
            },
            "accessibility": {
                "high_contrast": True,
                "large_text": True,
                "reduced_motion": True,
                "focus_indicators": "enhanced"
            }
        }


class ThemeService:
    """Advanced theme management service"""
    
    def __init__(self, db: Session):
        self.db = db
        self.color_intelligence = ColorIntelligence()
        self.theme_generator = ThemeGenerator()
    
    def create_custom_theme(
        self, 
        organization_id: int,
        name: str,
        colors: Dict[str, Any],
        typography: Optional[Dict[str, Any]] = None,
        layout: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        category: Optional[str] = None
    ) -> OrganizationTheme:
        """Create a new custom theme"""
        
        # Generate dark variant automatically
        if colors.get("mode") != "dark" and colors.get("primary"):
            dark_colors = self._generate_dark_theme_colors(colors)
            colors["dark_variant"] = dark_colors
        
        theme = OrganizationTheme(
            organization_id=organization_id,
            name=name,
            description=description,
            theme_type=ThemeType.CUSTOM,
            category=category,
            colors=colors,
            typography=typography or {},
            layout=layout or {}
        )
        
        self.db.add(theme)
        self.db.commit()
        self.db.refresh(theme)
        
        return theme
    
    def generate_theme_from_industry(
        self,
        organization_id: int,
        industry: str,
        base_colors: List[str],
        name: Optional[str] = None
    ) -> OrganizationTheme:
        """Generate theme based on industry best practices"""
        
        theme_config = self.theme_generator.generate_industry_theme(industry, base_colors)
        
        # Generate dark variant
        dark_colors = self._generate_dark_theme_colors(theme_config["colors"])
        theme_config["colors"]["dark_variant"] = dark_colors
        
        theme_name = name or f"{industry.title()} Theme"
        
        theme = OrganizationTheme(
            organization_id=organization_id,
            name=theme_name,
            description=f"Auto-generated {industry} industry theme",
            theme_type=ThemeType.GENERATED,
            category=industry,
            colors=theme_config["colors"],
            typography=theme_config["typography"],
            layout=theme_config["layout"],
            generation_algorithm="industry_based"
        )
        
        self.db.add(theme)
        self.db.commit()
        self.db.refresh(theme)
        
        return theme
    
    def generate_accessibility_variant(
        self, 
        theme_id: int,
        organization_id: int
    ) -> OrganizationTheme:
        """Generate high contrast accessibility variant of existing theme"""
        
        base_theme = self.db.query(OrganizationTheme).filter(
            OrganizationTheme.id == theme_id,
            OrganizationTheme.organization_id == organization_id
        ).first()
        
        if not base_theme:
            raise ValueError("Base theme not found")
        
        # Generate accessibility theme
        accessibility_config = self.theme_generator.generate_accessibility_theme({
            "colors": base_theme.colors,
            "typography": base_theme.typography,
            "layout": base_theme.layout
        })
        
        accessibility_theme = OrganizationTheme(
            organization_id=organization_id,
            name=f"{base_theme.name} (High Contrast)",
            description=f"High contrast accessibility variant of {base_theme.name}",
            theme_type=ThemeType.GENERATED,
            category=ThemeCategory.ACCESSIBILITY,
            colors=accessibility_config["colors"],
            typography=accessibility_config["typography"],
            layout=accessibility_config["layout"],
            source_theme_id=theme_id,
            generation_algorithm="accessibility_variant",
            high_contrast=True,
            large_text=True,
            reduced_motion=True
        )
        
        self.db.add(accessibility_theme)
        self.db.commit()
        self.db.refresh(accessibility_theme)
        
        return accessibility_theme
    
    def create_theme_schedule(
        self,
        organization_id: int,
        theme_id: int,
        name: str,
        start_time: time,
        end_time: time,
        days_of_week: List[int],
        priority: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> ThemeSchedule:
        """Create a theme schedule"""
        
        schedule = ThemeSchedule(
            organization_id=organization_id,
            theme_id=theme_id,
            name=name,
            start_time=start_time,
            end_time=end_time,
            days_of_week=days_of_week,
            priority=priority,
            start_date=start_date,
            end_date=end_date
        )
        
        self.db.add(schedule)
        self.db.commit()
        self.db.refresh(schedule)
        
        return schedule
    
    def get_active_theme_for_time(
        self, 
        organization_id: int,
        check_time: Optional[datetime] = None
    ) -> Optional[OrganizationTheme]:
        """Get the theme that should be active at a specific time"""
        
        if check_time is None:
            check_time = datetime.now()
        
        current_time = check_time.time()
        current_day = check_time.weekday()  # 0 = Monday
        
        # For now, return the default active theme
        # TODO: Implement full scheduling logic with proper time comparison
        return self.db.query(OrganizationTheme).filter(
            OrganizationTheme.organization_id == organization_id,
            OrganizationTheme.is_active == True
        ).first()
    
    def _generate_dark_theme_colors(self, light_colors: Dict[str, Any]) -> Dict[str, Any]:
        """Generate dark variant of light theme colors"""
        dark_colors = {"mode": "dark"}
        
        color_mappings = {
            "primary": light_colors.get("primary"),
            "secondary": light_colors.get("secondary"), 
            "accent": light_colors.get("accent")
        }
        
        # Generate dark variants for main colors
        for key, color in color_mappings.items():
            if color:
                dark_colors[key] = self.color_intelligence.generate_dark_variant(color)
        
        # Dark theme specific colors
        dark_colors.update({
            "background": "#0f172a",
            "surface": "#1e293b", 
            "text": "#f1f5f9",
            "text_secondary": "#94a3b8",
            "success": "#22c55e",
            "warning": "#eab308",
            "error": "#ef4444"
        })
        
        return dark_colors
    
    def get_organization_themes(self, organization_id: int) -> List[OrganizationTheme]:
        """Get all themes for organization"""
        return self.db.query(OrganizationTheme).filter(
            OrganizationTheme.organization_id == organization_id
        ).order_by(OrganizationTheme.created_at.desc()).all()
    
    def get_theme_templates(self, category: Optional[str] = None) -> List[ThemeTemplate]:
        """Get available theme templates"""
        query = self.db.query(ThemeTemplate)
        
        if category:
            query = query.filter(ThemeTemplate.category == category)
        
        return query.order_by(ThemeTemplate.popularity_score.desc()).all()
    
    def apply_theme_template(
        self,
        organization_id: int,
        template_id: int,
        custom_name: Optional[str] = None
    ) -> OrganizationTheme:
        """Apply a theme template to organization"""
        
        template = self.db.query(ThemeTemplate).filter(
            ThemeTemplate.id == template_id
        ).first()
        
        if not template:
            raise ValueError("Template not found")
        
        theme_name = custom_name or f"{template.name} (Custom)"
        
        # Convert template colors to dict and generate dark variant
        template_colors = template.colors if isinstance(template.colors, dict) else {}
        dark_colors = self._generate_dark_theme_colors(template_colors)
        colors_with_dark = {**template_colors, "dark_variant": dark_colors}
        
        theme = OrganizationTheme(
            organization_id=organization_id,
            name=theme_name,
            description=f"Based on {template.name} template",
            theme_type=ThemeType.TEMPLATE,
            category=template.category,
            colors=colors_with_dark,
            typography=template.typography if isinstance(template.typography, dict) else {},
            layout=template.layout if isinstance(template.layout, dict) else {},
            custom_css=template.custom_css
        )
        
        self.db.add(theme)
        self.db.commit()
        self.db.refresh(theme)
        
        # Update template popularity using SQL update
        self.db.query(ThemeTemplate).filter(
            ThemeTemplate.id == template_id
        ).update({
            ThemeTemplate.popularity_score: ThemeTemplate.popularity_score + 1
        })
        self.db.commit()
        
        return theme
