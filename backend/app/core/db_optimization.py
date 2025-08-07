"""
Database Connection Pooling and Optimization

This module provides advanced database connection management with:
- Connection pooling for performance
- Query optimization utilities
- Database health monitoring
- Connection lifecycle management
- Performance metrics collection
"""

import logging
from contextlib import contextmanager
from typing import Dict, Any, Optional, List, Generator
from datetime import datetime, timedelta
import time
import threading
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, StaticPool
from sqlalchemy.exc import DisconnectionError, TimeoutError
import psutil
import json

from app.core.config import settings
from app.core.cache import redis_client

logger = logging.getLogger(__name__)


class DatabaseConnectionPool:
    """
    Advanced database connection pool manager with optimization features.
    """
    
    def __init__(self):
        self.engines: Dict[str, Engine] = {}
        self.session_factories: Dict[str, sessionmaker] = {}
        self.connection_stats = {
            "total_connections": 0,
            "active_connections": 0,
            "pool_checkouts": 0,
            "pool_checkins": 0,
            "query_count": 0,
            "slow_queries": 0,
            "connection_errors": 0,
            "last_health_check": None
        }
        self.slow_query_threshold = 2.0  # seconds
        self._stats_lock = threading.Lock()
    
    def create_optimized_engine(
        self, 
        database_url: str, 
        pool_name: str = "default",
        **kwargs
    ) -> Engine:
        """
        Create an optimized database engine with connection pooling.
        
        Args:
            database_url: Database connection URL
            pool_name: Name for the connection pool
            **kwargs: Additional engine options
            
        Returns:
            Engine: Configured SQLAlchemy engine
        """
        # Default optimized settings
        engine_config = {
            "poolclass": QueuePool,
            "pool_size": getattr(settings, 'DB_POOL_SIZE', 20),
            "max_overflow": getattr(settings, 'DB_MAX_OVERFLOW', 30),
            "pool_timeout": getattr(settings, 'DB_POOL_TIMEOUT', 30),
            "pool_recycle": getattr(settings, 'DB_POOL_RECYCLE', 3600),
            "pool_pre_ping": True,  # Verify connections before use
            "echo": settings.SQL_ECHO,
            "future": True,
            "connect_args": {
                "connect_timeout": 10,
                "application_name": f"sonicus_{pool_name}",
                "options": "-c timezone=UTC"
            }
        }
        
        # Override with custom settings
        engine_config.update(kwargs)
        
        try:
            engine = create_engine(database_url, **engine_config)
            
            # Add event listeners for monitoring
            self._add_engine_listeners(engine, pool_name)
            
            # Store engine reference
            self.engines[pool_name] = engine
            
            # Create session factory
            self.session_factories[pool_name] = sessionmaker(
                bind=engine,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False
            )
            
            logger.info(f"Created optimized database engine '{pool_name}' with pool_size={engine_config['pool_size']}")
            return engine
            
        except Exception as e:
            logger.error(f"Failed to create database engine '{pool_name}': {e}")
            raise
    
    def _add_engine_listeners(self, engine: Engine, pool_name: str):
        """Add event listeners for monitoring and optimization."""
        
        @event.listens_for(engine, "connect")
        def set_connection_settings(dbapi_connection, connection_record):
            """Set optimal connection settings."""
            with dbapi_connection.cursor() as cursor:
                # Set connection-level optimizations
                cursor.execute("SET statement_timeout = '30s'")
                cursor.execute("SET lock_timeout = '10s'")
                cursor.execute("SET idle_in_transaction_session_timeout = '5min'")
                cursor.execute("SET search_path = sonicus, public")
            
            with self._stats_lock:
                self.connection_stats["total_connections"] += 1
        
        @event.listens_for(engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """Track connection checkouts."""
            with self._stats_lock:
                self.connection_stats["active_connections"] += 1
                self.connection_stats["pool_checkouts"] += 1
        
        @event.listens_for(engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            """Track connection checkins."""
            with self._stats_lock:
                self.connection_stats["active_connections"] -= 1
                self.connection_stats["pool_checkins"] += 1
        
        @event.listens_for(engine, "before_cursor_execute")
        def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Track query execution start."""
            context._query_start_time = time.time()
        
        @event.listens_for(engine, "after_cursor_execute")
        def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Track query execution completion and identify slow queries."""
            if hasattr(context, '_query_start_time'):
                query_time = time.time() - context._query_start_time
                
                with self._stats_lock:
                    self.connection_stats["query_count"] += 1
                    
                    if query_time > self.slow_query_threshold:
                        self.connection_stats["slow_queries"] += 1
                        
                        # Log slow query
                        logger.warning(
                            f"Slow query detected ({query_time:.3f}s) in pool '{pool_name}': "
                            f"{statement[:200]}..."
                        )
                        
                        # Store slow query for analysis
                        try:
                            self._store_slow_query(pool_name, statement, query_time, parameters)
                        except Exception as e:
                            logger.error(f"Failed to store slow query: {e}")
    
    def _store_slow_query(self, pool_name: str, statement: str, query_time: float, parameters: Any):
        """Store slow query information for analysis."""
        try:
            slow_query_data = {
                "pool_name": pool_name,
                "statement": statement[:500],  # Truncate long queries
                "execution_time": query_time,
                "parameters": str(parameters)[:200] if parameters else None,
                "timestamp": datetime.utcnow().isoformat(),
                "threshold": self.slow_query_threshold
            }
            
            # Store in Redis with expiration
            key = f"slow_query:{pool_name}:{int(time.time())}"
            redis_client.set_json(key, slow_query_data, expire=7 * 24 * 3600)  # 7 days
            
        except Exception as e:
            logger.error(f"Failed to store slow query data: {e}")
    
    @contextmanager
    def get_db_session(self, pool_name: str = "default") -> Generator[Session, None, None]:
        """
        Get a database session with proper lifecycle management.
        
        Args:
            pool_name: Name of the connection pool to use
            
        Yields:
            Session: Database session
        """
        if pool_name not in self.session_factories:
            raise ValueError(f"Database pool '{pool_name}' not found")
        
        session = self.session_factories[pool_name]()
        
        try:
            yield session
            session.commit()
            
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error in pool '{pool_name}': {e}")
            
            with self._stats_lock:
                self.connection_stats["connection_errors"] += 1
            
            raise
            
        finally:
            session.close()
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get current connection pool statistics."""
        with self._stats_lock:
            stats = self.connection_stats.copy()
        
        # Add pool-specific stats
        pool_stats = {}
        for pool_name, engine in self.engines.items():
            try:
                pool = engine.pool
                pool_stats[pool_name] = {
                    "pool_size": getattr(pool, 'size', lambda: 0)(),
                    "checked_in": getattr(pool, 'checkedin', lambda: 0)(),
                    "checked_out": getattr(pool, 'checkedout', lambda: 0)(),
                    "overflow": getattr(pool, 'overflow', lambda: 0)(),
                    "invalid": getattr(pool, 'invalid', lambda: 0)()
                }
            except Exception as e:
                logger.warning(f"Failed to get pool stats for '{pool_name}': {e}")
                pool_stats[pool_name] = {"error": str(e)}
        
        stats["pool_details"] = pool_stats
        stats["last_updated"] = datetime.utcnow().isoformat()
        
        return stats
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive database health check.
        
        Returns:
            Dict: Health check results
        """
        health_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "healthy",
            "pools": {},
            "system_metrics": {}
        }
        
        try:
            # Check each connection pool
            for pool_name, engine in self.engines.items():
                pool_health = self._check_pool_health(pool_name, engine)
                health_results["pools"][pool_name] = pool_health
                
                if pool_health["status"] != "healthy":
                    health_results["overall_status"] = "degraded"
            
            # System metrics
            health_results["system_metrics"] = {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent
            }
            
            # Update last health check time
            with self._stats_lock:
                self.connection_stats["last_health_check"] = datetime.utcnow().isoformat()
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            health_results["overall_status"] = "unhealthy"
            health_results["error"] = str(e)
        
        return health_results
    
    def _check_pool_health(self, pool_name: str, engine: Engine) -> Dict[str, Any]:
        """Check health of a specific connection pool."""
        pool_health = {
            "status": "healthy",
            "pool_name": pool_name,
            "response_time": None,
            "errors": []
        }
        
        try:
            # Test connection with simple query
            start_time = time.time()
            
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
            
            response_time = time.time() - start_time
            pool_health["response_time"] = response_time
            
            # Check for performance issues
            if response_time > 1.0:
                pool_health["status"] = "slow"
                pool_health["errors"].append(f"Slow response time: {response_time:.3f}s")
            
            # Check pool utilization
            pool = engine.pool
            try:
                pool_size = getattr(pool, 'size', lambda: 1)()
                checked_out = getattr(pool, 'checkedout', lambda: 0)()
                utilization = (checked_out / max(pool_size, 1)) * 100
                
                if utilization > 80:
                    pool_health["status"] = "high_utilization"
                    pool_health["errors"].append(f"High pool utilization: {utilization:.1f}%")
                
                pool_health["pool_stats"] = {
                    "size": pool_size,
                    "checked_out": checked_out,
                    "utilization_percent": utilization
                }
            except Exception as e:
                logger.warning(f"Failed to get pool utilization for '{pool_name}': {e}")
            
        except Exception as e:
            pool_health["status"] = "unhealthy"
            pool_health["errors"].append(str(e))
            logger.error(f"Pool health check failed for '{pool_name}': {e}")
        
        return pool_health
    
    def optimize_queries(self, enable_query_cache: bool = True):
        """Enable query optimization features."""
        if enable_query_cache:
            # Enable query result caching for frequently accessed data
            for pool_name, engine in self.engines.items():
                @event.listens_for(engine, "before_cursor_execute", retval=True)
                def query_cache_check(conn, cursor, statement, parameters, context, executemany):
                    """Check cache before executing query."""
                    if statement.strip().upper().startswith('SELECT'):
                        cache_key = f"query_cache:{hash(statement + str(parameters))}"
                        cached_result = redis_client.get_json(cache_key)
                        
                        if cached_result:
                            context._cached_result = cached_result
                            return statement, parameters
                    
                    return statement, parameters
        
        logger.info("Query optimization features enabled")
    
    def get_slow_queries(self, pool_name: Optional[str] = None, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get slow queries from the last N hours.
        
        Args:
            pool_name: Specific pool name or None for all pools
            hours: Number of hours to look back
            
        Returns:
            List: Slow query records
        """
        try:
            if not redis_client.client:
                return []
            
            pattern = f"slow_query:{pool_name or '*'}:*"
            slow_queries = []
            
            for key in redis_client.client.scan_iter(match=pattern):
                try:
                    key_str = key.decode() if isinstance(key, bytes) else key
                    query_data = redis_client.get_json(key_str)
                    
                    if query_data and isinstance(query_data, dict):
                        query_time = datetime.fromisoformat(query_data.get("timestamp", ""))
                        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
                        
                        if query_time >= cutoff_time:
                            slow_queries.append(query_data)
                            
                except Exception as e:
                    logger.warning(f"Failed to process slow query key {key}: {e}")
                    continue
            
            # Sort by execution time (slowest first)
            slow_queries.sort(key=lambda x: x.get("execution_time", 0), reverse=True)
            
            return slow_queries
            
        except Exception as e:
            logger.error(f"Failed to get slow queries: {e}")
            return []
    
    def cleanup_connections(self):
        """Clean up and dispose of all connection pools."""
        try:
            for pool_name, engine in self.engines.items():
                engine.dispose()
                logger.info(f"Disposed database engine '{pool_name}'")
            
            self.engines.clear()
            self.session_factories.clear()
            
        except Exception as e:
            logger.error(f"Error during connection cleanup: {e}")


# Global instance
db_pool_manager = DatabaseConnectionPool()


# Utility functions for easy access
def get_optimized_engine(database_url: str, pool_name: str = "default") -> Engine:
    """Create an optimized database engine."""
    return db_pool_manager.create_optimized_engine(database_url, pool_name)


@contextmanager
def get_db_session(pool_name: str = "default") -> Generator[Session, None, None]:
    """Get a database session from the connection pool."""
    with db_pool_manager.get_db_session(pool_name) as session:
        yield session


def get_db_health() -> Dict[str, Any]:
    """Get database health status."""
    return db_pool_manager.health_check()


def get_db_stats() -> Dict[str, Any]:
    """Get database connection statistics."""
    return db_pool_manager.get_connection_stats()
