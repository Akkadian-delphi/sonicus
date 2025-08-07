"""
Comprehensive Error Handling and Logging System

This module provides advanced error handling and structured logging with:
- Structured logging with JSON format
- Error tracking and analytics
- Performance monitoring
- Log aggregation and filtering
- Error alerting and notifications
- Request/response logging
- Error recovery mechanisms
"""

import logging
import json
import time
import traceback
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from functools import wraps
from dataclasses import dataclass, asdict
from enum import Enum
import threading
from pathlib import Path

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
import psutil

from app.core.redis_caching import advanced_cache

# Configure root logger early
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)

logger = logging.getLogger(__name__)


class LogLevel(Enum):
    """Log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"    
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ErrorCategory(Enum):
    """Error categories for classification."""
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATABASE = "database"
    EXTERNAL_API = "external_api"
    FILE_SYSTEM = "file_system"
    NETWORK = "network"
    SYSTEM = "system"
    BUSINESS_LOGIC = "business_logic"
    UNKNOWN = "unknown"


@dataclass
class LogEntry:
    """Structured log entry."""
    timestamp: datetime
    level: str
    message: str
    logger_name: str
    module: str
    function: str
    line_number: int
    thread_id: str
    process_id: int
    request_id: Optional[str] = None
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None
    error_category: Optional[str] = None
    stack_trace: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), default=str)


@dataclass
class ErrorMetrics:
    """Error tracking metrics."""
    error_id: str
    category: ErrorCategory
    message: str
    count: int
    first_seen: datetime
    last_seen: datetime
    affected_users: List[int]
    stack_trace: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        
        # Extract extra information
        extra_data = {}
        for key, value in record.__dict__.items():
            if key not in ('name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                          'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process', 'message'):
                extra_data[key] = value
        
        log_entry = LogEntry(
            timestamp=datetime.fromtimestamp(record.created),
            level=record.levelname,
            message=record.getMessage(),
            logger_name=record.name,
            module=record.module,
            function=record.funcName,
            line_number=record.lineno,
            thread_id=str(record.thread),
            process_id=record.process or 0,
            request_id=getattr(record, 'request_id', None),
            user_id=getattr(record, 'user_id', None),
            session_id=getattr(record, 'session_id', None),
            extra_data=extra_data if extra_data else None,
            error_category=getattr(record, 'error_category', None),
            stack_trace=self.formatException(record.exc_info) if record.exc_info else None
        )
        
        return log_entry.to_json()


class LogStorage:
    """Storage backend for logs and metrics."""
    
    def __init__(self):
        self.cache = advanced_cache
        self.local_storage = []  # Fallback storage
        self.max_local_entries = 10000
    
    def store_log(self, log_entry: LogEntry):
        """Store a log entry."""
        try:
            # Try to store in cache/database
            success = self.cache.set(
                'logs',
                f"{log_entry.timestamp.isoformat()}_{log_entry.thread_id}",
                log_entry.to_dict(),
                ttl=86400 * 7  # 7 days
            )
            
            if not success:
                # Fallback to local storage
                self.local_storage.append(log_entry.to_dict())
                
                # Keep only recent entries
                if len(self.local_storage) > self.max_local_entries:
                    self.local_storage = self.local_storage[-self.max_local_entries:]
                    
        except Exception as e:
            # Last resort: write to file
            try:
                with open('error_logs.json', 'a') as f:
                    f.write(log_entry.to_json() + '\n')
            except Exception:
                pass  # Can't do much more
    
    def get_recent_logs(self, limit: int = 100, level: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recent log entries."""
        try:
            # For now, return from local storage
            # In production, this would query the database/cache
            logs = self.local_storage[-limit:]
            
            if level:
                logs = [log for log in logs if log.get('level') == level]
            
            return list(reversed(logs))  # Most recent first
            
        except Exception as e:
            logger.error(f"Failed to retrieve recent logs: {e}")
            return []
    
    def store_error_metrics(self, error_metrics: ErrorMetrics):
        """Store error metrics."""
        try:
            self.cache.set(
                'error_metrics',
                error_metrics.error_id,
                asdict(error_metrics),
                ttl=86400 * 30  # 30 days
            )
        except Exception as e:
            logger.error(f"Failed to store error metrics: {e}")


