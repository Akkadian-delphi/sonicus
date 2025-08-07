"""
Background Task Examples

This module demonstrates various background tasks for the Sonicus application:
- Email sending tasks
- File processing tasks
- Analytics and reporting tasks
- Maintenance and cleanup tasks
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List

from app.core.background_jobs import background_task, TaskConfig, TaskPriority

logger = logging.getLogger(__name__)


# Email Tasks
@background_task(
    name='app.core.background_jobs.send_welcome_email',
    config=TaskConfig(
        priority=TaskPriority.NORMAL,
        queue='email',
        max_retries=3,
        time_limit=300
    )
)
def send_welcome_email(self, user_email: str, user_name: str) -> Dict[str, Any]:
    """Send welcome email to new users."""
    try:
        logger.info(f"Sending welcome email to {user_email}")
        
        # Simulate email sending
        time.sleep(2)  # Simulate API call delay
        
        return {
            "status": "sent",
            "recipient": user_email,
            "template": "welcome",
            "sent_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to send welcome email to {user_email}: {e}")
        raise


@background_task(
    name='app.core.background_jobs.send_password_reset',
    config=TaskConfig(
        priority=TaskPriority.HIGH,
        queue='email',
        max_retries=5,
        time_limit=180
    )
)
def send_password_reset_email(self, user_email: str, reset_token: str) -> Dict[str, Any]:
    """Send password reset email."""
    try:
        logger.info(f"Sending password reset email to {user_email}")
        
        # Simulate email sending with reset link
        time.sleep(1)
        
        return {
            "status": "sent",
            "recipient": user_email,
            "template": "password_reset",
            "token": reset_token[:8] + "...",  # Truncated for security
            "sent_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to send password reset email: {e}")
        raise


@background_task(
    name='app.core.background_jobs.send_bulk_newsletter',
    config=TaskConfig(
        priority=TaskPriority.LOW,
        queue='email',
        max_retries=2,
        time_limit=1800  # 30 minutes
    )
)
def send_bulk_newsletter(self, recipient_list: List[str], newsletter_content: Dict[str, Any]) -> Dict[str, Any]:
    """Send newsletter to multiple recipients."""
    try:
        logger.info(f"Sending newsletter to {len(recipient_list)} recipients")
        
        sent_count = 0
        failed_count = 0
        
        for email in recipient_list:
            try:
                # Simulate sending to each recipient
                time.sleep(0.1)
                sent_count += 1
                
                # Simulate occasional failures
                if sent_count % 50 == 0:
                    failed_count += 1
                    logger.warning(f"Failed to send to {email}")
                
            except Exception as e:
                failed_count += 1
                logger.warning(f"Failed to send newsletter to {email}: {e}")
        
        return {
            "status": "completed",
            "total_recipients": len(recipient_list),
            "sent_count": sent_count,
            "failed_count": failed_count,
            "newsletter_id": newsletter_content.get("id", "unknown"),
            "completed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to send bulk newsletter: {e}")
        raise


# File Processing Tasks
@background_task(
    name='app.core.background_jobs.process_audio_file',
    config=TaskConfig(
        priority=TaskPriority.HIGH,
        queue='file_processing',
        max_retries=3,
        time_limit=1200  # 20 minutes
    )
)
def process_audio_file(self, file_path: str, processing_options: Dict[str, Any]) -> Dict[str, Any]:
    """Process uploaded audio files."""
    try:
        logger.info(f"Processing audio file: {file_path}")
        
        # Simulate audio processing steps
        steps = [
            "format_validation",
            "metadata_extraction",
            "quality_analysis",
            "thumbnail_generation",
            "format_conversion"
        ]
        
        results = {}
        
        for step in steps:
            logger.info(f"Executing step: {step}")
            time.sleep(2)  # Simulate processing time
            
            results[step] = {
                "status": "completed",
                "duration": 2.0,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        return {
            "status": "processed",
            "file_path": file_path,
            "processing_steps": results,
            "total_duration": len(steps) * 2.0,
            "completed_at": datetime.utcnow().isoformat(),
            "metadata": {
                "format": processing_options.get("format", "mp3"),
                "quality": processing_options.get("quality", "high"),
                "size_mb": 15.7  # Simulated file size
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to process audio file {file_path}: {e}")
        raise


@background_task(
    name='app.core.background_jobs.generate_thumbnails',
    config=TaskConfig(
        priority=TaskPriority.NORMAL,
        queue='file_processing',
        max_retries=2,
        time_limit=600
    )
)
def generate_thumbnails(self, image_path: str, sizes: List[tuple]) -> Dict[str, Any]:
    """Generate thumbnails for images."""
    try:
        logger.info(f"Generating thumbnails for: {image_path}")
        
        generated_thumbs = []
        
        for width, height in sizes:
            # Simulate thumbnail generation
            time.sleep(1)
            
            thumb_path = f"{image_path}_thumb_{width}x{height}.jpg"
            generated_thumbs.append({
                "size": f"{width}x{height}",
                "path": thumb_path,
                "generated_at": datetime.utcnow().isoformat()
            })
        
        return {
            "status": "completed",
            "original_image": image_path,
            "thumbnails": generated_thumbs,
            "total_generated": len(generated_thumbs),
            "completed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to generate thumbnails for {image_path}: {e}")
        raise


# Analytics Tasks
@background_task(
    name='app.core.background_jobs.generate_daily_analytics',
    config=TaskConfig(
        priority=TaskPriority.LOW,
        queue='analytics',
        max_retries=1,
        time_limit=3600  # 1 hour
    )
)
def generate_daily_analytics(self, date: str) -> Dict[str, Any]:
    """Generate daily analytics report."""
    try:
        logger.info(f"Generating daily analytics for {date}")
        
        # Simulate analytics processing
        time.sleep(5)
        
        # Mock analytics data
        analytics = {
            "date": date,
            "metrics": {
                "total_users": 1250,
                "active_users": 890,
                "new_registrations": 45,
                "total_sessions": 2340,
                "avg_session_duration": 1240,  # seconds
                "therapy_sounds_played": 5670,
                "subscription_conversions": 12,
                "revenue": 450.75
            },
            "trends": {
                "user_growth": "+3.6%",
                "engagement": "+1.2%",
                "revenue_growth": "+8.3%"
            },
            "top_sounds": [
                {"name": "Ocean Waves", "plays": 450},
                {"name": "Forest Rain", "plays": 389},
                {"name": "White Noise", "plays": 234}
            ],
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return {
            "status": "completed",
            "analytics": analytics,
            "processing_time": 5.0,
            "completed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to generate daily analytics for {date}: {e}")
        raise


@background_task(
    name='app.core.background_jobs.update_user_recommendations',
    config=TaskConfig(
        priority=TaskPriority.NORMAL,
        queue='analytics',
        max_retries=2,
        time_limit=1800
    )
)
def update_user_recommendations(self, user_id: int) -> Dict[str, Any]:
    """Update personalized recommendations for a user."""
    try:
        logger.info(f"Updating recommendations for user {user_id}")
        
        # Simulate recommendation algorithm
        time.sleep(3)
        
        recommendations = [
            {
                "sound_id": 101,
                "title": "Deep Forest Ambience",
                "score": 0.89,
                "reason": "Similar to recently played sounds"
            },
            {
                "sound_id": 205,
                "title": "Gentle Thunder",
                "score": 0.76,
                "reason": "Popular in your region"
            },
            {
                "sound_id": 312,
                "title": "Meditation Bells",
                "score": 0.71,
                "reason": "Based on your listening history"
            }
        ]
        
        return {
            "status": "updated",
            "user_id": user_id,
            "recommendations": recommendations,
            "algorithm_version": "v2.1",
            "updated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to update recommendations for user {user_id}: {e}")
        raise


# Maintenance Tasks
@background_task(
    name='app.core.background_jobs.cleanup_temp_files',
    config=TaskConfig(
        priority=TaskPriority.LOW,
        queue='maintenance',
        max_retries=1,
        time_limit=1800
    )
)
def cleanup_temp_files(self, older_than_days: int = 7) -> Dict[str, Any]:
    """Clean up temporary files older than specified days."""
    try:
        logger.info(f"Cleaning up temp files older than {older_than_days} days")
        
        # Simulate file cleanup
        time.sleep(3)
        
        # Mock cleanup results
        cleaned_files = [
            {"path": "/tmp/audio_temp_123.wav", "size_mb": 15.2},
            {"path": "/tmp/image_temp_456.jpg", "size_mb": 2.1},
            {"path": "/tmp/processing_789.tmp", "size_mb": 8.7}
        ]
        
        total_size = sum(f["size_mb"] for f in cleaned_files)
        
        return {
            "status": "completed",
            "files_cleaned": len(cleaned_files),
            "total_size_mb": total_size,
            "older_than_days": older_than_days,
            "cleaned_files": cleaned_files,
            "completed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup temp files: {e}")
        raise


@background_task(
    name='app.core.background_jobs.backup_user_data',
    config=TaskConfig(
        priority=TaskPriority.LOW,
        queue='maintenance',
        max_retries=2,
        time_limit=7200  # 2 hours
    )
)
def backup_user_data(self, backup_type: str = "incremental") -> Dict[str, Any]:
    """Backup user data to external storage."""
    try:
        logger.info(f"Starting {backup_type} backup of user data")
        
        # Simulate backup process
        backup_steps = [
            "database_dump",
            "file_compression",
            "encryption",
            "upload_to_storage",
            "verification"
        ]
        
        step_results = {}
        
        for step in backup_steps:
            logger.info(f"Backup step: {step}")
            time.sleep(2)  # Simulate processing time
            
            step_results[step] = {
                "status": "completed",
                "duration": 2.0,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        return {
            "status": "completed",
            "backup_type": backup_type,
            "backup_size_gb": 12.5,
            "steps": step_results,
            "backup_location": "s3://sonicus-backups/user-data/",
            "backup_id": f"backup_{int(time.time())}",
            "completed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to backup user data: {e}")
        raise


# Utility function to submit common tasks
def submit_common_tasks():
    """Submit some common background tasks for testing."""
    from app.core.background_jobs import job_manager
    
    results = []
    
    # Method 1: Use job_manager directly (always works)
    result = job_manager.submit_task(
        'app.core.background_jobs.send_welcome_email',
        args=("test@example.com", "Test User")
    )
    results.append(("welcome_email_direct", result))
    
    # Method 2: Use submit method if available (works when decorator adds it)
    try:
        # Use getattr to safely access the submit method
        submit_func = getattr(send_welcome_email, 'submit', None)
        if submit_func:
            result = submit_func("test2@example.com", "Test User 2")
            results.append(("welcome_email_submit", result))
        else:
            logger.warning("submit method not available on send_welcome_email")
    except Exception as e:
        logger.warning(f"Failed to use submit method: {e}")
    
    # File processing task
    result = job_manager.submit_task(
        'app.core.background_jobs.process_audio_file',
        args=("/path/to/audio.mp3", {"format": "mp3", "quality": "high"})
    )
    results.append(("audio_processing", result))
    
    # Analytics task
    result = job_manager.submit_task(
        'app.core.background_jobs.generate_daily_analytics',
        args=(datetime.now().strftime("%Y-%m-%d"),)
    )
    results.append(("daily_analytics", result))
    
    # Maintenance task
    result = job_manager.submit_task(
        'app.core.background_jobs.cleanup_temp_files',
        args=(7,)
    )
    results.append(("cleanup", result))
    
    return results


def submit_with_submit_method():
    """
    Alternative approach using the dynamically added submit methods.
    This demonstrates how to use the submit methods safely.
    """
    results = []
    
    # Helper function to safely call submit method
    def safe_submit(task_func, task_name: str, *args, **kwargs):
        """Safely call submit method with fallback to job_manager."""
        try:
            submit_method = getattr(task_func, 'submit', None)
            if submit_method and callable(submit_method):
                return submit_method(*args, **kwargs)
            else:
                # Fallback to job_manager
                from app.core.background_jobs import job_manager
                return job_manager.submit_task(task_name, args, kwargs)
        except Exception as e:
            logger.error(f"Failed to submit task {task_name}: {e}")
            raise
    
    # Use the safe submit approach
    result = safe_submit(
        send_welcome_email, 
        'app.core.background_jobs.send_welcome_email',
        "safe@example.com", 
        "Safe User"
    )
    results.append(("safe_welcome_email", result))
    
    result = safe_submit(
        process_audio_file,
        'app.core.background_jobs.process_audio_file',
        "/path/to/safe_audio.mp3",
        {"format": "wav", "quality": "medium"}
    )
    results.append(("safe_audio_processing", result))
    
    return results
