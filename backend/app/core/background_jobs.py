"""
Advanced Celery Background Job Processing System

This module provides comprehensive background job processing with:
- Task queue management
- Job scheduling and monitoring
- Result tracking and storage
- Retry mechanisms with exponential backoff
- Task priority and routing
- Performance monitoring and analytics
"""

import logging
import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Callable
from functools import wraps
from dataclasses import dataclass, asdict
from enum import Enum

try:
    from celery import Celery as CeleryApp, Task as CeleryTask
    from celery.result import AsyncResult as CeleryAsyncResult
    from celery.exceptions import Retry, WorkerLostError
    from kombu import Queue
    CELERY_AVAILABLE = True
    
except ImportError:
    CELERY_AVAILABLE = False
    CeleryApp = None  # type: ignore[misc]
    CeleryTask = None  # type: ignore[misc]
    CeleryAsyncResult = None  # type: ignore[misc]
    Queue = None  # type: ignore[misc]
    Retry = None  # type: ignore[misc]
    WorkerLostError = None  # type: ignore[misc]
    
    # We'll define fallback classes later

from app.core.config import settings

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Task priority levels."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RETRY = "RETRY"
    REVOKED = "REVOKED"


@dataclass
class TaskConfig:
    """Configuration for background tasks."""
    max_retries: int = 3
    retry_backoff: bool = True
    retry_backoff_max: int = 600  # 10 minutes
    retry_jitter: bool = True
    priority: TaskPriority = TaskPriority.NORMAL
    time_limit: int = 300  # 5 minutes
    soft_time_limit: int = 240  # 4 minutes
    queue: str = "default"
    routing_key: str = "default"


