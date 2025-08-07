import os
import json
from typing import List, Any, Optional
from pydantic import EmailStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import logging

# Set up logger
logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    # Environment setting
    ENV: str = os.getenv("ENV", "development")# Path: /Users/luis/Projects/Elefefe/Sonicus/app/core/settings.py

    # Application settings
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Sonicus Therapy Sound API"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Docker Compose related settings
    # This is used by the Docker stack in elefefe.yml
    STACK_ELEFEFE: str = os.getenv("STACK_ELEFEFE", "praetoria")
    
    # Database
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "sonicus")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_SCHEMA: str = os.getenv("POSTGRES_SCHEMA", "sonicus")
    POSTGRES_URL: Optional[str] = os.getenv("POSTGRES_URL", None)
    DATABASE_URL: Optional[str] = None # Keep for potential direct use or fallback
    
    # SQL Echo mode - set to True to log all SQL queries (development only)
    SQL_ECHO: bool = os.getenv("SQL_ECHO", "False").lower() == "true"
    
    # Redis settings
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    REDIS_URL: str = os.getenv(
        "REDIS_URL", 
        f"redis://{':' + REDIS_PASSWORD + '@' if REDIS_PASSWORD else ''}{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    )
    
    # Cache settings
    CACHE_EXPIRATION_SECONDS: int = int(os.getenv("CACHE_EXPIRATION_SECONDS", "300"))  # 5 minutes default
    
    # Email settings
    MAIL_USERNAME: str = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD: str = os.getenv("MAIL_PASSWORD", "")
    MAIL_FROM: EmailStr = os.getenv("MAIL_FROM", "noreply@sonicus.com")
    MAIL_SERVER: str = os.getenv("MAIL_SERVER", "")
    MAIL_PORT: int = int(os.getenv("MAIL_PORT", "587"))
    MAIL_TLS: bool = os.getenv("MAIL_TLS", "True").lower() == "true"
    MAIL_SSL: bool = os.getenv("MAIL_SSL", "False").lower() == "true"
    
    # Storage
    DEFAULT_SOUND_PATH: str = os.getenv("DEFAULT_SOUND_PATH", "/secure/storage/path/to/sounds/")
    
    # CORS - Use a default empty list
    CORS_ORIGINS: List[str] = []
    
    # Performance settings
    CONNECTION_POOL_SIZE: int = int(os.getenv("CONNECTION_POOL_SIZE", "10"))
    MAX_OVERFLOW: int = int(os.getenv("MAX_OVERFLOW", "20"))
    
    # Database pool settings for optimization
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "20"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "30"))
    DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    DB_POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", "3600"))
    
    # Development mode
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Firebase IAM settings
    FIREBASE_PROJECT_ID: str = os.getenv("FIREBASE_PROJECT_ID", "")
    FIREBASE_SERVICE_ACCOUNT_KEY: str = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY", "")
    FIREBASE_WEB_API_KEY: str = os.getenv("FIREBASE_WEB_API_KEY", "")
    FIREBASE_AUTH_DOMAIN: str = os.getenv("FIREBASE_AUTH_DOMAIN", "")
    FIREBASE_DATABASE_URL: str = os.getenv("FIREBASE_DATABASE_URL", "")
    FIREBASE_STORAGE_BUCKET: str = os.getenv("FIREBASE_STORAGE_BUCKET", "")

    @field_validator("FIREBASE_PROJECT_ID", mode="after")
    def validate_firebase_project_id(cls, v: str, info) -> str:
        """Validate that Firebase Project ID is provided in production."""
        if not v and info.data.get("ENV") == "production":
            logger.warning("Firebase Project ID not configured in production!")
        return v

    @field_validator("DATABASE_URL", mode="before") # mode='before' to handle v if DATABASE_URL env var is set
    def validate_database_url(cls, v: Optional[str], info) -> Optional[str]:
        """Validate or construct the database URL."""
        if v: # If DATABASE_URL is explicitly set, validate it
            if not v.startswith(("postgresql://", "postgresql+psycopg2://", "postgresql+asyncpg://")):
                logger.warning("DATABASE_URL doesn't use the postgresql:// scheme")
            return str(v)

        # If DATABASE_URL is not set, try POSTGRES_URL
        postgres_url = os.getenv("POSTGRES_URL", None)
        if postgres_url:
            return postgres_url

        # If neither is set, construct from individual environment variables
        user = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD", "postgres")
        server = os.getenv("POSTGRES_SERVER", "localhost")
        port = int(os.getenv("POSTGRES_PORT", "5432"))
        db = os.getenv("POSTGRES_DB", "sonicus")
        schema = os.getenv("POSTGRES_SCHEMA", "sonicus")
        url = f"postgresql+asyncpg://{user}:{password}@{server}:{port}/{db}?options=-csearch_path%3D{schema}"
        return url
    
    @field_validator("SECRET_KEY", mode="after") # mode='after' to access info.data.ENV
    def validate_secret_key(cls, v: str, info) -> str:
        """Validate that SECRET_KEY is not using the default development value in production."""
        # Access ENV from info.data, as ENV field is defined earlier
        if v == "dev-secret-key-change-in-production" and info.data.get("ENV") == "production":
            logger.critical("Using default SECRET_KEY in production. This is a security risk!")
        return v
    
    @field_validator("CORS_ORIGINS", mode="before")
    def parse_cors_origins(cls, v: Any) -> List[str]:
        """Parse CORS_ORIGINS from different input formats."""
        # Handle the case where v is already a list
        if isinstance(v, list):
            return v
        
        # Handle empty string case
        if not v:
            return []
            
        # Handle string case (from environment variable)
        if isinstance(v, str):
            # If it looks like a JSON list
            if (v.startswith("[") and v.endswith("]")):
                try:
                    # Try standard JSON parsing first
                    return json.loads(v)
                except json.JSONDecodeError:
                    # Handle case with single quotes instead of double quotes
                    try:
                        corrected_v = v.replace("'", '"')
                        return json.loads(corrected_v)
                    except json.JSONDecodeError:
                        # Fallback to comma-separated parsing
                        return [origin.strip() for origin in v.strip('[]').split(",") if origin.strip()]
            
            # Otherwise, split by comma
            return [origin.strip() for origin in v.split(",") if origin.strip()]
            
        # Default case - return as is
        return v
    
    # model_config correctly defines settings behavior
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', extra='ignore')

# Initialize settings
try:
    settings = Settings()
    
    # Warn about development settings in production
    if settings.ENV == "production":
        if settings.DEBUG:
            logger.warning("DEBUG mode is enabled in production environment!")
        
        if settings.SQL_ECHO:
            logger.warning("SQL_ECHO is enabled in production environment!")
            
except Exception as e:
    logger.critical(f"Failed to load settings: {str(e)}")
    raise
