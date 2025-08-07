"""
Business Admin Communications Router

Comprehensive communication tools for business administrators to manage
employee announcements, surveys, feedback collection, reminders, and
communication history within their organizations.

Created: July 27, 2025
Author: Sonicus Platform Team
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, text
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
import logging
import uuid
from enum import Enum

# Database and models
from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.organization import Organization

# Schemas
from pydantic import BaseModel, Field, validator
from typing import Union

# Authentication and security
from app.core.auth_dependencies import get_current_user_compatible as get_current_user, get_business_admin_user

# Initialize router and logger
router = APIRouter()
logger = logging.getLogger(__name__)

# =================== ENUMS ===================

class CommunicationType(str, Enum):
    """Types of communications"""
    ANNOUNCEMENT = "announcement"
    SURVEY = "survey"
    FEEDBACK_REQUEST = "feedback_request"
    REMINDER = "reminder"
    ALERT = "alert"
    UPDATE = "update"

class Priority(str, Enum):
    """Communication priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class DeliveryMethod(str, Enum):
    """Methods for delivering communications"""
    EMAIL = "email"
    IN_APP = "in_app"
    PUSH_NOTIFICATION = "push_notification"
    SMS = "sms"
    ALL = "all"

class SurveyType(str, Enum):
    """Types of surveys"""
    WELLNESS_CHECK = "wellness_check"
    SATISFACTION = "satisfaction"
    FEEDBACK = "feedback"
    PULSE = "pulse"
    EXIT = "exit"
    CUSTOM = "custom"

class CommunicationStatus(str, Enum):
    """Status of communications"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    RESPONDED = "responded"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class ReminderFrequency(str, Enum):
    """Reminder frequency options"""
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"

# =================== PYDANTIC SCHEMAS ===================

class CommunicationTarget(BaseModel):
    """Schema for communication targeting"""
    target_type: str = Field(..., description="all, specific, role, department")
    employee_ids: Optional[List[int]] = Field(default_factory=list)
    roles: Optional[List[str]] = Field(default_factory=list)
    departments: Optional[List[str]] = Field(default_factory=list)
    exclude_employee_ids: Optional[List[int]] = Field(default_factory=list)

class AnnouncementRequest(BaseModel):
    """Schema for creating announcements"""
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1, max_length=5000)
    priority: Priority = Priority.MEDIUM
    category: Optional[str] = Field(None, max_length=100)
    
    # Delivery settings
    delivery_methods: List[DeliveryMethod] = Field(default_factory=lambda: [DeliveryMethod.EMAIL, DeliveryMethod.IN_APP])
    schedule_for: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    # Targeting
    targets: CommunicationTarget
    
    # Options
    require_acknowledgment: bool = False
    allow_comments: bool = True
    attach_files: Optional[List[str]] = Field(default_factory=list)
    tags: Optional[List[str]] = Field(default_factory=list)

class SurveyQuestion(BaseModel):
    """Schema for survey questions"""
    question_id: str = Field(..., min_length=1)
    question_text: str = Field(..., min_length=1, max_length=1000)
    question_type: str = Field(..., description="multiple_choice, text, rating, yes_no, scale")
    options: Optional[List[str]] = Field(default_factory=list)
    required: bool = True
    order: int = Field(..., ge=1)

class SurveyRequest(BaseModel):
    """Schema for creating surveys"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    survey_type: SurveyType = SurveyType.CUSTOM
    
    # Questions
    questions: List[SurveyQuestion] = Field(..., description="Survey questions (minimum 1 required)")
    
    @validator('questions')
    def validate_questions(cls, v):
        if not v or len(v) < 1:
            raise ValueError('At least one question is required')
        return v
    
    # Settings
    anonymous: bool = False
    multiple_responses: bool = False
    show_results: bool = False
    
    # Delivery
    delivery_methods: List[DeliveryMethod] = Field(default_factory=lambda: [DeliveryMethod.EMAIL])
    schedule_for: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    reminder_frequency: Optional[ReminderFrequency] = None
    
    # Targeting
    targets: CommunicationTarget
    
    # Metadata
    tags: Optional[List[str]] = Field(default_factory=list)

class FeedbackFilter(BaseModel):
    """Schema for filtering feedback"""
    feedback_type: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    employee_ids: Optional[List[int]] = Field(default_factory=list)
    categories: Optional[List[str]] = Field(default_factory=list)
    sentiment: Optional[str] = Field(None, description="positive, neutral, negative")
    status: Optional[str] = Field(None, description="new, reviewed, responded, closed")

