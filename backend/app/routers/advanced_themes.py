"""
Advanced theme management API router
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, time
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.auth_dependencies import get_current_user
from app.core.tenant_middleware import get_current_tenant
from app.db.session import get_db
from app.services.advanced_theme_service import ThemeService
from app.models.theme_management import OrganizationTheme, ThemeSchedule, ThemeTemplate


router = APIRouter(prefix="/api/themes", tags=["Advanced Themes"])


# Pydantic schemas
class ThemeColorSchema(BaseModel):
    mode: str = "light"
    primary: str
    secondary: Optional[str] = None
    accent: Optional[str] = None
    success: Optional[str] = "#10b981"
    warning: Optional[str] = "#f59e0b"
    error: Optional[str] = "#ef4444"
    background: Optional[str] = "#ffffff"
    surface: Optional[str] = "#f8fafc"
    text: Optional[str] = "#1e293b"
    text_secondary: Optional[str] = "#64748b"


class ThemeTypographySchema(BaseModel):
    primary_font: Optional[str] = "Inter"
    secondary_font: Optional[str] = "system-ui"
    font_scale: Optional[float] = 1.0
    line_height: Optional[float] = 1.5
    font_weight: Optional[str] = "400"


class ThemeLayoutSchema(BaseModel):
    border_radius: Optional[str] = "8px"
    spacing_scale: Optional[float] = 1.0
    container_max_width: Optional[str] = "1200px"
    border_width: Optional[str] = "1px"
    focus_ring_width: Optional[str] = "2px"


class CreateThemeRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    colors: ThemeColorSchema
    typography: Optional[ThemeTypographySchema] = None
    layout: Optional[ThemeLayoutSchema] = None
    category: Optional[str] = None


class GenerateIndustryThemeRequest(BaseModel):
    industry: str = Field(..., description="Industry type: healthcare, corporate, creative, technology, finance")
    base_colors: List[str] = Field(..., min_length=1, description="Base hex colors for theme generation")
    name: Optional[str] = None


class CreateScheduleRequest(BaseModel):
    theme_id: int
    name: str = Field(..., min_length=1, max_length=255)
    start_time: str = Field(..., description="Start time in HH:MM format")
    end_time: str = Field(..., description="End time in HH:MM format")  
    days_of_week: List[int] = Field(..., description="Days of week (0=Monday, 6=Sunday)")
    priority: Optional[int] = 0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class ThemeResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    theme_type: str
    category: Optional[str]
    colors: Dict[str, Any]
    typography: Optional[Dict[str, Any]]
    layout: Optional[Dict[str, Any]]
    custom_css: Optional[str]
    is_active: bool
    is_favorite: bool
    high_contrast: bool
    large_text: bool
    reduced_motion: bool
    usage_count: int
    created_at: Optional[str]
    last_used_at: Optional[str]

    class Config:
        from_attributes = True


class ScheduleResponse(BaseModel):
    id: int
    name: str
    theme_id: int
    is_active: bool
    start_time: str
    end_time: str
    days_of_week: List[int]
    start_date: Optional[str]
    end_date: Optional[str]
    priority: int
    created_at: Optional[str]

    class Config:
        from_attributes = True


class TemplateResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    category: str
    industry: Optional[str]
    colors: Dict[str, Any]
    typography: Optional[Dict[str, Any]]
    layout: Optional[Dict[str, Any]]
    custom_css: Optional[str]
    is_premium: bool
    tags: Optional[List[str]]
    preview_image_url: Optional[str]
    has_dark_variant: bool
    has_high_contrast_variant: bool
    accessibility_score: Optional[int]
    popularity_score: int
    created_at: Optional[str]

    class Config:
        from_attributes = True


# API Endpoints

@router.get("/", response_model=List[ThemeResponse])
def get_organization_themes(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_info: dict = Depends(get_current_tenant)
):
    """Get all themes for the organization"""
    organization_id = tenant_info["organization_id"]
    theme_service = ThemeService(db)
    themes = theme_service.get_organization_themes(organization_id)
    return [ThemeResponse.model_validate(theme.to_dict()) for theme in themes]


@router.post("/", response_model=ThemeResponse)
def create_custom_theme(
    request: CreateThemeRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_info: dict = Depends(get_current_tenant)
):
    """Create a new custom theme"""
    organization_id = tenant_info["organization_id"]
    theme_service = ThemeService(db)
    
    try:
        theme = theme_service.create_custom_theme(
            organization_id=organization_id,
            name=request.name,
            colors=request.colors.model_dump(),
            typography=request.typography.model_dump() if request.typography else None,
            layout=request.layout.model_dump() if request.layout else None,
            description=request.description,
            category=request.category
        )
        return ThemeResponse.model_validate(theme.to_dict())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/generate/industry", response_model=ThemeResponse)
def generate_industry_theme(
    request: GenerateIndustryThemeRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_info: dict = Depends(get_current_tenant)
):
    """Generate theme based on industry best practices"""
    organization_id = tenant_info["organization_id"]
    theme_service = ThemeService(db)
    
    try:
        theme = theme_service.generate_theme_from_industry(
            organization_id=organization_id,
            industry=request.industry,
            base_colors=request.base_colors,
            name=request.name
        )
        return ThemeResponse.model_validate(theme.to_dict())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{theme_id}/accessibility", response_model=ThemeResponse)
def generate_accessibility_variant(
    theme_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_info: dict = Depends(get_current_tenant)
):
    """Generate high contrast accessibility variant of existing theme"""
    organization_id = tenant_info["organization_id"]
    theme_service = ThemeService(db)
    
    try:
        theme = theme_service.generate_accessibility_variant(
            theme_id=theme_id,
            organization_id=organization_id
        )
        return ThemeResponse.model_validate(theme.to_dict())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{theme_id}/activate")
def activate_theme(
    theme_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_info: dict = Depends(get_current_tenant)
):
    """Activate a theme for the organization"""
    organization_id = tenant_info["organization_id"]
    
    # Deactivate all other themes using SQL update
    db.query(OrganizationTheme).filter(
        OrganizationTheme.organization_id == organization_id
    ).update({"is_active": False})
    
    # Activate the selected theme using SQL update
    theme_updated = db.query(OrganizationTheme).filter(
        OrganizationTheme.id == theme_id,
        OrganizationTheme.organization_id == organization_id
    ).update({
        "is_active": True,
        "last_used_at": datetime.utcnow(),
        "usage_count": OrganizationTheme.usage_count + 1
    })
    
    if not theme_updated:
        raise HTTPException(status_code=404, detail="Theme not found")
    
    db.commit()
    
    return {"message": "Theme activated successfully"}


@router.delete("/{theme_id}")
def delete_theme(
    theme_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_info: dict = Depends(get_current_tenant)
):
    """Delete a custom theme"""
    organization_id = tenant_info["organization_id"]
    
    theme = db.query(OrganizationTheme).filter(
        OrganizationTheme.id == theme_id,
        OrganizationTheme.organization_id == organization_id
    ).first()
    
    if not theme:
        raise HTTPException(status_code=404, detail="Theme not found")
    
    # Check if theme is active using a separate query
    active_check = db.query(OrganizationTheme.is_active).filter(
        OrganizationTheme.id == theme_id
    ).scalar()
    
    if active_check:
        raise HTTPException(status_code=400, detail="Cannot delete active theme")
    
    db.delete(theme)
    db.commit()
    
    return {"message": "Theme deleted successfully"}


# Theme Scheduling Endpoints

@router.get("/schedules", response_model=List[ScheduleResponse])
def get_theme_schedules(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_info: dict = Depends(get_current_tenant)
):
    """Get all theme schedules for organization"""
    organization_id = tenant_info["organization_id"]
    
    schedules = db.query(ThemeSchedule).filter(
        ThemeSchedule.organization_id == organization_id
    ).order_by(ThemeSchedule.priority.desc()).all()
    
    return [ScheduleResponse.model_validate(schedule.to_dict()) for schedule in schedules]


@router.post("/schedules", response_model=ScheduleResponse)
def create_theme_schedule(
    request: CreateScheduleRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_info: dict = Depends(get_current_tenant)
):
    """Create a new theme schedule"""
    organization_id = tenant_info["organization_id"]
    theme_service = ThemeService(db)
    
    try:
        # Parse time strings
        start_time_obj = datetime.strptime(request.start_time, "%H:%M").time()
        end_time_obj = datetime.strptime(request.end_time, "%H:%M").time()
        
        schedule = theme_service.create_theme_schedule(
            organization_id=organization_id,
            theme_id=request.theme_id,
            name=request.name,
            start_time=start_time_obj,
            end_time=end_time_obj,
            days_of_week=request.days_of_week,
            priority=request.priority or 0,
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        return ScheduleResponse.model_validate(schedule.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid time format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/active")
def get_current_active_theme(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_info: dict = Depends(get_current_tenant)
):
    """Get the theme that should be active right now based on schedules"""
    organization_id = tenant_info["organization_id"]
    theme_service = ThemeService(db)
    active_theme = theme_service.get_active_theme_for_time(organization_id)
    
    if not active_theme:
        raise HTTPException(status_code=404, detail="No active theme found")
    
    return ThemeResponse.model_validate(active_theme.to_dict())


# Theme Templates Endpoints

@router.get("/templates", response_model=List[TemplateResponse])
def get_theme_templates(
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get available theme templates"""
    theme_service = ThemeService(db)
    templates = theme_service.get_theme_templates(category)
    return [TemplateResponse.model_validate(template.to_dict()) for template in templates]