class ErrorTracker:
    """Track and analyze errors."""
    
    def __init__(self, storage: LogStorage):
        self.storage = storage
        self.error_counts: Dict[str, int] = {}
        self.error_cache: Dict[str, ErrorMetrics] = {}
        self._lock = threading.Lock()
    
    def track_error(
        self, 
        exception: Exception, 
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        user_id: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Track an error occurrence."""
        
        # Generate error ID based on error type and message
        error_signature = f"{type(exception).__name__}:{str(exception)}"
        error_id = f"error_{hash(error_signature) % 1000000}"
        
        with self._lock:
            if error_id in self.error_cache:
                # Update existing error
                error_metrics = self.error_cache[error_id]
                error_metrics.count += 1
                error_metrics.last_seen = datetime.utcnow()
                
                if user_id and user_id not in error_metrics.affected_users:
                    error_metrics.affected_users.append(user_id)
                    
            else:
                # Create new error metrics
                error_metrics = ErrorMetrics(
                    error_id=error_id,
                    category=category,
                    message=str(exception),
                    count=1,
                    first_seen=datetime.utcnow(),
                    last_seen=datetime.utcnow(),
                    affected_users=[user_id] if user_id else [],
                    stack_trace=''.join(traceback.format_exception(type(exception), exception, exception.__traceback__)),
                    context=context
                )
                
                self.error_cache[error_id] = error_metrics
            
            # Store updated metrics
            self.storage.store_error_metrics(error_metrics)
            
            return error_id
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for the specified time period."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            recent_errors = []
            total_errors = 0
            categories = {}
            
            for error_metrics in self.error_cache.values():
                if error_metrics.last_seen >= cutoff_time:
                    recent_errors.append({
                        'error_id': error_metrics.error_id,
                        'category': error_metrics.category.value,
                        'message': error_metrics.message,
                        'count': error_metrics.count,
                        'affected_users': len(error_metrics.affected_users),
                        'last_seen': error_metrics.last_seen.isoformat()
                    })
                    
                    total_errors += error_metrics.count
                    category = error_metrics.category.value
                    categories[category] = categories.get(category, 0) + error_metrics.count
            
            # Sort by count descending
            recent_errors.sort(key=lambda x: x['count'], reverse=True)
            
            return {
                'time_period_hours': hours,
                'total_errors': total_errors,
                'unique_errors': len(recent_errors),
                'error_categories': categories,
                'top_errors': recent_errors[:10],
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate error summary: {e}")
            return {'error': str(e)}


class PerformanceMonitor:
    """Monitor application performance."""
    
    def __init__(self):
        self.request_times: List[float] = []
        self.max_samples = 1000
        self._lock = threading.Lock()
    
    def record_request_time(self, duration: float):
        """Record a request duration."""
        with self._lock:
            self.request_times.append(duration)
            
            # Keep only recent samples
            if len(self.request_times) > self.max_samples:
                self.request_times = self.request_times[-self.max_samples:]
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        try:
            with self._lock:
                request_times = self.request_times.copy()
            
            if not request_times:
                return {'error': 'No performance data available'}
            
            # Calculate statistics
            avg_time = sum(request_times) / len(request_times)
            min_time = min(request_times)
            max_time = max(request_times)
            
            # Calculate percentiles
            sorted_times = sorted(request_times)
            p50 = sorted_times[int(len(sorted_times) * 0.5)]
            p90 = sorted_times[int(len(sorted_times) * 0.9)]
            p95 = sorted_times[int(len(sorted_times) * 0.95)]
            p99 = sorted_times[int(len(sorted_times) * 0.99)]
            
            # System metrics
            system_stats = {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage_percent': psutil.disk_usage('/').percent,
                'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else None
            }
            
            return {
                'request_stats': {
                    'total_requests': len(request_times),
                    'avg_response_time': avg_time,
                    'min_response_time': min_time,
                    'max_response_time': max_time,
                    'p50_response_time': p50,
                    'p90_response_time': p90,
                    'p95_response_time': p95,
                    'p99_response_time': p99
                },
                'system_stats': system_stats,
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get performance stats: {e}")
            return {'error': str(e)}


class AdvancedLogger:
    """
    Advanced logging system with structured logging and error tracking.
    """
    
    def __init__(self):
        self.storage = LogStorage()
        self.error_tracker = ErrorTracker(self.storage)
        self.performance_monitor = PerformanceMonitor()
        
        # Configure structured logging
        self.setup_structured_logging()
        
        # Application logger
        self.logger = logging.getLogger('sonicus')
        
        # Request context
        self._request_context: Dict[str, Any] = {}
        self._context_lock = threading.Lock()
    
    def setup_structured_logging(self):
        """Set up structured JSON logging."""
        try:
            # Create logs directory
            logs_dir = Path('logs')
            logs_dir.mkdir(exist_ok=True)
            
            # Configure structured formatter
            structured_formatter = StructuredFormatter()
            
            # File handler for structured logs
            file_handler = logging.FileHandler(logs_dir / 'structured.log')
            file_handler.setFormatter(structured_formatter)
            file_handler.setLevel(logging.INFO)
            
            # Error file handler
            error_handler = logging.FileHandler(logs_dir / 'errors.log')
            error_handler.setFormatter(structured_formatter)
            error_handler.setLevel(logging.ERROR)
            
            # Console handler for development
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            
            # Configure root logger
            root_logger = logging.getLogger()
            root_logger.handlers.clear()  # Remove default handlers
            root_logger.addHandler(file_handler)
            root_logger.addHandler(error_handler)
            root_logger.addHandler(console_handler)
            root_logger.setLevel(logging.INFO)
            
        except Exception as e:
            print(f"Failed to setup structured logging: {e}")
    
    def set_request_context(
        self, 
        request_id: str,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        **kwargs
    ):
        """Set request context for logging."""
        with self._context_lock:
            self._request_context = {
                'request_id': request_id,
                'user_id': user_id,
                'session_id': session_id,
                **kwargs
            }
    
    def clear_request_context(self):
        """Clear request context."""
        with self._context_lock:
            self._request_context = {}
    
    def _add_context(self, extra: Dict[str, Any]) -> Dict[str, Any]:
        """Add request context to log extra data."""
        with self._context_lock:
            context_data = self._request_context.copy()
        
        if extra:
            context_data.update(extra)
        
        return context_data
    
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log info message."""
        self.logger.info(message, extra=self._add_context(extra or {}))
    
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log warning message."""
        self.logger.warning(message, extra=self._add_context(extra or {}))
    
    def error(
        self, 
        message: str, 
        exception: Optional[Exception] = None,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        extra: Optional[Dict[str, Any]] = None
    ):
        """Log error message and track the error."""
        context_data = self._add_context(extra or {})
        context_data['error_category'] = category.value
        
        if exception:
            # Track the error
            error_id = self.error_tracker.track_error(
                exception, 
                category, 
                context_data.get('user_id'),
                context_data
            )
            context_data['error_id'] = error_id
            
            self.logger.error(message, exc_info=exception, extra=context_data)
        else:
            self.logger.error(message, extra=context_data)
    
    def critical(
        self, 
        message: str, 
        exception: Optional[Exception] = None,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        extra: Optional[Dict[str, Any]] = None
    ):
        """Log critical message."""
        context_data = self._add_context(extra or {})
        context_data['error_category'] = category.value
        
        if exception:
            error_id = self.error_tracker.track_error(
                exception, 
                category, 
                context_data.get('user_id'),
                context_data
            )
            context_data['error_id'] = error_id
            
            self.logger.critical(message, exc_info=exception, extra=context_data)
        else:
            self.logger.critical(message, extra=context_data)
    
    def get_logs(self, limit: int = 100, level: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recent logs."""
        return self.storage.get_recent_logs(limit, level)
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary."""
        return self.error_tracker.get_error_summary(hours)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        return self.performance_monitor.get_performance_stats()
    
    def record_request_performance(self, duration: float):
        """Record request performance."""
        self.performance_monitor.record_request_time(duration)


# Global logger instance
advanced_logger = AdvancedLogger()


# Decorators and middleware
def log_exceptions(
    category: ErrorCategory = ErrorCategory.UNKNOWN,
    re_raise: bool = True
):
    """
    Decorator to automatically log exceptions.
    
    Args:
        category: Error category for classification
        re_raise: Whether to re-raise the exception
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                advanced_logger.error(
                    f"Exception in {func.__name__}: {str(e)}",
                    exception=e,
                    category=category,
                    extra={
                        'function': func.__name__,
                        'module': func.__module__,
                        'args': str(args)[:200],  # Truncate for privacy
                        'kwargs_keys': list(kwargs.keys())
                    }
                )
                
                if re_raise:
                    raise
                else:
                    return None
        
        return wrapper
    return decorator


def monitor_performance(func: Callable) -> Callable:
    """Decorator to monitor function performance."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            advanced_logger.record_request_performance(duration)
            
            if duration > 1.0:  # Log slow operations
                advanced_logger.warning(
                    f"Slow operation detected: {func.__name__} took {duration:.2f}s",
                    extra={
                        'function': func.__name__,
                        'duration': duration,
                        'performance_issue': True
                    }
                )
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            advanced_logger.record_request_performance(duration)
            raise
    
    return wrapper


# Request logging middleware
async def request_logging_middleware(request: Request, call_next):
    """Middleware to log all requests and responses."""
    
    # Generate request ID
    request_id = f"req_{int(time.time() * 1000)}_{hash(str(request.url)) % 10000}"
    
    # Set context
    advanced_logger.set_request_context(
        request_id=request_id,
        # user_id would be extracted from authentication
        # session_id would be extracted from session
    )
    
    start_time = time.time()
    
    # Log request
    advanced_logger.info(
        f"Request started: {request.method} {request.url.path}",
        extra={
            'request_method': request.method,
            'request_path': str(request.url.path),
            'request_query': str(request.url.query),
            'client_ip': request.client.host if request.client else 'unknown',
            'user_agent': request.headers.get('user-agent', 'unknown')
        }
    )
    
    try:
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        advanced_logger.record_request_performance(duration)
        
        # Log successful response
        advanced_logger.info(
            f"Request completed: {request.method} {request.url.path} - {response.status_code}",
            extra={
                'response_status': response.status_code,
                'response_time': duration,
                'response_size': getattr(response, 'content_length', 0)
            }
        )
        
        return response
        
    except Exception as e:
        # Calculate duration
        duration = time.time() - start_time
        advanced_logger.record_request_performance(duration)
        
        # Log error
        advanced_logger.error(
            f"Request failed: {request.method} {request.url.path}",
            exception=e,
            category=ErrorCategory.SYSTEM,
            extra={
                'response_time': duration,
                'error_during_request': True
            }
        )
        
        # Return error response
        return JSONResponse(
            status_code=500,
            content={
                'error': 'Internal server error',
                'request_id': request_id,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
    
    finally:
        # Clear context
        advanced_logger.clear_request_context()


# Convenience functions
def get_logs(limit: int = 100, level: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get recent logs."""
    return advanced_logger.get_logs(limit, level)


def get_error_summary(hours: int = 24) -> Dict[str, Any]:
    """Get error summary."""
    return advanced_logger.get_error_summary(hours)


def get_performance_stats() -> Dict[str, Any]:
    """Get performance statistics."""
    return advanced_logger.get_performance_stats()


def get_system_health() -> Dict[str, Any]:
    """Get comprehensive system health information."""
    try:
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'errors': get_error_summary(24),
            'performance': get_performance_stats(),
            'system_info': {
                'python_version': sys.version,
                'platform': sys.platform,
                'process_id': os.getpid(),
                'working_directory': os.getcwd()
            }
        }
    except Exception as e:
        return {'error': f'Failed to get system health: {e}'}