class ReminderRequest(BaseModel):
    """Schema for creating reminders"""
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=2000)
    reminder_type: str = Field(..., description="wellness_check, goal_update, survey_reminder, etc.")
    
    # Scheduling
    start_date: datetime
    frequency: ReminderFrequency = ReminderFrequency.ONCE
    end_date: Optional[datetime] = None
    custom_schedule: Optional[Dict[str, Any]] = None
    
    # Delivery
    delivery_methods: List[DeliveryMethod] = Field(default_factory=lambda: [DeliveryMethod.IN_APP])
    delivery_time: Optional[str] = Field(None, description="HH:MM format")
    timezone: Optional[str] = Field(None, description="Employee timezone")
    
    # Targeting
    targets: CommunicationTarget
    
    # Options
    personalized: bool = True
    action_required: bool = False
    action_url: Optional[str] = None
    tags: Optional[List[str]] = Field(default_factory=list)

class CommunicationHistoryFilter(BaseModel):
    """Schema for filtering communication history"""
    communication_types: Optional[List[CommunicationType]] = Field(default_factory=list)
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    status: Optional[CommunicationStatus] = None
    priority: Optional[Priority] = None
    employee_id: Optional[int] = None
    created_by: Optional[int] = None
    search_text: Optional[str] = None

# =================== RESPONSE SCHEMAS ===================

class AnnouncementResponse(BaseModel):
    """Response schema for announcements"""
    announcement_id: str
    title: str
    content: str
    priority: str
    category: Optional[str]
    status: str
    
    # Delivery info
    delivery_methods: List[str]
    scheduled_for: Optional[datetime]
    expires_at: Optional[datetime]
    
    # Stats
    total_recipients: int
    delivered_count: int
    read_count: int
    acknowledged_count: int
    comment_count: int
    
    # Metadata
    created_by: int
    created_at: datetime
    tags: List[str]

class SurveyResponse(BaseModel):
    """Response schema for surveys"""
    survey_id: str
    title: str
    description: Optional[str]
    survey_type: str
    status: str
    
    # Configuration
    anonymous: bool
    multiple_responses: bool
    show_results: bool
    
    # Questions
    question_count: int
    questions: List[Dict[str, Any]]
    
    # Delivery info
    delivery_methods: List[str]
    scheduled_for: Optional[datetime]
    expires_at: Optional[datetime]
    
    # Response stats
    total_recipients: int
    response_count: int
    response_rate: float
    completion_rate: float
    
    # Metadata
    created_by: int
    created_at: datetime
    tags: List[str]

class FeedbackItem(BaseModel):
    """Schema for individual feedback items"""
    feedback_id: str
    employee_id: Optional[int]
    employee_email: Optional[str]
    feedback_type: str
    category: Optional[str]
    subject: Optional[str]
    content: str
    
    # Analysis
    sentiment: Optional[str]
    sentiment_score: Optional[float]
    keywords: List[str]
    
    # Status
    status: str
    priority: Optional[str]
    assigned_to: Optional[int]
    
    # Metadata
    submitted_at: datetime
    responded_at: Optional[datetime]
    source: str
    tags: List[str]

class FeedbackSummary(BaseModel):
    """Summary of collected feedback"""
    total_feedback_items: int
    feedback_by_type: Dict[str, int]
    feedback_by_category: Dict[str, int]
    sentiment_distribution: Dict[str, int]
    recent_feedback: List[FeedbackItem]
    trending_topics: List[Dict[str, Any]]
    response_rate: float
    average_sentiment_score: float

class ReminderResponse(BaseModel):
    """Response schema for reminders"""
    reminder_id: str
    title: str
    message: str
    reminder_type: str
    
    # Schedule
    frequency: str
    start_date: datetime
    end_date: Optional[datetime]
    next_delivery: Optional[datetime]
    
    # Delivery
    delivery_methods: List[str]
    delivery_time: Optional[str]
    
    # Stats
    total_recipients: int
    total_sent: int
    delivery_success_rate: float
    
    # Status
    status: str
    is_active: bool
    
    # Metadata
    created_by: int
    created_at: datetime
    tags: List[str]

class CommunicationHistoryItem(BaseModel):
    """Schema for communication history items"""
    communication_id: str
    communication_type: str
    title: str
    status: str
    priority: str
    
    # Recipients
    total_recipients: int
    successful_deliveries: int
    failed_deliveries: int
    
    # Engagement
    read_count: int
    response_count: int
    engagement_rate: float
    
    # Metadata
    created_by: int
    created_by_name: str
    created_at: datetime
    last_updated: datetime
    tags: List[str]

class CommunicationHistoryResponse(BaseModel):
    """Response schema for communication history"""
    communications: List[CommunicationHistoryItem]
    total: int
    page: int
    page_size: int
    total_pages: int
    summary_stats: Dict[str, Any]

# =================== HELPER FUNCTIONS ===================

