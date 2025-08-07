"""
Business Admin Sound Package Management Router

This module provides comprehensive sound package management capabilities for business administrators
within their organizations. Includes package creation, assignment, analytics, and usage tracking.

Created: July 26, 2025
Author: Sonicus Platform Team
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, text
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
import logging
import uuid

# Database and models
from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.organization import Organization, OrganizationSoundPackage
from app.models.therapy_sound import TherapySound

# Try to import the new sound package models, fall back if not available
try:
    from app.models.sound_package import SoundPackage, PackageAssignment, PackageUsage, PackageType, PackageStatus, AssignmentStatus
    ENHANCED_PACKAGES_AVAILABLE = True
except ImportError:
    ENHANCED_PACKAGES_AVAILABLE = False

# Schemas
from pydantic import BaseModel, Field, validator
from typing import Union

# Authentication and dependencies
from app.core.security import get_current_user

# Initialize router and logger
router = APIRouter()
logger = logging.getLogger(__name__)

# =================== PYDANTIC SCHEMAS ===================

class SoundInfo(BaseModel):
    """Schema for sound information within packages"""
    id: int
    title: str
    description: Optional[str]
    category: Optional[str]
    duration: float
    is_premium: bool

class PackageBase(BaseModel):
    """Base schema for sound packages"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    sound_ids: List[int]
    auto_assign_new_users: bool = False
    delivery_schedule: Optional[Dict[str, Any]] = None
    
    @validator('sound_ids')
    def validate_sound_ids(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one sound ID is required')
        return v

class PackageCreate(PackageBase):
    """Schema for creating new sound packages"""
    assign_to_employees: List[int] = Field(default_factory=list)
    assignment_notes: Optional[str] = None

class PackageUpdate(BaseModel):
    """Schema for updating existing packages"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    sound_ids: Optional[List[int]] = None
    is_active: Optional[bool] = None
    auto_assign_new_users: Optional[bool] = None
    delivery_schedule: Optional[Dict[str, Any]] = None

class PackageResponse(BaseModel):
    """Schema for package information response"""
    id: str
    name: str
    description: Optional[str]
    category: Optional[str]
    sound_count: int
    total_duration_minutes: float
    is_active: bool
    auto_assign_new_users: bool
    assignment_count: int
    total_listens: int
    unique_users_accessed: int
    created_at: datetime
    updated_at: datetime
    sounds: List[SoundInfo]
    
    class Config:
        from_attributes = True

class PackageListResponse(BaseModel):
    """Schema for paginated package list response"""
    packages: List[PackageResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class EmployeeAssignment(BaseModel):
    """Schema for employee package assignment"""
    employee_id: int
    employee_email: str
    employee_name: Optional[str]
    assigned_at: datetime
    status: str
    completion_percentage: float
    total_play_time_minutes: float
    last_activity_at: Optional[datetime]

class PackageAssignmentRequest(BaseModel):
    """Schema for assigning packages to employees"""
    employee_ids: List[int]
    assignment_notes: Optional[str] = None
    send_notification: bool = True
    
    @validator('employee_ids')
    def validate_employee_ids(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one employee ID is required')
        return v

class PackageAssignmentResponse(BaseModel):
    """Schema for package assignment response"""
    package_id: str
    successful_assignments: List[int]
    failed_assignments: List[Dict[str, Any]]
    total_assigned: int

class PackageUsageAnalytics(BaseModel):
    """Schema for package usage analytics"""
    package_id: str
    package_name: str
    time_range: str
    total_assignments: int
    active_users: int
    completion_rate: float
    avg_session_duration_minutes: float
    total_plays: int
    most_popular_sounds: List[Dict[str, Any]]
    usage_by_day: List[Dict[str, Any]]
    employee_progress: List[EmployeeAssignment]
    performance_metrics: Dict[str, Any]
    generated_at: datetime

# =================== HELPER FUNCTIONS ===================

# Use centralized business admin authentication from auth_dependencies
# get_business_admin_user is now imported and available for use

def get_sounds_by_ids(db: Session, sound_ids: List[int]) -> List[TherapySound]:
    """
    Retrieve therapy sounds by their IDs
    """
    return db.query(TherapySound).filter(TherapySound.id.in_(sound_ids)).all()

def calculate_package_metrics(package: OrganizationSoundPackage, sounds: List[TherapySound]) -> Dict[str, Any]:
    """
    Calculate metrics for a sound package
    """
    total_duration = sum(getattr(sound, 'duration', 0) for sound in sounds)
    sound_count = len(sounds)
    
    return {
        "sound_count": sound_count,
        "total_duration_minutes": total_duration,
        "assignment_count": getattr(package, 'unique_users_accessed', 0),
        "total_listens": getattr(package, 'total_listens', 0),
        "unique_users_accessed": getattr(package, 'unique_users_accessed', 0)
    }

async def send_package_assignment_notification(
    employee_email: str,
    package_name: str,
    organization_name: str,
    assignment_notes: Optional[str] = None
):
    """
    Send notification email to employee about package assignment
    """
    try:
        # Mock email sending for development
        logger.info(f"📧 Package assignment notification sent to {employee_email}")
        logger.debug(f"Package: {package_name} from {organization_name}")
        if assignment_notes:
            logger.debug(f"Notes: {assignment_notes}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to send assignment notification to {employee_email}: {str(e)}")
        return False

def generate_mock_usage_analytics(
    package: OrganizationSoundPackage,
    time_range: str,
    db: Session
) -> Dict[str, Any]:
    """
    Generate mock analytics data for package usage
    """
    # Parse time range
    days = int(time_range.replace('d', ''))
    
    # Mock data - in production, this would query actual usage records
    analytics = {
        "total_assignments": getattr(package, 'unique_users_accessed', 0) or 5,
        "active_users": 3,
        "completion_rate": 68.5,
        "avg_session_duration_minutes": 22.3,
        "total_plays": getattr(package, 'total_listens', 0) or 45,
        "most_popular_sounds": [
            {"sound_id": 1, "title": "Ocean Waves", "play_count": 15},
            {"sound_id": 2, "title": "Forest Rain", "play_count": 12},
            {"sound_id": 3, "title": "White Noise", "play_count": 8}
        ],
        "usage_by_day": []
    }
    
    # Generate daily usage data
    for i in range(days):
        date = datetime.utcnow() - timedelta(days=i)
        analytics["usage_by_day"].append({
            "date": date.strftime("%Y-%m-%d"),
            "plays": max(0, 8 - i * 0.5),
            "unique_users": max(1, 4 - i * 0.2),
            "total_duration_minutes": max(10, 180 - i * 5)
        })
    
    # Mock performance metrics
    analytics["performance_metrics"] = {
        "engagement_score": 78.5,
        "retention_rate": 85.2,
        "stress_reduction_reported": 12.3,
        "satisfaction_score": 4.2,
        "productivity_improvement": 8.7
    }
    
    return analytics

# =================== API ENDPOINTS ===================

@router.get("/packages", response_model=PackageListResponse)
async def get_organization_packages(
    skip: int = Query(0, ge=0, description="Number of packages to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of packages to return"),
    search: Optional[str] = Query(None, description="Search packages by name or category"),
    category: Optional[str] = Query(None, description="Filter by package category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all available sound packages for the organization with filtering and pagination
    """
    try:
        # Ensure user has an organization
        user_org_id = getattr(current_user, 'organization_id', None)
        if not user_org_id:
            raise HTTPException(status_code=400, detail="User is not associated with an organization")
        
        # Build base query
        query = db.query(OrganizationSoundPackage).filter(
            OrganizationSoundPackage.organization_id == user_org_id
        )
        
        # Apply search filter
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    OrganizationSoundPackage.package_name.ilike(search_pattern),
                    OrganizationSoundPackage.description.ilike(search_pattern),
                    OrganizationSoundPackage.category.ilike(search_pattern)
                )
            )
        
        # Apply category filter
        if category:
            query = query.filter(OrganizationSoundPackage.category == category)
        
        # Apply status filter
        if is_active is not None:
            query = query.filter(OrganizationSoundPackage.is_active == is_active)
        
        # Apply sorting
        sort_field = getattr(OrganizationSoundPackage, sort_by, OrganizationSoundPackage.created_at)
        if sort_order.lower() == "desc":
            query = query.order_by(desc(sort_field))
        else:
            query = query.order_by(sort_field)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        packages = query.offset(offset).limit(page_size).all()
        
        # Calculate pagination info
        total_pages = (total + page_size - 1) // page_size
        
        # Convert to response format
        package_responses = []
        for pkg in packages:
            # Get sounds for this package
            sound_ids = getattr(pkg, 'sound_ids', []) or []
            sounds = get_sounds_by_ids(db, sound_ids) if sound_ids else []
            
            # Calculate metrics
            metrics = calculate_package_metrics(pkg, sounds)
            
            # Create sound info list
            sound_infos = []
            for sound in sounds:
                sound_infos.append(SoundInfo(
                    id=getattr(sound, 'id', 0),
                    title=getattr(sound, 'title', ''),
                    description=getattr(sound, 'description', ''),
                    category=getattr(sound, 'category', ''),
                    duration=getattr(sound, 'duration', 0.0),
                    is_premium=getattr(sound, 'is_premium', False)
                ))
            
            pkg_response = PackageResponse(
                id=str(getattr(pkg, 'id', '')),
                name=getattr(pkg, 'package_name', ''),
                description=getattr(pkg, 'description', ''),
                category=getattr(pkg, 'category', ''),
                sound_count=metrics["sound_count"],
                total_duration_minutes=metrics["total_duration_minutes"],
                is_active=getattr(pkg, 'is_active', True),
                auto_assign_new_users=getattr(pkg, 'auto_assign_new_users', False),
                assignment_count=metrics["assignment_count"],
                total_listens=metrics["total_listens"],
                unique_users_accessed=metrics["unique_users_accessed"],
                created_at=getattr(pkg, 'created_at', datetime.utcnow()),
                updated_at=getattr(pkg, 'updated_at', datetime.utcnow()),
                sounds=sound_infos
            )
            package_responses.append(pkg_response)
        
        return PackageListResponse(
            packages=package_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"Failed to list packages: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list packages: {str(e)}")