@router.post("/templates/{template_id}/apply", response_model=ThemeResponse)
def apply_theme_template(
    template_id: int,
    custom_name: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_info: dict = Depends(get_current_tenant)
):
    """Apply a theme template to organization"""
    organization_id = tenant_info["organization_id"]
    theme_service = ThemeService(db)
    
    try:
        theme = theme_service.apply_theme_template(
            organization_id=organization_id,
            template_id=template_id,
            custom_name=custom_name
        )
        return ThemeResponse.model_validate(theme.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Color Intelligence Endpoints

@router.post("/colors/analyze")
def analyze_color_palette(
    colors: List[str],
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_info: dict = Depends(get_current_tenant)
):
    """Analyze color palette and generate suggestions"""
    from app.services.advanced_theme_service import ColorIntelligence
    
    if not colors:
        raise HTTPException(status_code=400, detail="At least one color required")
    
    primary_color = colors[0]
    
    try:
        # Generate complementary palette
        complementary = ColorIntelligence.generate_complementary_palette(primary_color, 5)
        
        # Generate dark variants
        dark_variants = [ColorIntelligence.generate_dark_variant(color) for color in colors]
        
        # Generate accessibility colors
        accessibility = ColorIntelligence.generate_accessibility_colors(primary_color)
        
        return {
            "original_colors": colors,
            "complementary_palette": complementary,
            "dark_variants": dark_variants,
            "accessibility_colors": accessibility
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Color analysis failed: {str(e)}")


@router.post("/preview")
def generate_theme_preview(
    colors: ThemeColorSchema,
    typography: Optional[ThemeTypographySchema] = None,
    layout: Optional[ThemeLayoutSchema] = None
):
    """Generate CSS preview for theme configuration"""
    
    css_vars = []
    
    # Color variables
    for key, value in colors.model_dump().items():
        if value and key != "mode":
            css_vars.append(f"  --color-{key.replace('_', '-')}: {value};")
    
    # Typography variables
    if typography:
        for key, value in typography.model_dump().items():
            if value is not None:
                css_vars.append(f"  --typography-{key.replace('_', '-')}: {value};")
    
    # Layout variables  
    if layout:
        for key, value in layout.model_dump().items():
            if value is not None:
                css_vars.append(f"  --layout-{key.replace('_', '-')}: {value};")
    
    css_preview = ":root {\n" + "\n".join(css_vars) + "\n}"
    
    return {"css_preview": css_preview}