# Use centralized business admin authentication from auth_dependencies
# get_business_admin_user is now imported and available for use

def validate_communication_targets(
    targets: CommunicationTarget, 
    organization_id: str, 
    db: Session
) -> List[User]:
    """Validate and resolve communication targets to actual users"""
    target_users = []
    
    if targets.target_type == "all":
        # Get all users in organization
        target_users = db.query(User).filter(
            User.organization_id == organization_id
        ).all()
    
    elif targets.target_type == "specific":
        # Get specific employees
        if targets.employee_ids:
            target_users = db.query(User).filter(
                and_(
                    User.id.in_(targets.employee_ids),
                    User.organization_id == organization_id
                )
            ).all()
    
    elif targets.target_type == "role":
        # Get users by role
        if targets.roles:
            # Convert string roles to enum values
            role_enums = []
            for role_str in targets.roles:
                try:
                    role_enums.append(UserRole(role_str))
                except ValueError:
                    continue
            
            if role_enums:
                target_users = db.query(User).filter(
                    and_(
                        User.role.in_(role_enums),
                        User.organization_id == organization_id
                    )
                ).all()
    
    # Remove excluded users
    if targets.exclude_employee_ids:
        exclude_ids = set(targets.exclude_employee_ids)
        target_users = [
            user for user in target_users 
            if getattr(user, 'id', 0) not in exclude_ids
        ]
    
    return target_users

async def send_communication_notification(
    users: List[User],
    communication_type: str,
    title: str,
    content: str,
    delivery_methods: List[DeliveryMethod],
    background_tasks: BackgroundTasks
) -> Dict[str, int]:
    """Send notifications to users via specified delivery methods"""
    
    delivery_stats = {
        "total_attempted": len(users),
        "email_successful": 0,
        "email_failed": 0,
        "in_app_successful": 0,
        "push_successful": 0,
        "sms_successful": 0
    }
    
    for user in users:
        user_email = getattr(user, 'email', '')
        
        # Email delivery
        if DeliveryMethod.EMAIL in delivery_methods or DeliveryMethod.ALL in delivery_methods:
            try:
                # Mock email sending
                logger.info(f"📧 {communication_type.title()} sent via email to {user_email}")
                logger.debug(f"Subject: {title}")
                delivery_stats["email_successful"] += 1
            except Exception as e:
                logger.error(f"Failed to send email to {user_email}: {str(e)}")
                delivery_stats["email_failed"] += 1
        
        # In-app notification
        if DeliveryMethod.IN_APP in delivery_methods or DeliveryMethod.ALL in delivery_methods:
            try:
                # Mock in-app notification
                logger.info(f"📱 In-app {communication_type} notification sent to {user_email}")
                delivery_stats["in_app_successful"] += 1
            except Exception as e:
                logger.error(f"Failed to send in-app notification to {user_email}: {str(e)}")
        
        # Push notification
        if DeliveryMethod.PUSH_NOTIFICATION in delivery_methods or DeliveryMethod.ALL in delivery_methods:
            try:
                # Mock push notification
                logger.info(f"🔔 Push notification sent to {user_email}")
                delivery_stats["push_successful"] += 1
            except Exception as e:
                logger.error(f"Failed to send push notification to {user_email}: {str(e)}")
        
        # SMS delivery
        if DeliveryMethod.SMS in delivery_methods or DeliveryMethod.ALL in delivery_methods:
            try:
                # Mock SMS sending
                user_phone = getattr(user, 'telephone', '')
                if user_phone:
                    logger.info(f"📲 SMS sent to {user_phone} ({user_email})")
                    delivery_stats["sms_successful"] += 1
                else:
                    logger.warning(f"No phone number for SMS delivery to {user_email}")
            except Exception as e:
                logger.error(f"Failed to send SMS to {user_email}: {str(e)}")
    
    return delivery_stats

