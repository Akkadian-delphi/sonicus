"""
Sound Package Models

This module defines the database models for sound packages, including
package definitions, employee assignments, and usage tracking.

Created: July 26, 2025
Author: Sonicus Platform Team
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey, Float, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
import uuid
from enum import Enum
from datetime import datetime


class PackageType(str, Enum):
    """Types of sound packages"""
    STANDARD = "standard"          # Pre-defined packages
    CUSTOM = "custom"             # Organization-specific packages
    PREMIUM = "premium"           # High-tier packages
    TRIAL = "trial"              # Trial packages


class PackageStatus(str, Enum):
    """Package status options"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"
    ARCHIVED = "archived"


class AssignmentStatus(str, Enum):
    """Employee package assignment status"""
    ASSIGNED = "assigned"
    ACTIVE = "active"
    COMPLETED = "completed"
    REVOKED = "revoked"


class SoundPackage(Base):
    """
    Sound packages that can be assigned to employees
    """
    __tablename__ = "sound_packages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Package configuration
    package_type = Column(SQLEnum(PackageType), nullable=False, default=PackageType.STANDARD)
    status = Column(SQLEnum(PackageStatus), nullable=False, default=PackageStatus.ACTIVE)
    
    # Organization relationship (null for global packages)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Package content
    sound_ids = Column(JSON, nullable=True)  # List of therapy sound IDs
    category_tags = Column(JSON, nullable=True)  # Categories included
    total_duration_minutes = Column(Float, nullable=True)
    sound_count = Column(Integer, default=0)
    
    # Usage tracking
    assignment_count = Column(Integer, default=0)
    total_plays = Column(Integer, default=0)
    avg_completion_rate = Column(Float, default=0.0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # Temporarily commented out to avoid circular import issues
    # organization = relationship("Organization", back_populates="sound_packages")
    created_by = relationship("User", foreign_keys=[created_by_user_id])
    assignments = relationship("PackageAssignment", back_populates="package")
    usage_records = relationship("PackageUsage", back_populates="package")
    # user_assignments = relationship("UserSoundPackage", back_populates="sound_package")  # B2C user assignments (disabled temporarily)


class PackageAssignment(Base):
    """
    Assignment of sound packages to employees
    """
    __tablename__ = "package_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Relationships
    package_id = Column(UUID(as_uuid=True), ForeignKey("sound_packages.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    # Assignment details
    status = Column(SQLEnum(AssignmentStatus), nullable=False, default=AssignmentStatus.ASSIGNED)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    
    # Progress tracking
    sounds_completed = Column(Integer, default=0)
    total_play_time_minutes = Column(Float, default=0.0)
    completion_percentage = Column(Float, default=0.0)
    last_activity_at = Column(DateTime, nullable=True)
    
    # Notes
    assignment_notes = Column(Text, nullable=True)
    completion_notes = Column(Text, nullable=True)
    
    # Relationships
    package = relationship("SoundPackage", back_populates="assignments")
    employee = relationship("User", foreign_keys=[employee_id])
    assigned_by = relationship("User", foreign_keys=[assigned_by_id])
    organization = relationship("Organization")


class PackageUsage(Base):
    """
    Detailed usage tracking for sound packages
    """
    __tablename__ = "package_usage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Relationships
    package_id = Column(UUID(as_uuid=True), ForeignKey("sound_packages.id"), nullable=False)
    assignment_id = Column(UUID(as_uuid=True), ForeignKey("package_assignments.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    # Usage details
    therapy_sound_id = Column(Integer, ForeignKey("therapy_sounds.id"), nullable=True)
    session_start = Column(DateTime, nullable=False)
    session_end = Column(DateTime, nullable=True)
    duration_minutes = Column(Float, default=0.0)
    completion_percentage = Column(Float, default=0.0)
    
    # Context
    device_type = Column(String(50), nullable=True)  # mobile, desktop, tablet
    location = Column(String(100), nullable=True)    # office, home, etc.
    mood_before = Column(String(50), nullable=True)  # stressed, anxious, calm, etc.
    mood_after = Column(String(50), nullable=True)   # improved, same, worse
    
    # Metadata
    recorded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    package = relationship("SoundPackage", back_populates="usage_records")
    assignment = relationship("PackageAssignment")
    employee = relationship("User")
    therapy_sound = relationship("TherapySound")
    organization = relationship("Organization")
