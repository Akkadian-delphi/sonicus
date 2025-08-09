"""
Organization branding management endpoints
Handles logo upload, color customization, theme presets, and branding configuration
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import os
import uuid
from PIL import Image

from app.db.session import get_db
from app.core.auth_dependencies import get_current_user
from app.core.tenant_middleware import get_current_tenant
from app.models.organization import Organization
from app.models.organization_branding import OrganizationBranding
from app.schemas.organization_branding import (
    OrganizationBrandingCreate,
    OrganizationBrandingUpdate,
    OrganizationBrandingResponse,
    LogoUploadResponse,
    BrandingPreviewRequest,
    BrandingThemePreset
)

router = APIRouter(prefix="/organization/branding", tags=["Organization Branding"])


@router.get("/", response_model=OrganizationBrandingResponse)
def get_organization_branding(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_info: dict = Depends(get_current_tenant)
):
    """Get current organization branding configuration"""
    organization_id = tenant_info.get("organization_id")
    if not organization_id:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    branding = db.query(OrganizationBranding).filter(
        OrganizationBranding.organization_id == organization_id
    ).first()
    
    if not branding:
        # Return default branding if none exists
        default_branding = OrganizationBranding.get_default_branding()
        return OrganizationBrandingResponse(
            id=0,
            organization_id=organization_id,
            logo_url=None,
            favicon_url=None,
            colors={k: v for k, v in default_branding["colors"].items()},
            typography={k: v for k, v in default_branding["typography"].items()},
            layout=default_branding["layout"],
            custom_css=None,
            is_active=True,
            updated_at=None
        )
    
    return OrganizationBrandingResponse.from_orm(branding)


@router.post("/", response_model=OrganizationBrandingResponse)
def create_organization_branding(
    branding_data: OrganizationBrandingCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_info: dict = Depends(get_current_tenant)
):
    """Create or update organization branding configuration"""
    organization_id = tenant_info.get("organization_id")
    if not organization_id:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Check if branding already exists
    existing_branding = db.query(OrganizationBranding).filter(
        OrganizationBranding.organization_id == organization_id
    ).first()
    
    if existing_branding:
        # Update existing branding
        update_data = branding_data.dict(exclude_unset=True)
        
        # Handle nested objects
        if 'colors' in update_data:
            colors = update_data.pop('colors')
            for key, value in colors.items():
                if hasattr(existing_branding, f"{key}_color"):
                    setattr(existing_branding, f"{key}_color", value)
        
        if 'typography' in update_data:
            typography = update_data.pop('typography')
            for key, value in typography.items():
                if hasattr(existing_branding, key):
                    setattr(existing_branding, key, value)
        
        if 'layout' in update_data:
            layout = update_data.pop('layout')
            for key, value in layout.items():
                if hasattr(existing_branding, key):
                    setattr(existing_branding, key, value)
        
        # Update other fields
        for key, value in update_data.items():
            if hasattr(existing_branding, key):
                setattr(existing_branding, key, value)
        
        db.commit()
        db.refresh(existing_branding)
        return OrganizationBrandingResponse.from_orm(existing_branding)
    else:
        # Create new branding
        branding = OrganizationBranding(
            organization_id=organization_id,
            logo_url=branding_data.logo_url,
            favicon_url=branding_data.favicon_url,
            custom_css=branding_data.custom_css
        )
        
        # Set colors
        if branding_data.colors:
            if branding_data.colors.primary is not None:
                branding.primary_color = branding_data.colors.primary  # type: ignore
            if branding_data.colors.secondary is not None:
                branding.secondary_color = branding_data.colors.secondary  # type: ignore
            if branding_data.colors.accent is not None:
                branding.accent_color = branding_data.colors.accent  # type: ignore
            if branding_data.colors.background is not None:
                branding.background_color = branding_data.colors.background  # type: ignore
            if branding_data.colors.text is not None:
                branding.text_color = branding_data.colors.text  # type: ignore
        
        # Set typography
        if branding_data.typography:
            if branding_data.typography.font_family is not None:
                branding.font_family = branding_data.typography.font_family  # type: ignore
            if branding_data.typography.heading_font is not None:
                branding.heading_font = branding_data.typography.heading_font  # type: ignore
        
        # Set layout
        if branding_data.layout:
            if branding_data.layout.sidebar_style is not None:
                branding.sidebar_style = branding_data.layout.sidebar_style  # type: ignore
            if branding_data.layout.theme_mode is not None:
                branding.theme_mode = branding_data.layout.theme_mode  # type: ignore
        
        db.add(branding)
        db.commit()
        db.refresh(branding)
        return OrganizationBrandingResponse.from_orm(branding)


@router.put("/", response_model=OrganizationBrandingResponse)
def update_organization_branding(
    branding_data: OrganizationBrandingUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_info: dict = Depends(get_current_tenant)
):
    """Update organization branding configuration"""
    organization_id = tenant_info.get("organization_id")
    if not organization_id:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    branding = db.query(OrganizationBranding).filter(
        OrganizationBranding.organization_id == organization_id
    ).first()
    
    if not branding:
        raise HTTPException(status_code=404, detail="Organization branding not found")
    
    update_data = branding_data.dict(exclude_unset=True)
    
    # Handle nested objects
    if 'colors' in update_data:
        colors = update_data.pop('colors')
        for key, value in colors.items():
            if hasattr(branding, f"{key}_color"):
                setattr(branding, f"{key}_color", value)
    
    if 'typography' in update_data:
        typography = update_data.pop('typography')
        for key, value in typography.items():
            if hasattr(branding, key):
                setattr(branding, key, value)
    
    if 'layout' in update_data:
        layout = update_data.pop('layout')
        for key, value in layout.items():
            if hasattr(branding, key):
                setattr(branding, key, value)
    
    # Update other fields
    for key, value in update_data.items():
        if hasattr(branding, key):
            setattr(branding, key, value)
    
    db.commit()
    db.refresh(branding)
    return OrganizationBrandingResponse.from_orm(branding)


@router.post("/upload-logo", response_model=LogoUploadResponse)
async def upload_logo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_info: dict = Depends(get_current_tenant)
):
    """Upload organization logo"""
    organization_id = tenant_info.get("organization_id")
    if not organization_id:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/svg+xml"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file.content_type} not allowed. Allowed types: {allowed_types}"
        )
    
    # Validate file size (max 5MB)
    max_size = 5 * 1024 * 1024  # 5MB
    contents = await file.read()
    if len(contents) > max_size:
        raise HTTPException(status_code=400, detail="File size too large. Maximum 5MB allowed.")
    
    # Create upload directory
    upload_dir = f"uploads/organizations/{organization_id}/branding"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    filename = file.filename or "unknown"
    file_extension = os.path.splitext(filename)[1]
    unique_filename = f"logo_{uuid.uuid4().hex}{file_extension}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    try:
        # Save file
        with open(file_path, "wb") as buffer:
            buffer.write(contents)
        
        # For non-SVG images, create optimized version
        if file.content_type != "image/svg+xml":
            await optimize_image(file_path)
        
        # Generate URL
        logo_url = f"/uploads/organizations/{organization_id}/branding/{unique_filename}"
        
        # Update branding record
        branding = db.query(OrganizationBranding).filter(
            OrganizationBranding.organization_id == organization_id
        ).first()
        
        if branding:
            # Remove old logo file if exists
            if branding.logo_url:  # type: ignore
                old_path = f"uploads{branding.logo_url}"
                if os.path.exists(old_path):
                    os.remove(old_path)
            
            branding.logo_url = logo_url  # type: ignore
            branding.logo_filename = file.filename  # type: ignore
        else:
            # Create new branding record
            branding = OrganizationBranding(
                organization_id=organization_id,
                logo_url=logo_url,
                logo_filename=file.filename
            )
            db.add(branding)
        
        db.commit()
        
        return LogoUploadResponse(
            success=True,
            message="Logo uploaded successfully",
            logo_url=logo_url,
            filename=unique_filename
        )
    
    except Exception as e:
        # Clean up file if upload failed
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Failed to upload logo: {str(e)}")


@router.delete("/logo")
def delete_logo(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_info: dict = Depends(get_current_tenant)
):
    """Delete organization logo"""
    organization_id = tenant_info.get("organization_id")
    if not organization_id:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    branding = db.query(OrganizationBranding).filter(
        OrganizationBranding.organization_id == organization_id
    ).first()
    
    if not branding or not branding.logo_url:  # type: ignore
        raise HTTPException(status_code=404, detail="Logo not found")
    
    # Remove file
    file_path = f"uploads{branding.logo_url}"
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # Update database
    branding.logo_url = None  # type: ignore
    branding.logo_filename = None  # type: ignore
    db.commit()
    
    return {"success": True, "message": "Logo deleted successfully"}


@router.get("/presets")
def get_branding_presets():
    """Get available branding theme presets"""
    return BrandingThemePreset.get_presets()


@router.post("/preview")
def preview_branding(
    preview_data: BrandingPreviewRequest,
    current_user: dict = Depends(get_current_user)
):
    """Generate CSS preview for branding changes"""
    css_vars = []
    
    if preview_data.colors:
        colors = preview_data.colors.dict(exclude_unset=True)
        for key, value in colors.items():
            if value:
                css_vars.append(f"--color-{key.replace('_', '-')}: {value};")
    
    if preview_data.typography:
        typography = preview_data.typography.dict(exclude_unset=True)
        for key, value in typography.items():
            if value:
                css_var_name = key.replace('_', '-')
                css_vars.append(f"--font-{css_var_name}: {value};")
    
    css_preview = f"""
    :root {{
        {' '.join(css_vars)}
    }}
    
    .org-branded {{
        background-color: var(--color-background, #ffffff);
        color: var(--color-text, #333333);
        font-family: var(--font-font-family, 'Inter, sans-serif');
    }}
    
    .org-branded h1, .org-branded h2, .org-branded h3 {{
        font-family: var(--font-heading-font, var(--font-font-family, 'Inter, sans-serif'));
    }}
    
    .btn-primary {{
        background-color: var(--color-primary, #3B82F6);
        border-color: var(--color-primary, #3B82F6);
    }}
    
    .btn-secondary {{
        background-color: var(--color-secondary, #64748B);
        border-color: var(--color-secondary, #64748B);
    }}
    
    .accent {{
        color: var(--color-accent, #10B981);
    }}
    
    {preview_data.custom_css or ''}
    """
    
    return {
        "css": css_preview,
        "variables": dict(zip([var.split(':')[0].strip() for var in css_vars], 
                            [var.split(':')[1].strip().rstrip(';') for var in css_vars]))
    }


async def optimize_image(file_path: str, max_width: int = 300, max_height: int = 300, quality: int = 85):
    """Optimize uploaded image for web use"""
    try:
        with Image.open(file_path) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Resize if too large
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # Save optimized version
            img.save(file_path, 'JPEG', quality=quality, optimize=True)
    except Exception as e:
        # If optimization fails, keep original file
        pass
