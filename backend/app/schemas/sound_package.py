"""
Sound Package Schemas

Pydantic schemas for sound package management in the Sonicus platform.
These schemas handle validation for package creation, updates, and responses.

Created: July 26, 2025
Author: Sonicus Platform Team
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

# =================== ENUMS ===================

class SoundPackageType(str, Enum):
    """Types of sound packages available"""
    STANDARD = "standard"
    CUSTOM = "custom"
    PREMIUM = "premium"
    TRIAL = "trial"

class SoundPackageStatus(str, Enum):
    """Status of sound packages"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"
    ARCHIVED = "archived"

class PackageAssignmentStatus(str, Enum):
    """Status of package assignments to employees"""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"

# =================== BASE SCHEMAS ===================

class SoundInfo(BaseModel):
    """Schema for sound information within packages"""
    id: int
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    duration: float = Field(..., ge=0)
    is_premium: bool = False
    file_url: Optional[str] = None
    thumbnail_url: Optional[str] = None

class PackageDeliverySchedule(BaseModel):
    """Schema for package delivery scheduling"""
    delivery_type: str = Field(..., description="daily, weekly, custom")
    frequency: int = Field(1, ge=1, description="Frequency of delivery")
    time_of_day: Optional[str] = Field(None, description="Preferred delivery time (HH:MM)")
    days_of_week: Optional[List[int]] = Field(None, description="Days for weekly delivery (0-6)")
    custom_schedule: Optional[Dict[str, Any]] = None

# =================== REQUEST SCHEMAS ===================

class PackageCreateRequest(BaseModel):
    """Schema for creating new sound packages"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, max_length=100)
    package_type: SoundPackageType = SoundPackageType.CUSTOM
    sound_ids: List[int]
    auto_assign_new_users: bool = False
    delivery_schedule: Optional[PackageDeliverySchedule] = None
    assign_to_employees: List[int] = Field(default_factory=list)
    assignment_notes: Optional[str] = Field(None, max_length=500)
    
    @validator('sound_ids')
    def validate_sound_ids(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one sound ID is required')
        return v
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Package name cannot be empty')
        return v.strip()

class PackageUpdateRequest(BaseModel):
    """Schema for updating existing packages"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, max_length=100)
    sound_ids: Optional[List[int]] = None
    status: Optional[SoundPackageStatus] = None
    auto_assign_new_users: Optional[bool] = None
    delivery_schedule: Optional[PackageDeliverySchedule] = None
    
    @validator('sound_ids')
    def validate_sound_ids(cls, v):
        if v is not None and len(v) == 0:
            raise ValueError('If provided, sound_ids must contain at least one ID')
        return v