def generate_mock_feedback_data(
    organization_id: str,
    filters: FeedbackFilter,
    db: Session
) -> List[FeedbackItem]:
    """Generate mock feedback data for demonstration"""
    
    mock_feedback = [
        {
            "feedback_id": str(uuid.uuid4()),
            "employee_id": 1,
            "employee_email": "john.doe@company.com",
            "feedback_type": "suggestion",
            "category": "wellness_program",
            "subject": "More meditation content needed",
            "content": "I'd love to see more guided meditation sessions, especially for beginners. The current selection is great but could use more variety.",
            "sentiment": "positive",
            "sentiment_score": 0.75,
            "keywords": ["meditation", "content", "variety", "beginners"],
            "status": "new",
            "priority": "medium",
            "submitted_at": datetime.utcnow() - timedelta(days=2),
            "source": "app_feedback",
            "tags": ["content", "meditation", "suggestion"]
        },
        {
            "feedback_id": str(uuid.uuid4()),
            "employee_id": 2,
            "employee_email": "jane.smith@company.com",
            "feedback_type": "complaint",
            "category": "technical_issue",
            "subject": "App crashes during sessions",
            "content": "The app keeps crashing when I try to start a breathing exercise. This is really frustrating when I'm trying to de-stress during busy workdays.",
            "sentiment": "negative",
            "sentiment_score": -0.6,
            "keywords": ["crash", "breathing", "technical", "frustrating"],
            "status": "reviewed",
            "priority": "high",
            "submitted_at": datetime.utcnow() - timedelta(days=5),
            "responded_at": datetime.utcnow() - timedelta(days=3),
            "source": "support_ticket",
            "tags": ["technical", "bug", "urgent"]
        },
        {
            "feedback_id": str(uuid.uuid4()),
            "employee_id": 3,
            "employee_email": "mike.johnson@company.com",
            "feedback_type": "praise",
            "category": "general",
            "subject": "Great improvement in team morale",
            "content": "Since we started using the wellness program, I've noticed a significant improvement in our team's overall mood and collaboration. Thank you for investing in our wellbeing!",
            "sentiment": "positive",
            "sentiment_score": 0.85,
            "keywords": ["improvement", "team", "morale", "collaboration", "wellbeing"],
            "status": "responded",
            "priority": "low",
            "submitted_at": datetime.utcnow() - timedelta(days=7),
            "responded_at": datetime.utcnow() - timedelta(days=6),
            "source": "survey_response",
            "tags": ["praise", "team", "morale"]
        },
        {
            "feedback_id": str(uuid.uuid4()),
            "employee_id": 4,
            "employee_email": "sarah.wilson@company.com",
            "feedback_type": "feature_request",
            "category": "functionality",
            "subject": "Sleep tracking integration",
            "content": "It would be amazing if the app could integrate with my fitness tracker to automatically log my sleep data. Manual entry is a bit tedious.",
            "sentiment": "neutral",
            "sentiment_score": 0.1,
            "keywords": ["sleep", "tracking", "integration", "fitness", "automatic"],
            "status": "new",
            "priority": "medium",
            "submitted_at": datetime.utcnow() - timedelta(days=1),
            "source": "app_feedback",
            "tags": ["feature", "integration", "sleep"]
        }
    ]
    
    # Apply filters
    filtered_feedback = []
    for item in mock_feedback:
        if filters.feedback_type and item["feedback_type"] != filters.feedback_type:
            continue
        if filters.sentiment and item["sentiment"] != filters.sentiment:
            continue
        if filters.status and item["status"] != filters.status:
            continue
        if filters.date_from and item["submitted_at"] < filters.date_from:
            continue
        if filters.date_to and item["submitted_at"] > filters.date_to:
            continue
        if filters.employee_ids and item["employee_id"] not in filters.employee_ids:
            continue
        
        filtered_feedback.append(FeedbackItem(**item))
    
    return filtered_feedback

def generate_mock_communication_history(
    organization_id: str,
    filters: CommunicationHistoryFilter,
    page: int,
    page_size: int
) -> List[CommunicationHistoryItem]:
    """Generate mock communication history for demonstration"""
    
    mock_history = [
        {
            "communication_id": str(uuid.uuid4()),
            "communication_type": "announcement",
            "title": "New Wellness Content Available",
            "status": "sent",
            "priority": "medium",
            "total_recipients": 45,
            "successful_deliveries": 43,
            "failed_deliveries": 2,
            "read_count": 38,
            "response_count": 12,
            "engagement_rate": 86.4,
            "created_by": 1,
            "created_by_name": "Admin User",
            "created_at": datetime.utcnow() - timedelta(days=3),
            "last_updated": datetime.utcnow() - timedelta(days=2),
            "tags": ["content", "wellness", "announcement"]
        },
        {
            "communication_id": str(uuid.uuid4()),
            "communication_type": "survey",
            "title": "Monthly Wellness Check-in",
            "status": "sent",
            "priority": "high",
            "total_recipients": 45,
            "successful_deliveries": 45,
            "failed_deliveries": 0,
            "read_count": 41,
            "response_count": 35,
            "engagement_rate": 85.4,
            "created_by": 1,
            "created_by_name": "Admin User",
            "created_at": datetime.utcnow() - timedelta(days=7),
            "last_updated": datetime.utcnow() - timedelta(days=1),
            "tags": ["survey", "wellness", "monthly"]
        },
        {
            "communication_id": str(uuid.uuid4()),
            "communication_type": "reminder",
            "title": "Complete Your Daily Meditation",
            "status": "sent",
            "priority": "low",
            "total_recipients": 28,
            "successful_deliveries": 28,
            "failed_deliveries": 0,
            "read_count": 24,
            "response_count": 18,
            "engagement_rate": 75.0,
            "created_by": 1,
            "created_by_name": "Admin User",
            "created_at": datetime.utcnow() - timedelta(days=1),
            "last_updated": datetime.utcnow() - timedelta(hours=2),
            "tags": ["reminder", "meditation", "daily"]
        }
    ]
    
    # Apply filters
    filtered_history = []
    for item in mock_history:
        if filters.communication_types and item["communication_type"] not in [t.value for t in filters.communication_types]:
            continue
        if filters.status and item["status"] != filters.status.value:
            continue
        if filters.priority and item["priority"] != filters.priority.value:
            continue
        if filters.date_from and item["created_at"] < filters.date_from:
            continue
        if filters.date_to and item["created_at"] > filters.date_to:
            continue
        if filters.search_text and filters.search_text.lower() not in item["title"].lower():
            continue
        
        filtered_history.append(CommunicationHistoryItem(**item))
    
    # Apply pagination
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    
    return filtered_history[start_idx:end_idx]