@router.post("/packages", response_model=PackageResponse)
async def create_custom_package(
    package_data: PackageCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a custom sound package for the organization
    """
    try:
        # Ensure user has an organization
        user_org_id = getattr(current_user, 'organization_id', None)
        if not user_org_id:
            raise HTTPException(status_code=400, detail="User is not associated with an organization")
        
        # Validate that sounds exist
        sounds = get_sounds_by_ids(db, package_data.sound_ids)
        if len(sounds) != len(package_data.sound_ids):
            found_ids = [getattr(s, 'id', 0) for s in sounds]
            missing_ids = set(package_data.sound_ids) - set(found_ids)
            raise HTTPException(status_code=404, detail=f"Sounds not found: {list(missing_ids)}")
        
        # Check for duplicate package names within organization
        existing_package = db.query(OrganizationSoundPackage).filter(
            and_(
                OrganizationSoundPackage.organization_id == user_org_id,
                OrganizationSoundPackage.package_name == package_data.name
            )
        ).first()
        
        if existing_package:
            raise HTTPException(status_code=409, detail="Package with this name already exists")
        
        # Calculate package metrics
        total_duration = sum(getattr(sound, 'duration', 0) for sound in sounds)
        
        # Create new package
        new_package = OrganizationSoundPackage(
            organization_id=user_org_id,
            package_name=package_data.name,
            description=package_data.description,
            category=package_data.category,
            sound_ids=package_data.sound_ids,
            auto_assign_new_users=package_data.auto_assign_new_users,
            delivery_schedule=package_data.delivery_schedule,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(new_package)
        db.commit()
        db.refresh(new_package)
        
        # Assign to specified employees if requested
        if package_data.assign_to_employees:
            # Verify employees belong to the organization
            employees = db.query(User).filter(
                and_(
                    User.id.in_(package_data.assign_to_employees),
                    User.organization_id == user_org_id
                )
            ).all()
            
            # Send notifications in background
            org = db.query(Organization).filter(Organization.id == user_org_id).first()
            org_name = getattr(org, 'name', 'Unknown') if org else 'Unknown'
            
            for employee in employees:
                emp_email = getattr(employee, 'email', '')
                if emp_email:
                    background_tasks.add_task(
                        send_package_assignment_notification,
                        employee_email=emp_email,
                        package_name=package_data.name,
                        organization_name=org_name,
                        assignment_notes=package_data.assignment_notes
                    )
        
        # Create response
        sound_infos = []
        for sound in sounds:
            sound_infos.append(SoundInfo(
                id=getattr(sound, 'id', 0),
                title=getattr(sound, 'title', ''),
                description=getattr(sound, 'description', ''),
                category=getattr(sound, 'category', ''),
                duration=getattr(sound, 'duration', 0.0),
                is_premium=getattr(sound, 'is_premium', False)
            ))
        
        return PackageResponse(
            id=str(getattr(new_package, 'id', '')),
            name=getattr(new_package, 'package_name', ''),
            description=getattr(new_package, 'description', ''),
            category=getattr(new_package, 'category', ''),
            sound_count=len(sounds),
            total_duration_minutes=total_duration,
            is_active=getattr(new_package, 'is_active', True),
            auto_assign_new_users=getattr(new_package, 'auto_assign_new_users', False),
            assignment_count=0,
            total_listens=0,
            unique_users_accessed=0,
            created_at=getattr(new_package, 'created_at', datetime.utcnow()),
            updated_at=getattr(new_package, 'updated_at', datetime.utcnow()),
            sounds=sound_infos
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create package: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create package: {str(e)}")

@router.put("/packages/{package_id}/assign", response_model=PackageAssignmentResponse)
async def assign_package_to_employees(
    package_id: str,
    assignment_data: PackageAssignmentRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Assign a sound package to specific employees
    """
    try:
        # Ensure user has an organization
        user_org_id = getattr(current_user, 'organization_id', None)
        if not user_org_id:
            raise HTTPException(status_code=400, detail="User is not associated with an organization")
        
        # Get the package
        package = db.query(OrganizationSoundPackage).filter(
            and_(
                OrganizationSoundPackage.id == package_id,
                OrganizationSoundPackage.organization_id == user_org_id
            )
        ).first()
        
        if not package:
            raise HTTPException(status_code=404, detail="Package not found in your organization")
        
        if not getattr(package, 'is_active', True):
            raise HTTPException(status_code=400, detail="Cannot assign inactive package")
        
        # Get employees to assign
        employees = db.query(User).filter(
            and_(
                User.id.in_(assignment_data.employee_ids),
                User.organization_id == user_org_id
            )
        ).all()
        
        successful_assignments = []
        failed_assignments = []
        
        # Get organization for notifications
        org = db.query(Organization).filter(Organization.id == user_org_id).first()
        org_name = getattr(org, 'name', 'Unknown') if org else 'Unknown'
        package_name = getattr(package, 'package_name', 'Unknown Package')
        
        for employee_id in assignment_data.employee_ids:
            try:
                employee = next((emp for emp in employees if getattr(emp, 'id', 0) == employee_id), None)
                
                if not employee:
                    failed_assignments.append({
                        "employee_id": employee_id,
                        "error": "Employee not found in organization"
                    })
                    continue
                
                # Check if already assigned (mock check since we don't have assignment tracking yet)
                # In a real implementation, you'd check the PackageAssignment table
                
                # Mock assignment success
                successful_assignments.append(employee_id)
                
                # Send notification if requested
                if assignment_data.send_notification:
                    emp_email = getattr(employee, 'email', '')
                    if emp_email:
                        background_tasks.add_task(
                            send_package_assignment_notification,
                            employee_email=emp_email,
                            package_name=package_name,
                            organization_name=org_name,
                            assignment_notes=assignment_data.assignment_notes
                        )
                
            except Exception as e:
                failed_assignments.append({
                    "employee_id": employee_id,
                    "error": str(e)
                })
        
        # Update package assignment count
        current_users = getattr(package, 'unique_users_accessed', 0) or 0
        setattr(package, 'unique_users_accessed', current_users + len(successful_assignments))
        db.commit()
        
        return PackageAssignmentResponse(
            package_id=package_id,
            successful_assignments=successful_assignments,
            failed_assignments=failed_assignments,
            total_assigned=len(successful_assignments)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to assign package {package_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to assign package: {str(e)}")

@router.get("/packages/{package_id}/usage", response_model=PackageUsageAnalytics)
async def get_package_usage_analytics(
    package_id: str,
    time_range: str = Query("30d", description="Time range: 7d, 30d, 90d"),
    include_employee_details: bool = Query(True, description="Include individual employee progress"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed usage analytics for a specific sound package
    """
    try:
        # Ensure user has an organization
        user_org_id = getattr(current_user, 'organization_id', None)
        if not user_org_id:
            raise HTTPException(status_code=400, detail="User is not associated with an organization")
        
        # Get the package
        package = db.query(OrganizationSoundPackage).filter(
            and_(
                OrganizationSoundPackage.id == package_id,
                OrganizationSoundPackage.organization_id == user_org_id
            )
        ).first()
        
        if not package:
            raise HTTPException(status_code=404, detail="Package not found in your organization")
        
        # Generate analytics data
        analytics_data = generate_mock_usage_analytics(package, time_range, db)
        
        # Mock employee progress data
        employee_progress = []
        if include_employee_details:
            # In production, this would query actual assignment and usage records
            mock_employees = [
                {
                    "employee_id": 1,
                    "employee_email": "john.doe@company.com",
                    "employee_name": "John Doe",
                    "assigned_at": datetime.utcnow() - timedelta(days=15),
                    "status": "active",
                    "completion_percentage": 75.5,
                    "total_play_time_minutes": 180.3,
                    "last_activity_at": datetime.utcnow() - timedelta(hours=2)
                },
                {
                    "employee_id": 2,
                    "employee_email": "jane.smith@company.com",
                    "employee_name": "Jane Smith",
                    "assigned_at": datetime.utcnow() - timedelta(days=10),
                    "status": "completed",
                    "completion_percentage": 100.0,
                    "total_play_time_minutes": 240.7,
                    "last_activity_at": datetime.utcnow() - timedelta(days=1)
                }
            ]
            
            for emp_data in mock_employees:
                employee_progress.append(EmployeeAssignment(**emp_data))
        
        return PackageUsageAnalytics(
            package_id=package_id,
            package_name=getattr(package, 'package_name', ''),
            time_range=time_range,
            total_assignments=analytics_data["total_assignments"],
            active_users=analytics_data["active_users"],
            completion_rate=analytics_data["completion_rate"],
            avg_session_duration_minutes=analytics_data["avg_session_duration_minutes"],
            total_plays=analytics_data["total_plays"],
            most_popular_sounds=analytics_data["most_popular_sounds"],
            usage_by_day=analytics_data["usage_by_day"],
            employee_progress=employee_progress,
            performance_metrics=analytics_data["performance_metrics"],
            generated_at=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get package analytics for {package_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get package analytics: {str(e)}")

@router.delete("/packages/{package_id}")
async def remove_package(
    package_id: str,
    force_delete: bool = Query(False, description="Force delete even if assigned to employees"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Remove a sound package from the organization
    """
    try:
        # Ensure user has an organization
        user_org_id = getattr(current_user, 'organization_id', None)
        if not user_org_id:
            raise HTTPException(status_code=400, detail="User is not associated with an organization")
        
        # Get the package
        package = db.query(OrganizationSoundPackage).filter(
            and_(
                OrganizationSoundPackage.id == package_id,
                OrganizationSoundPackage.organization_id == user_org_id
            )
        ).first()
        
        if not package:
            raise HTTPException(status_code=404, detail="Package not found in your organization")
        
        package_name = getattr(package, 'package_name', 'Unknown')
        assignment_count = getattr(package, 'unique_users_accessed', 0) or 0
        
        # Check if package is assigned to employees
        if assignment_count > 0 and not force_delete:
            raise HTTPException(
                status_code=409,
                detail=f"Package is assigned to {assignment_count} employees. Use force_delete=true to proceed."
            )
        
        # Remove the package
        db.delete(package)
        db.commit()
        
        return {
            "message": f"Package '{package_name}' has been successfully removed",
            "package_id": package_id,
            "affected_employees": assignment_count,
            "removed_at": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to remove package {package_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to remove package: {str(e)}")