class PackageAssignmentRequest(BaseModel):
    """Schema for assigning packages to employees"""
    employee_ids: List[int]
    assignment_notes: Optional[str] = Field(None, max_length=500)
    send_notification: bool = True
    auto_start: bool = True
    custom_deadline: Optional[datetime] = None
    
    @validator('employee_ids')
    def validate_employee_ids(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one employee ID is required')
        return v

# =================== RESPONSE SCHEMAS ===================

class PackageBasicInfo(BaseModel):
    """Basic package information schema"""
    id: str
    name: str
    description: Optional[str]
    category: Optional[str]
    package_type: str
    status: str
    sound_count: int
    created_at: datetime
    updated_at: datetime

class PackageResponse(BaseModel):
    """Comprehensive package information response"""
    id: str
    name: str
    description: Optional[str]
    category: Optional[str]
    package_type: str
    status: str
    sound_count: int
    total_duration_minutes: float
    is_active: bool
    auto_assign_new_users: bool
    assignment_count: int
    active_assignments: int
    total_listens: int
    unique_users_accessed: int
    avg_completion_rate: float
    created_at: datetime
    updated_at: datetime
    sounds: List[SoundInfo]
    delivery_schedule: Optional[PackageDeliverySchedule] = None
    
    class Config:
        from_attributes = True

class PackageListResponse(BaseModel):
    """Schema for paginated package list response"""
    packages: List[PackageResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    filters_applied: Dict[str, Any]

class EmployeeAssignmentInfo(BaseModel):
    """Schema for employee package assignment information"""
    employee_id: int
    employee_email: str
    employee_name: Optional[str]
    assigned_at: datetime
    status: PackageAssignmentStatus
    completion_percentage: float
    total_play_time_minutes: float
    sessions_completed: int
    last_activity_at: Optional[datetime]
    progress_notes: Optional[str] = None

class PackageAssignmentResponse(BaseModel):
    """Schema for package assignment operation response"""
    package_id: str
    package_name: str
    successful_assignments: List[int]
    failed_assignments: List[Dict[str, Any]]
    total_assigned: int
    notifications_sent: int
    operation_timestamp: datetime

# =================== ANALYTICS SCHEMAS ===================

class SoundPopularityInfo(BaseModel):
    """Schema for sound popularity within packages"""
    sound_id: int
    title: str
    play_count: int
    unique_listeners: int
    avg_session_duration: float
    completion_rate: float

class DailyUsageMetrics(BaseModel):
    """Schema for daily usage metrics"""
    date: str
    total_plays: int
    unique_users: int
    total_duration_minutes: float
    avg_session_duration: float
    new_assignments: int
    completions: int

class PackagePerformanceMetrics(BaseModel):
    """Schema for package performance metrics"""
    engagement_score: float = Field(..., ge=0, le=100)
    retention_rate: float = Field(..., ge=0, le=100)
    satisfaction_score: float = Field(..., ge=0, le=5)
    stress_reduction_reported: float = Field(..., ge=0, le=100)
    productivity_improvement: float = Field(..., ge=-50, le=100)
    recommended_by_users: int = Field(0, ge=0)

class PackageUsageAnalytics(BaseModel):
    """Comprehensive package usage analytics response"""
    package_id: str
    package_name: str
    analysis_period: str
    time_range_start: datetime
    time_range_end: datetime
    
    # Core metrics
    total_assignments: int
    active_users: int
    completed_assignments: int
    completion_rate: float
    avg_session_duration_minutes: float
    total_plays: int
    total_listening_hours: float
    
    # Detailed breakdowns
    most_popular_sounds: List[SoundPopularityInfo]
    daily_usage: List[DailyUsageMetrics]
    employee_progress: List[EmployeeAssignmentInfo]
    performance_metrics: PackagePerformanceMetrics
    
    # Trends and insights
    usage_trends: Dict[str, Any]
    recommendations: List[str]
    
    generated_at: datetime

# =================== BULK OPERATIONS ===================

class BulkPackageOperation(BaseModel):
    """Schema for bulk package operations"""
    operation: str = Field(..., description="activate, deactivate, delete, assign")
    package_ids: List[str]
    target_employee_ids: Optional[List[int]] = None
    operation_notes: Optional[str] = None
    
    @validator('package_ids')
    def validate_package_ids(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one package ID is required')
        return v

class BulkOperationResponse(BaseModel):
    """Schema for bulk operation response"""
    operation: str
    total_requested: int
    successful_operations: int
    failed_operations: int
    success_details: List[Dict[str, Any]]
    failure_details: List[Dict[str, Any]]
    operation_timestamp: datetime

# =================== SEARCH AND FILTER SCHEMAS ===================

class PackageSearchFilters(BaseModel):
    """Schema for package search and filtering"""
    search_query: Optional[str] = None
    category: Optional[str] = None
    package_type: Optional[SoundPackageType] = None
    status: Optional[SoundPackageStatus] = None
    min_duration: Optional[float] = Field(None, ge=0)
    max_duration: Optional[float] = Field(None, ge=0)
    min_sounds: Optional[int] = Field(None, ge=1)
    max_sounds: Optional[int] = Field(None, ge=1)
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    has_assignments: Optional[bool] = None
    assignment_count_min: Optional[int] = Field(None, ge=0)
    assignment_count_max: Optional[int] = Field(None, ge=0)

class PackageSortOptions(BaseModel):
    """Schema for package sorting options"""
    sort_by: str = Field("created_at", description="Field to sort by")
    sort_order: str = Field("desc", description="Sort order: asc or desc")
    secondary_sort: Optional[str] = None
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v not in ['asc', 'desc']:
            raise ValueError('Sort order must be either "asc" or "desc"')
        return v
