"""
Database session management.
"""
import logging
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Extract just the base URL without options for engine creation
base_db_url = settings.DATABASE_URL
if base_db_url and '?' in base_db_url:
    base_db_url = base_db_url.split('?')[0]

# Print database connection info (without password)
if base_db_url:
    # Mask password for logging
    safe_connection = base_db_url
    if '@' in safe_connection:
        parts = safe_connection.split('@')
        connection_prefix = parts[0]
        if ':' in connection_prefix:
            user_pass = connection_prefix.split(':')
            if len(user_pass) > 2:  # Handle cases with multiple colons
                safe_connection = f"{user_pass[0]}:***@{parts[1]}"
            else:
                safe_connection = f"{user_pass[0]}:***@{parts[1]}"
    
    logger.info(f"Connecting to database: {safe_connection}")

# Ensure we have a valid database URL
if not base_db_url:
    raise ValueError("DATABASE_URL is not configured in settings")

# Create SQLAlchemy engine with psycopg2 instead of asyncpg for schema handling
# We'll strip the asyncpg part and any query parameters
connection_url = base_db_url.replace("postgresql+asyncpg", "postgresql")
logger.debug(f"Using connection URL: {connection_url} (with masked password)")

# Create SQLAlchemy engine
engine = create_engine(
    connection_url,
    pool_size=settings.CONNECTION_POOL_SIZE,
    max_overflow=settings.MAX_OVERFLOW,
    echo=settings.SQL_ECHO
)

# Set schema on connection using event listener
@event.listens_for(engine, "connect")
def set_search_path(dbapi_connection, connection_record):
    """Set the search_path to the specified schema after connecting."""
    schema = settings.POSTGRES_SCHEMA
    cursor = dbapi_connection.cursor()
    cursor.execute(f"SET search_path TO {schema}, public")
    cursor.close()
    logger.debug(f"Set search_path to {schema}, public")

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a base class for declarative models
Base = declarative_base()

# Dependency to get a database session
def get_db():
    """
    Get a database session.
    
    Returns:
        Session: Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