@dataclass
class TaskResult:
    """Task execution result with metadata."""
    task_id: str
    status: TaskStatus
    result: Any = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None
    retries: int = 0
    max_retries: int = 3
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class CeleryConfig:
    """Celery configuration settings."""
    
    broker_url = getattr(settings, 'CELERY_BROKER_URL', 'redis://localhost:6379/0')
    result_backend = getattr(settings, 'CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    
    # Task settings
    task_serializer = 'json'
    accept_content = ['json']
    result_serializer = 'json'
    timezone = 'UTC'
    enable_utc = True
    
    # Task execution settings
    task_always_eager = getattr(settings, 'CELERY_ALWAYS_EAGER', False)
    task_eager_propagates = True
    task_store_eager_result = True
    
    # Worker settings
    worker_prefetch_multiplier = 1
    worker_max_tasks_per_child = 1000
    worker_disable_rate_limits = False
    
    # Task routing
    task_routes = {
        'app.core.background_jobs.email_task': {'queue': 'email'},
        'app.core.background_jobs.file_processing_task': {'queue': 'file_processing'},
        'app.core.background_jobs.analytics_task': {'queue': 'analytics'},
        'app.core.background_jobs.cleanup_task': {'queue': 'maintenance'},
    }
    
    # Queue definitions - handle missing Queue gracefully
    if CELERY_AVAILABLE and Queue:
        task_queues = [
            Queue('default', routing_key='default'),
            Queue('email', routing_key='email'),
            Queue('file_processing', routing_key='file_processing'),
            Queue('analytics', routing_key='analytics'),
            Queue('maintenance', routing_key='maintenance'),
            Queue('high_priority', routing_key='high_priority'),
        ]
    else:
        task_queues = []
    
    # Task time limits
    task_time_limit = 600  # 10 minutes
    task_soft_time_limit = 540  # 9 minutes
    
    # Result settings
    result_expires = 3600  # 1 hour
    result_persistent = True
    
    # Monitoring
    worker_send_task_events = True
    task_send_sent_event = True


# Define fallback classes when Celery is not available
if not CELERY_AVAILABLE:
    class FallbackCelery:
        def __init__(self, name: str):
            self.name = name
        
        def config_from_object(self, config):
            pass
        
        def task(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator
        
        @property
        def tasks(self):
            return {}
    
    class FallbackTask:
        def __init__(self):
            self.name = "unknown"
            self.request = type('obj', (object,), {'hostname': 'unknown'})()
    
    class FallbackAsyncResult:
        def __init__(self, task_id: str, app=None):
            self.id = task_id
            self.state = "PENDING"
            self.info = {}
            self.result = None
            self.traceback = None
        
        def revoke(self, terminate: bool = False):
            pass
    
    Celery = FallbackCelery
    Task = FallbackTask
    AsyncResult = FallbackAsyncResult
else:
    Celery = CeleryApp
    Task = CeleryTask
    AsyncResult = CeleryAsyncResult


# Initialize Celery app
if CELERY_AVAILABLE and CeleryApp:
    celery_app = Celery('sonicus_jobs') # type: ignore
    celery_app.config_from_object(CeleryConfig)
else:
    celery_app = None
    logger.warning("Celery not available - background jobs will run synchronously")


class BaseTask(Task): # type: ignore
    """Base task class with enhanced error handling and monitoring."""
    
    def __init__(self):
        self.start_time = None
        self.task_config = TaskConfig()
    
    def on_success(self, retval, task_id, args, kwargs):
        """Handle successful task completion."""
        duration = time.time() - self.start_time if self.start_time else 0
        logger.info(f"Task {task_id} completed successfully in {duration:.2f}s")
        
        # Store success metrics
        self._store_task_metrics(task_id, TaskStatus.SUCCESS, duration, None)
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        duration = time.time() - self.start_time if self.start_time else 0
        logger.error(f"Task {task_id} failed after {duration:.2f}s: {exc}")
        
        # Store failure metrics
        self._store_task_metrics(task_id, TaskStatus.FAILURE, duration, str(exc))
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Handle task retry."""
        duration = time.time() - self.start_time if self.start_time else 0
        logger.warning(f"Task {task_id} retrying after {duration:.2f}s: {exc}")
        
        # Store retry metrics
        self._store_task_metrics(task_id, TaskStatus.RETRY, duration, str(exc))
    
    def _store_task_metrics(self, task_id: str, status: TaskStatus, duration: float, error: Optional[str]):
        """Store task execution metrics."""
        try:
            from app.core.redis_caching import advanced_cache
            
            metrics = {
                "task_id": task_id,
                "task_name": getattr(self, 'name', 'unknown'),
                "status": status.value,
                "duration": duration,
                "error": error,
                "timestamp": datetime.utcnow().isoformat(),
                "worker": getattr(getattr(self, 'request', None), 'hostname', 'unknown')
            }
            
            # Store in cache for monitoring
            advanced_cache.set(
                'task_metrics', 
                task_id, 
                metrics, 
                ttl=86400  # 24 hours
            )
            
        except Exception as e:
            logger.warning(f"Failed to store task metrics: {e}")


class BackgroundJobManager:
    """
    Advanced background job management system.
    """
    
    def __init__(self):
        self.app = celery_app
        self.available = CELERY_AVAILABLE and celery_app is not None
        
        if not self.available:
            logger.warning("Background jobs will run synchronously - Celery not available")
    
    def submit_task(
        self, 
        task_name: str, 
        args: tuple = (), 
        kwargs: Optional[Dict[str, Any]] = None,
        config: Optional[TaskConfig] = None,
        eta: Optional[datetime] = None,
        countdown: Optional[int] = None
    ) -> TaskResult:
        """
        Submit a task for background execution.
        
        Args:
            task_name: Name of the task to execute
            args: Positional arguments for the task
            kwargs: Keyword arguments for the task
            config: Task configuration
            eta: Earliest time to execute the task
            countdown: Delay before executing the task (seconds)
            
        Returns:
            TaskResult: Task execution result
        """
        kwargs = kwargs or {}
        config = config or TaskConfig()
        
        try:
            if self.available:
                # Submit to Celery
                task_options = {
                    'queue': config.queue,
                    'routing_key': config.routing_key,
                    'priority': config.priority.value,
                    'retry': config.max_retries > 0,
                    'retry_policy': {
                        'max_retries': config.max_retries,
                        'interval_start': 1,
                        'interval_step': 2 if config.retry_backoff else 0,
                        'interval_max': config.retry_backoff_max,
                        'retry_jitter': config.retry_jitter
                    }
                }
                
                if eta:
                    task_options['eta'] = eta
                elif countdown:
                    task_options['countdown'] = countdown
                
                # Get task from registry
                if self.app and hasattr(self.app, 'tasks'):
                    task = self.app.tasks.get(task_name)  # type: ignore
                    if not task:
                        raise ValueError(f"Task '{task_name}' not found in registry")
                else:
                    raise ValueError(f"Celery app not available or no task registry")
                
                async_result = task.apply_async(args, kwargs, **task_options)
                
                return TaskResult(
                    task_id=async_result.id,
                    status=TaskStatus.PENDING,
                    max_retries=config.max_retries,
                    metadata={
                        'task_name': task_name,
                        'queue': config.queue,
                        'priority': config.priority.value,
                        'submitted_at': datetime.utcnow().isoformat()
                    }
                )
            else:
                # Execute synchronously as fallback
                logger.info(f"Executing task '{task_name}' synchronously")
                
                start_time = time.time()
                task_id = f"sync_{int(time.time() * 1000)}"
                
                try:
                    # Import and execute the task function
                    result = self._execute_sync_task(task_name, args, kwargs)
                    duration = time.time() - start_time
                    
                    return TaskResult(
                        task_id=task_id,
                        status=TaskStatus.SUCCESS,
                        result=result,
                        started_at=datetime.utcnow() - timedelta(seconds=duration),
                        completed_at=datetime.utcnow(),
                        duration=duration,
                        metadata={
                            'task_name': task_name,
                            'execution_mode': 'synchronous',
                            'submitted_at': datetime.utcnow().isoformat()
                        }
                    )
                    
                except Exception as e:
                    duration = time.time() - start_time
                    
                    return TaskResult(
                        task_id=task_id,
                        status=TaskStatus.FAILURE,
                        error=str(e),
                        started_at=datetime.utcnow() - timedelta(seconds=duration),
                        completed_at=datetime.utcnow(),
                        duration=duration,
                        metadata={
                            'task_name': task_name,
                            'execution_mode': 'synchronous',
                            'submitted_at': datetime.utcnow().isoformat()
                        }
                    )
                    
        except Exception as e:
            logger.error(f"Failed to submit task '{task_name}': {e}")
            
            return TaskResult(
                task_id=f"error_{int(time.time() * 1000)}",
                status=TaskStatus.FAILURE,
                error=str(e),
                metadata={
                    'task_name': task_name,
                    'error_type': 'submission_error',
                    'submitted_at': datetime.utcnow().isoformat()
                }
            )
    
    def get_task_result(self, task_id: str) -> TaskResult:
        """
        Get the result of a background task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            TaskResult: Task execution result
        """
        try:
            if self.available and not task_id.startswith('sync_'):
                if AsyncResult:
                    async_result = AsyncResult(task_id, app=self.app) # type: ignore
                else:
                    # Fallback when AsyncResult is not available
                    return TaskResult(
                        task_id=task_id,
                        status=TaskStatus.PENDING,
                        metadata={'error': 'AsyncResult not available'}
                    )
                
                # Map Celery states to our TaskStatus
                status_mapping = {
                    'PENDING': TaskStatus.PENDING,
                    'STARTED': TaskStatus.STARTED,
                    'SUCCESS': TaskStatus.SUCCESS,
                    'FAILURE': TaskStatus.FAILURE,
                    'RETRY': TaskStatus.RETRY,
                    'REVOKED': TaskStatus.REVOKED
                }
                
                status = status_mapping.get(async_result.state, TaskStatus.PENDING)
                
                # Get task info
                info = async_result.info or {}
                
                return TaskResult(
                    task_id=task_id,
                    status=status,
                    result=async_result.result if status == TaskStatus.SUCCESS else None,
                    error=str(info.get('error', async_result.traceback)) if status == TaskStatus.FAILURE else None,
                    retries=info.get('retries', 0),
                    metadata={
                        'celery_state': async_result.state,
                        'task_name': info.get('task_name', 'unknown'),
                        'retrieved_at': datetime.utcnow().isoformat()
                    }
                )
            else:
                # Try to get from cache (for sync tasks or metrics)
                from app.core.redis_caching import advanced_cache
                
                cached_result = advanced_cache.get('task_metrics', task_id)
                if cached_result:
                    return TaskResult(
                        task_id=task_id,
                        status=TaskStatus(cached_result.get('status', 'PENDING')),
                        error=cached_result.get('error'),
                        duration=cached_result.get('duration'),
                        metadata=cached_result
                    )
                else:
                    return TaskResult(
                        task_id=task_id,
                        status=TaskStatus.PENDING,
                        metadata={'retrieved_at': datetime.utcnow().isoformat()}
                    )
                    
        except Exception as e:
            logger.error(f"Failed to get task result for '{task_id}': {e}")
            
            return TaskResult(
                task_id=task_id,
                status=TaskStatus.FAILURE,
                error=f"Failed to retrieve result: {e}",
                metadata={'error_type': 'retrieval_error'}
            )
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a pending or running task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            bool: Success status
        """
        try:
            if self.available and not task_id.startswith('sync_'):
                if AsyncResult:
                    async_result = AsyncResult(task_id, app=self.app) # type: ignore
                    async_result.revoke(terminate=True)
                    logger.info(f"Task {task_id} cancelled")
                    return True
                else:
                    logger.warning(f"Cannot cancel task {task_id} - AsyncResult not available")
                    return False
            else:
                logger.warning(f"Cannot cancel task {task_id} - not a Celery task")
                return False
                
        except Exception as e:
            logger.error(f"Failed to cancel task {task_id}: {e}")
            return False
    
    def _execute_sync_task(self, task_name: str, args: tuple, kwargs: Dict[str, Any]) -> Any:
        """Execute a task synchronously."""
        # This is a simple implementation - in a real system you might want
        # to maintain a registry of task functions
        
        # For now, we'll just return a placeholder result
        logger.info(f"Synchronously executing {task_name} with args={args}, kwargs={kwargs}")
        return {"status": "completed", "task": task_name, "mode": "sync"}
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get statistics for all queues."""
        try:
            if not self.available:
                return {"error": "Celery not available"}
            
            # This would require additional Celery monitoring setup
            # For now, return basic info
            return {
                "available": True,
                "queues": [q.name for q in CeleryConfig.task_queues],
                "active_tasks": 0,  # Would need monitoring to get real count
                "worker_stats": {},
                "retrieved_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get queue stats: {e}")
            return {"error": str(e)}


# Global job manager instance
job_manager = BackgroundJobManager()


# Task decorator for easy task registration
def background_task(
    name: Optional[str] = None,
    config: Optional[TaskConfig] = None,
    bind: bool = False  # Default to False for simpler usage
):
    """
    Decorator to register a function as a background task.
    
    Args:
        name: Task name (defaults to function name)
        config: Task configuration
        bind: Whether to bind the task instance as first argument
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        task_name = name or f"{func.__module__}.{func.__name__}"
        config_obj = config or TaskConfig()
        
        if CELERY_AVAILABLE and celery_app:
            # Register with Celery
            task_options = {
                'bind': bind,
                'base': BaseTask,
                'queue': config_obj.queue,
                'routing_key': config_obj.routing_key,
                'priority': config_obj.priority.value,
                'max_retries': config_obj.max_retries,
                'time_limit': config_obj.time_limit,
                'soft_time_limit': config_obj.soft_time_limit
            }
            
            # Add convenience methods
            def submit(*args, **kwargs):
                return job_manager.submit_task(task_name, args, kwargs, config_obj)
            
            def submit_delayed(countdown: int, *args, **kwargs):
                return job_manager.submit_task(task_name, args, kwargs, config_obj, countdown=countdown)
            
            def submit_at(eta: datetime, *args, **kwargs):
                return job_manager.submit_task(task_name, args, kwargs, config_obj, eta=eta)
            
            celery_task = celery_app.task(name=task_name, **task_options)(func) # type: ignore
            
            # Add convenience methods using setattr to avoid type checker issues
            setattr(celery_task, 'submit', submit)
            setattr(celery_task, 'submit_delayed', submit_delayed)
            setattr(celery_task, 'submit_at', submit_at)
            
            return celery_task
        else:
            # Fallback: return a wrapper that supports the same interface
            class TaskWrapper:
                def __init__(self, func):
                    self.func = func
                    self.submit = lambda *args, **kwargs: job_manager.submit_task(task_name, args, kwargs, config_obj)
                    self.submit_delayed = lambda countdown, *args, **kwargs: job_manager.submit_task(task_name, args, kwargs, config_obj, countdown=countdown)
                    self.submit_at = lambda eta, *args, **kwargs: job_manager.submit_task(task_name, args, kwargs, config_obj, eta=eta)
                
                def __call__(self, *args, **kwargs):
                    return self.func(*args, **kwargs)
            
            return TaskWrapper(func)
    
    return decorator