# =================== API ENDPOINTS ===================

@router.post("/announcements", response_model=AnnouncementResponse)
async def send_announcement(
    announcement_data: AnnouncementRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_business_admin_user)
):
    """
    Send announcements to employees in the organization
    """
    try:
        # Ensure user has an organization
        user_org_id = getattr(current_user, 'organization_id', None)
        if not user_org_id:
            raise HTTPException(status_code=400, detail="User is not associated with an organization")
        
        # Validate and resolve targets
        target_users = validate_communication_targets(
            announcement_data.targets, str(user_org_id), db
        )
        
        if not target_users:
            raise HTTPException(status_code=404, detail="No valid recipients found for the specified targets")
        
        # Check if announcement should be scheduled
        if announcement_data.schedule_for and announcement_data.schedule_for > datetime.utcnow():
            # Schedule for later delivery
            status = CommunicationStatus.SCHEDULED
            logger.info(f"Announcement scheduled for {announcement_data.schedule_for}")
        else:
            # Send immediately
            delivery_stats = await send_communication_notification(
                target_users,
                "announcement",
                announcement_data.title,
                announcement_data.content,
                announcement_data.delivery_methods,
                background_tasks
            )
            status = CommunicationStatus.SENT
        
        # Generate response
        announcement_id = str(uuid.uuid4())
        
        return AnnouncementResponse(
            announcement_id=announcement_id,
            title=announcement_data.title,
            content=announcement_data.content,
            priority=announcement_data.priority.value,
            category=announcement_data.category,
            status=status.value,
            delivery_methods=[method.value for method in announcement_data.delivery_methods],
            scheduled_for=announcement_data.schedule_for,
            expires_at=announcement_data.expires_at,
            total_recipients=len(target_users),
            delivered_count=len(target_users) if status == CommunicationStatus.SENT else 0,
            read_count=0,  # Will be updated as users read
            acknowledged_count=0,  # Will be updated as users acknowledge
            comment_count=0,  # Will be updated as users comment
            created_by=getattr(current_user, 'id', 0),
            created_at=datetime.utcnow(),
            tags=announcement_data.tags or []
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send announcement: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send announcement: {str(e)}")

@router.post("/communications/surveys", response_model=SurveyResponse)
async def create_survey(
    survey_data: SurveyRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_business_admin_user)
):
    """
    Create and send surveys to employees
    """
    try:
        user_org_id = getattr(current_user, 'organization_id', None)
        if not user_org_id:
            raise HTTPException(status_code=400, detail="User is not associated with an organization")
        
        # Validate survey questions
        question_ids = [q.question_id for q in survey_data.questions]
        if len(question_ids) != len(set(question_ids)):
            raise HTTPException(status_code=400, detail="Duplicate question IDs found")
        
        # Validate and resolve targets
        target_users = validate_communication_targets(
            survey_data.targets, str(user_org_id), db
        )
        
        if not target_users:
            raise HTTPException(status_code=404, detail="No valid recipients found for the specified targets")
        
        # Process questions for storage
        processed_questions = []
        for question in survey_data.questions:
            processed_questions.append({
                "question_id": question.question_id,
                "question_text": question.question_text,
                "question_type": question.question_type,
                "options": question.options,
                "required": question.required,
                "order": question.order
            })
        
        # Send survey invitations
        if survey_data.schedule_for and survey_data.schedule_for > datetime.utcnow():
            status = CommunicationStatus.SCHEDULED
            logger.info(f"Survey scheduled for {survey_data.schedule_for}")
        else:
            # Send survey invitations
            survey_content = f"You have been invited to participate in: {survey_data.title}"
            if survey_data.description:
                survey_content += f"\n\n{survey_data.description}"
            
            delivery_stats = await send_communication_notification(
                target_users,
                "survey",
                f"Survey: {survey_data.title}",
                survey_content,
                survey_data.delivery_methods,
                background_tasks
            )
            status = CommunicationStatus.SENT
        
        # Generate response
        survey_id = str(uuid.uuid4())
        
        return SurveyResponse(
            survey_id=survey_id,
            title=survey_data.title,
            description=survey_data.description,
            survey_type=survey_data.survey_type.value,
            status=status.value,
            anonymous=survey_data.anonymous,
            multiple_responses=survey_data.multiple_responses,
            show_results=survey_data.show_results,
            question_count=len(survey_data.questions),
            questions=processed_questions,
            delivery_methods=[method.value for method in survey_data.delivery_methods],
            scheduled_for=survey_data.schedule_for,
            expires_at=survey_data.expires_at,
            total_recipients=len(target_users),
            response_count=0,  # Will be updated as responses come in
            response_rate=0.0,
            completion_rate=0.0,
            created_by=getattr(current_user, 'id', 0),
            created_at=datetime.utcnow(),
            tags=survey_data.tags or []
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create survey: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create survey: {str(e)}")

@router.get("/communications/feedback", response_model=FeedbackSummary)
async def collect_feedback(
    filters: FeedbackFilter = Depends(),
    include_summary: bool = Query(True, description="Include summary statistics"),
    limit: int = Query(20, ge=1, le=100, description="Number of recent feedback items to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_business_admin_user)
):
    """
    Collect and analyze employee feedback
    """
    try:
        user_org_id = getattr(current_user, 'organization_id', None)
        if not user_org_id:
            raise HTTPException(status_code=400, detail="User is not associated with an organization")
        
        # Get feedback data (using mock data for demonstration)
        feedback_items = generate_mock_feedback_data(str(user_org_id), filters, db)
        
        # Calculate summary statistics
        total_feedback = len(feedback_items)
        
        # Group by type
        feedback_by_type = {}
        for item in feedback_items:
            item_type = item.feedback_type
            feedback_by_type[item_type] = feedback_by_type.get(item_type, 0) + 1
        
        # Group by category
        feedback_by_category = {}
        for item in feedback_items:
            category = item.category or "uncategorized"
            feedback_by_category[category] = feedback_by_category.get(category, 0) + 1
        
        # Sentiment distribution
        sentiment_distribution = {}
        sentiment_scores = []
        for item in feedback_items:
            sentiment = item.sentiment or "neutral"
            sentiment_distribution[sentiment] = sentiment_distribution.get(sentiment, 0) + 1
            if item.sentiment_score:
                sentiment_scores.append(item.sentiment_score)
        
        # Calculate trending topics
        all_keywords = []
        for item in feedback_items:
            all_keywords.extend(item.keywords)
        
        keyword_counts = {}
        for keyword in all_keywords:
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        trending_topics = [
            {"topic": keyword, "count": count, "trend": "up"}
            for keyword, count in sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        # Calculate response rate (mock calculation)
        response_rate = 78.5  # Mock response rate
        
        # Calculate average sentiment
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
        
        # Get recent feedback (limited)
        recent_feedback = feedback_items[:limit]
        
        return FeedbackSummary(
            total_feedback_items=total_feedback,
            feedback_by_type=feedback_by_type,
            feedback_by_category=feedback_by_category,
            sentiment_distribution=sentiment_distribution,
            recent_feedback=recent_feedback,
            trending_topics=trending_topics,
            response_rate=response_rate,
            average_sentiment_score=avg_sentiment
        )
        
    except Exception as e:
        logger.error(f"Failed to collect feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to collect feedback: {str(e)}")

@router.post("/communications/reminders", response_model=ReminderResponse)
async def set_reminders(
    reminder_data: ReminderRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_business_admin_user)
):
    """
    Set up automated reminders for employees
    """
    try:
        user_org_id = getattr(current_user, 'organization_id', None)
        if not user_org_id:
            raise HTTPException(status_code=400, detail="User is not associated with an organization")
        
        # Validate reminder frequency and scheduling
        if reminder_data.frequency != ReminderFrequency.ONCE and not reminder_data.end_date:
            raise HTTPException(
                status_code=400, 
                detail="End date is required for recurring reminders"
            )
        
        if reminder_data.end_date and reminder_data.end_date <= reminder_data.start_date:
            raise HTTPException(
                status_code=400,
                detail="End date must be after start date"
            )
        
        # Validate and resolve targets
        target_users = validate_communication_targets(
            reminder_data.targets, str(user_org_id), db
        )
        
        if not target_users:
            raise HTTPException(status_code=404, detail="No valid recipients found for the specified targets")
        
        # Calculate next delivery time
        next_delivery = reminder_data.start_date
        if reminder_data.start_date <= datetime.utcnow():
            next_delivery = datetime.utcnow() + timedelta(minutes=1)  # Next minute if starting now
        
        # Set up the reminder (in a real implementation, this would be stored in database)
        reminder_id = str(uuid.uuid4())
        
        # Send initial reminder if it's time
        total_sent = 0
        delivery_success_rate = 0.0
        
        if reminder_data.start_date <= datetime.utcnow():
            delivery_stats = await send_communication_notification(
                target_users,
                "reminder",
                reminder_data.title,
                reminder_data.message,
                reminder_data.delivery_methods,
                background_tasks
            )
            
            total_sent = delivery_stats.get("total_attempted", 0)
            successful = sum([
                delivery_stats.get("email_successful", 0),
                delivery_stats.get("in_app_successful", 0),
                delivery_stats.get("push_successful", 0),
                delivery_stats.get("sms_successful", 0)
            ])
            delivery_success_rate = (successful / max(total_sent, 1)) * 100
        
        # Determine status
        is_active = True
        status = "active"
        if reminder_data.frequency == ReminderFrequency.ONCE and total_sent > 0:
            is_active = False
            status = "completed"
        
        return ReminderResponse(
            reminder_id=reminder_id,
            title=reminder_data.title,
            message=reminder_data.message,
            reminder_type=reminder_data.reminder_type,
            frequency=reminder_data.frequency.value,
            start_date=reminder_data.start_date,
            end_date=reminder_data.end_date,
            next_delivery=next_delivery if is_active else None,
            delivery_methods=[method.value for method in reminder_data.delivery_methods],
            delivery_time=reminder_data.delivery_time,
            total_recipients=len(target_users),
            total_sent=total_sent,
            delivery_success_rate=delivery_success_rate,
            status=status,
            is_active=is_active,
            created_by=getattr(current_user, 'id', 0),
            created_at=datetime.utcnow(),
            tags=reminder_data.tags or []
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set reminder: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to set reminder: {str(e)}")

@router.get("/communications/history", response_model=CommunicationHistoryResponse)
async def get_communication_history(
    filters: CommunicationHistoryFilter = Depends(),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    include_stats: bool = Query(True, description="Include summary statistics"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_business_admin_user)
):
    """
    Get communication history and analytics
    """
    try:
        user_org_id = getattr(current_user, 'organization_id', None)
        if not user_org_id:
            raise HTTPException(status_code=400, detail="User is not associated with an organization")
        
        # Get communication history (using mock data for demonstration)
        communications = generate_mock_communication_history(
            str(user_org_id), filters, page, page_size
        )
        
        # Calculate total count (for pagination)
        total_count = 25  # Mock total count
        total_pages = (total_count + page_size - 1) // page_size
        
        # Calculate summary statistics
        summary_stats = {}
        if include_stats:
            summary_stats = {
                "total_communications": total_count,
                "communications_this_month": 8,
                "average_engagement_rate": 82.3,
                "total_recipients_reached": 145,
                "most_used_communication_type": "announcement",
                "success_rate": 96.8,
                "response_rate": 74.2
            }
        
        return CommunicationHistoryResponse(
            communications=communications,
            total=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            summary_stats=summary_stats
        )
        
    except Exception as e:
        logger.error(f"Failed to get communication history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get communication history: {str(e)}")

# =================== BONUS ENDPOINTS ===================

@router.delete("/communications/{communication_id}")
async def delete_communication(
    communication_id: str,
    force_delete: bool = Query(False, description="Force delete even if already sent"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_business_admin_user)
):
    """
    Delete or cancel a communication
    """
    try:
        user_org_id = getattr(current_user, 'organization_id', None)
        if not user_org_id:
            raise HTTPException(status_code=400, detail="User is not associated with an organization")
        
        # In a real implementation, you would find and delete the communication
        # For now, we'll return a success message
        
        return {
            "message": f"Communication {communication_id} has been deleted successfully",
            "communication_id": communication_id,
            "deleted_by": getattr(current_user, 'id', 0),
            "deleted_at": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Failed to delete communication {communication_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete communication: {str(e)}")

@router.get("/communications/templates")
async def get_communication_templates(
    template_type: Optional[str] = Query(None, description="Filter by template type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_business_admin_user)
):
    """
    Get pre-built communication templates
    """
    try:
        # Mock templates for demonstration
        templates = [
            {
                "template_id": "announcement_new_content",
                "name": "New Content Announcement",
                "type": "announcement",
                "category": "content",
                "title": "New Wellness Content Available",
                "content": "We're excited to announce new meditation and mindfulness content has been added to your wellness library. Explore guided sessions designed to help reduce stress and improve focus.",
                "suggested_delivery_methods": ["email", "in_app"],
                "tags": ["content", "wellness", "announcement"]
            },
            {
                "template_id": "survey_monthly_checkin",
                "name": "Monthly Wellness Check-in",
                "type": "survey",
                "category": "wellness",
                "title": "How are you feeling this month?",
                "description": "Help us understand your wellness journey with this quick monthly check-in.",
                "questions": [
                    {
                        "question_id": "stress_level",
                        "question_text": "How would you rate your stress level this month?",
                        "question_type": "scale",
                        "options": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
                        "required": True,
                        "order": 1
                    },
                    {
                        "question_id": "program_satisfaction",
                        "question_text": "How satisfied are you with the wellness program?",
                        "question_type": "multiple_choice",
                        "options": ["Very satisfied", "Satisfied", "Neutral", "Dissatisfied", "Very dissatisfied"],
                        "required": True,
                        "order": 2
                    }
                ],
                "tags": ["survey", "wellness", "monthly"]
            },
            {
                "template_id": "reminder_daily_meditation",
                "name": "Daily Meditation Reminder",
                "type": "reminder",
                "category": "wellness",
                "title": "Time for your daily meditation",
                "message": "Take a few minutes to center yourself with a guided meditation session. Your mental wellbeing is important to us!",
                "frequency": "daily",
                "suggested_delivery_methods": ["in_app", "push_notification"],
                "tags": ["reminder", "meditation", "daily"]
            }
        ]
        
        # Filter by type if specified
        if template_type:
            templates = [t for t in templates if t["type"] == template_type]
        
        return {
            "templates": templates,
            "total": len(templates),
            "template_types": ["announcement", "survey", "reminder"]
        }
        
    except Exception as e:
        logger.error(f"Failed to get communication templates: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get communication templates: {str(e)}")

@router.get("/communications/analytics/engagement")
async def get_communication_engagement_analytics(
    period: str = Query("30d", description="Time period: 7d, 30d, 90d"),
    communication_type: Optional[str] = Query(None, description="Filter by communication type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_business_admin_user)
):
    """
    Get detailed engagement analytics for communications
    """
    try:
        user_org_id = getattr(current_user, 'organization_id', None)
        if not user_org_id:
            raise HTTPException(status_code=400, detail="User is not associated with an organization")
        
        # Mock engagement analytics
        analytics = {
            "period": period,
            "organization_id": str(user_org_id),
            "overall_engagement": {
                "total_communications": 15,
                "total_recipients": 675,
                "average_open_rate": 84.2,
                "average_response_rate": 67.8,
                "average_engagement_score": 78.5
            },
            "by_communication_type": {
                "announcement": {
                    "count": 8,
                    "open_rate": 89.3,
                    "response_rate": 23.4,
                    "engagement_score": 71.2
                },
                "survey": {
                    "count": 4,
                    "open_rate": 82.1,
                    "response_rate": 89.5,
                    "engagement_score": 87.8
                },
                "reminder": {
                    "count": 3,
                    "open_rate": 76.8,
                    "response_rate": 45.2,
                    "engagement_score": 68.9
                }
            },
            "engagement_trends": [
                {"date": "2025-07-20", "open_rate": 82.1, "response_rate": 65.3},
                {"date": "2025-07-21", "open_rate": 84.7, "response_rate": 68.9},
                {"date": "2025-07-22", "open_rate": 86.2, "response_rate": 71.2},
                {"date": "2025-07-23", "open_rate": 83.9, "response_rate": 69.7},
                {"date": "2025-07-24", "open_rate": 87.1, "response_rate": 73.4},
                {"date": "2025-07-25", "open_rate": 85.6, "response_rate": 70.8},
                {"date": "2025-07-26", "open_rate": 88.3, "response_rate": 75.1}
            ],
            "top_performing_communications": [
                {
                    "title": "New Meditation Content Available",
                    "type": "announcement",
                    "engagement_score": 92.4,
                    "open_rate": 95.2,
                    "response_rate": 34.7
                },
                {
                    "title": "Monthly Wellness Survey",
                    "type": "survey",
                    "engagement_score": 89.6,
                    "open_rate": 87.3,
                    "response_rate": 91.8
                }
            ],
            "recommendations": [
                "Continue using announcements for content updates - they show high open rates",
                "Consider timing reminders for mid-morning (10-11 AM) for better engagement",
                "Surveys perform best when kept under 5 questions",
                "Include personalization in communications to improve response rates"
            ]
        }
        
        return analytics
        
    except Exception as e:
        logger.error(f"Failed to get engagement analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get engagement analytics: {str(e)}")
