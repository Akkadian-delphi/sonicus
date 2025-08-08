import uvicorn
import os
# from app.routers import admin_databases  # TODO: Re-enable after auth migration
# from app.routers import super_admin  # TODO: Replace with Authentik auth
from app.routers import business_admin  # Re-enabled: using JWT auth from get_current_user
from app.routers import authentik_auth as authentik_router  # New Authentik OIDC authentication
from app.routers import user  # UNIFIED: Single comprehensive user management system
from app.routers import dashboard_metrics  # Re-enabled: now using Authentik compatible auth
from app.routers import dashboard_websocket  # Re-enabled: now using Authentik compatible auth
from app.routers import dashboard_management  # Re-enabled: now using Authentik compatible auth
# from app.routers import business_admin_employees  # TODO: Fix import errors
from app.routers import business_admin_customers
from app.routers import business_admin_packages
from app.routers import organization_crud  # Organization CRUD operations with Authentik auth
from app.routers import business_admin_communications
from app.routers import business_admin_organization  # New organization-specific endpoints
from app.routers import wellness_impact_tracking
from app.routers import webhook_management  # Webhook management and testing
from app.routers import public  # Public endpoints for platform detection
from app.routers import customers  # Customer management and B2C registration
import logging
from fastapi import FastAPI, Request, Response, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.api_docs import custom_openapi
import time
import httpx

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import essential routers
from app.routers import sounds_simple, sales_simple
from app.routers import organization_metrics
from app.routers import health
# from app.routers import user_b2c_simple  # TODO: Fix import errors

# Database specific imports
from app.db.session import engine # Synchronous engine for initial setup
from app.db.base import Base  # Assuming your SQLAlchemy models' Base is here
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy.exc import OperationalError

# Set up logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("Starting up Sonicus application")
    
    # Initialize database and tables
    try:
        db_url = str(engine.url)
        # Mask password in URL for logging
        safe_url = db_url
        if '@' in safe_url:
            parts = safe_url.split('@')
            connection_prefix = parts[0]
            if ':' in connection_prefix:
                user_pass = connection_prefix.split(':')
                if len(user_pass) >= 3:  # protocol://user:pass
                    safe_url = f"{user_pass[0]}:{user_pass[1]}:***@{parts[1]}"
        
        logger.info(f"Checking database connection to {safe_url}")
        
        # Test database connection first
        try:
            from sqlalchemy import text
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                logger.info("Database connection test successful")
        except OperationalError as e:
            logger.error(f"Database connection failed: {e}")
            if "password authentication failed" in str(e):
                logger.error("TROUBLESHOOTING TIPS:")
                logger.error("1. Check that PostgreSQL is running: 'brew services start postgresql' (macOS) or 'sudo systemctl start postgresql' (Linux)")
                logger.error("2. Verify database credentials in .env file")
                logger.error("3. Try connecting manually: psql -h localhost -U postgres -d postgres")
                logger.error("4. Reset postgres password if needed: 'ALTER USER postgres PASSWORD 'your_password';'")
            elif "connection refused" in str(e):
                logger.error("PostgreSQL server is not running or not accepting connections")
                logger.error("Start PostgreSQL service and try again")
            # Don't proceed if we can't connect
            logger.warning("Skipping database setup due to connection issues. Application will start but database features may not work.")
            yield
            return
        except Exception as e:
            logger.error(f"Unexpected database connection error: {e}")
            logger.warning("Skipping database setup due to connection issues. Application will start but database features may not work.")
            yield
            return
        
        # Check if database exists using a more robust method for Docker setups
        try:
            # Try to connect to the target database directly instead of using database_exists()
            with engine.connect() as conn:
                result = conn.execute(text("SELECT current_database()"))
                current_db = result.scalar()
                logger.info(f"Successfully connected to database: {current_db}")
        except OperationalError as e:
            if "does not exist" in str(e):
                logger.info("Database does not exist. Attempting to create database.")
                try:
                    # Create database by connecting to postgres default db first
                    from sqlalchemy import create_engine
                    from urllib.parse import urlparse, urlunparse
                    
                    # Parse the database URL and change database name to 'postgres'
                    parsed = urlparse(db_url)
                    postgres_db_url = urlunparse(parsed._replace(path='/postgres'))
                    
                    temp_engine = create_engine(postgres_db_url)
                    with temp_engine.connect() as conn:
                        conn.execute(text("COMMIT"))  # End any existing transaction
                        conn.execute(text(f"CREATE DATABASE {parsed.path[1:]}"))  # Remove leading slash
                    temp_engine.dispose()
                    logger.info("Database created successfully.")
                except Exception as create_error:
                    logger.error(f"Could not create database: {create_error}")
                    logger.error("Please create the database manually or check permissions.")
            else:
                logger.error(f"Database connection error: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during database check: {e}")

        # Ensure schema exists (from config)
        from sqlalchemy import text
        schema_name = getattr(settings, "POSTGRES_SCHEMA", "sonicus")
        try:
            with engine.connect() as conn:
                conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
                conn.commit()
                logger.info(f"Ensured '{schema_name}' schema exists.")
        except Exception as e:
            logger.error(f"Could not create schema '{schema_name}': {e}")

        # Check if tables exist in the configured schema, and create them if not
        try:
            from sqlalchemy import inspect
            inspector = inspect(engine)
            tables = inspector.get_table_names(schema=schema_name)
            if not tables:
                logger.info(f"No tables found in the '{schema_name}' schema. Creating all tables in this schema.")
                try:
                    for table in Base.metadata.tables.values():
                        if not table.schema:
                            table.schema = schema_name
                    Base.metadata.create_all(bind=engine)
                    logger.info(f"Tables created successfully in '{schema_name}' schema.")
                except OperationalError as e:
                    logger.error(f"Could not create tables: {e}. Please ensure the database is running and accessible.")
                except Exception as e:
                    logger.error(f"An unexpected error occurred during table creation: {e}")
            else:
                logger.info(f"Existing tables found in '{schema_name}' schema: {tables}")
        except Exception as e:
            logger.error(f"Could not inspect database schema: {e}")

    except Exception as e:
        logger.error(f"Error during application startup: {e}")
        logger.warning("Application will start but database features may not work correctly.")
    
    yield
    
    # Shutdown logic
    logger.info("Shutting down Sonicus application")
    # Close any connections or resources here

# Authentik OIDC token validation dependency
async def authentik_auth(request: Request):
    """
    TODO: Replace with Authentik OIDC authentication
    Current implementation is placeholder for Scaleway IAM
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )
    token = auth_header.split(" ", 1)[1]
    
    # TODO: Replace with Authentik token validation
    # from app.core.authentik_auth import authentik
    # payload = await authentik.verify_token(token)
    # return payload
    
    # Temporary mock validation - REMOVE AFTER AUTHENTIK INTEGRATION
    async with httpx.AsyncClient() as client:
        # This endpoint should be replaced with actual Authentik token introspection
        resp = await client.get(
            "https://iam.api.scaleway.com/validate",  # Placeholder endpoint
            headers={"Authorization": f"Bearer {token}"}
        )
        if resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token - please integrate Authentik",
            )

def create_application() -> FastAPI:
    """Create and configure the FastAPI application"""

    # Process API_V1_STR to ensure it's a valid path prefix
    effective_api_prefix = settings.API_V1_STR
    if effective_api_prefix and not effective_api_prefix.startswith("/"):
        effective_api_prefix = "/" + effective_api_prefix
    # If settings.API_V1_STR was empty, effective_api_prefix remains empty.
    # If settings.API_V1_STR was "/path", effective_api_prefix remains "/path".

    # Construct openapi_url carefully
    # If effective_api_prefix is empty, openapi_url should be "/openapi.json"
    # Otherwise, it should be f"{effective_api_prefix}/openapi.json"
    final_openapi_url = f"{effective_api_prefix}/openapi.json" if effective_api_prefix else "/openapi.json"

    application = FastAPI(
        title=settings.PROJECT_NAME,
        description="API for accessing therapeutic sound content",
        version="0.1.0",
        openapi_url=final_openapi_url,  # Use the processed URL
        lifespan=lifespan,
        debug=settings.DEBUG,
        # Make Swagger UI available at BOTH /docs and /api/v1/docs
        docs_url="/docs",  # Root path for convenience
        redoc_url="/redoc",  # Root path for convenience
    )
    
    # Set up CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add request logging middleware
    @application.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log request details
        logger.info(
            f"{request.method} {request.url.path} "
            f"[{response.status_code}] "
            f"({process_time:.4f}s)"
        )
        
        # Add X-Process-Time header
        response.headers["X-Process-Time"] = str(process_time)
        return response
    
    # Include routers with working endpoints
    # Health check endpoint (no authentication required)
    application.include_router(
        health.router,
        tags=["health"]
    )
    
    # Public endpoints for platform detection (no authentication required)
    application.include_router(
        public.router,
        prefix="/public",
        tags=["public"]
    )
    
    # Customer registration and management for B2C mode
    application.include_router(
        customers.router,
        prefix=f"{effective_api_prefix}/customers",
        tags=["customers"]
    )
    
    application.include_router(
        sounds_simple.router,
        prefix=effective_api_prefix,
        tags=["sounds"]
    )
    application.include_router(
        sales_simple.router,
        prefix=effective_api_prefix,
        tags=["sales"]
    )
    
    # B2C User Management - Subscription, content access, and analytics - COMMENTED OUT due to import issues
    # application.include_router(
    #     user_b2c_simple.router,
    #     tags=["user-b2c"]
    # )
    
    # application.include_router(
    #     admin_databases.router,
    #     prefix=effective_api_prefix,
    #     tags=["admin-databases"],
    #     dependencies=[Depends(scaleway_iam_auth)]
    # )
    # application.include_router(
    #     super_admin.router,
    #     prefix=f"{effective_api_prefix}/super-admin",
    #     tags=["super-admin"],
    #     dependencies=[Depends(scaleway_iam_auth)]
    # )
    
    # Main business admin router - Re-enabled: uses JWT auth from get_current_user
    application.include_router(
        business_admin.router,
        tags=["business-admin"]
    )
    
    # Authentik OIDC authentication router
    application.include_router(
        authentik_router.router,
        prefix=f"{effective_api_prefix}/auth",
        tags=["auth"]
    )
    
    # User management routers - UNIFIED SYSTEM ONLY
    # The unified user system consolidates all user operations
    application.include_router(
        user.router,
        prefix=effective_api_prefix,  # Mount at /api/v1 for legacy compatibility
        tags=["users"]
    )
    
    # Dashboard metrics router for Super Admin - Re-enabled with Authentik auth
    application.include_router(
        dashboard_metrics.router,
        prefix=effective_api_prefix,  # Already includes /super-admin/dashboard
        tags=["dashboard-metrics"]
    )
    
    # Dashboard WebSocket router for real-time updates - Re-enabled with Authentik auth
    application.include_router(
        dashboard_websocket.router,
        prefix="",  # WebSocket routes start with /ws
        tags=["dashboard-websocket"]
    )
    
    # Dashboard management router for cache and system operations - Re-enabled with Authentik auth
    application.include_router(
        dashboard_management.router,
        prefix=effective_api_prefix,  # Already includes management prefix
        tags=["dashboard-management"]
    )
    
    # Business admin employee management router (legacy - employees) - COMMENTED OUT due to import issues
    # application.include_router(
    #     business_admin_employees.router,
    #     prefix=f"{effective_api_prefix}/business-admin",
    #     tags=["business-admin-employees"]
    # )
    
    # Business admin customer management router (new - customers)
    application.include_router(
        business_admin_customers.router,
        prefix=f"{effective_api_prefix}/business-admin",
        tags=["business-admin-customers"]
    )
    
    # Business admin sound package management router
    application.include_router(
        business_admin_packages.router,
        prefix=f"{effective_api_prefix}/business-admin",
        tags=["business-admin-packages"]
    )
    
    # Organization CRUD operations with comprehensive audit logging
    application.include_router(
        organization_crud.router,
        prefix=f"{effective_api_prefix}/business-admin",
        tags=["organization-crud"]
    )
    
    # Organization-specific wellness metrics and analytics router
    application.include_router(
        organization_metrics.router,
        prefix=f"{effective_api_prefix}/organization",
        tags=["organization-metrics"]
    )
    
    # Business admin communications and employee engagement router
    application.include_router(
        business_admin_communications.router,
        prefix=f"{effective_api_prefix}/business-admin",
        tags=["business-admin-communications"]
    )
    
    # Business admin organization-specific endpoints router
    application.include_router(
        business_admin_organization.router,
        prefix=f"{effective_api_prefix}/business-admin",
        tags=["business-admin-organization"]
    )
    
    # Real wellness impact tracking with interactive dashboards router
    application.include_router(
        wellness_impact_tracking.router,
        prefix=f"{effective_api_prefix}/wellness",
        tags=["wellness-impact-tracking"]
    )
    
    # Webhook management and testing router
    application.include_router(
        webhook_management.router,
        tags=["webhook-management"]
    )
    
    # Set up custom OpenAPI documentation
    application.openapi = lambda: custom_openapi(application)
    
    # Add health check endpoint
    @application.get("/health", tags=["health"])
    async def health_check():
        return {"status": "ok", "version": "0.1.0"}

    # Add root redirect to docs for convenience
    @application.get("/", include_in_schema=False)
    async def redirect_to_docs():
        return {"message": "Welcome to Sonicus API", "docs": "/docs", "health": "/health"}
    
    return application

app = create_application()

if __name__ == "__main__":
    # Determine the host and port for the server
    host = "0.0.0.0"  # Bind to all interfaces for Docker
    port = int(os.getenv("PORT", 18100))  # Use PORT env var or default to 8100
    
    # In Docker, we want to bind to all interfaces
    # In development, we might want to bind to localhost only
    if os.getenv("DOCKER_ENV"):
        host = "0.0.0.0"
    elif settings.DEBUG:
        host = "127.0.0.1"  # Development mode
    
    logger.info(f"Starting Sonicus server on {host}:{port}")
    logger.info(f"Environment: {'Production' if not settings.DEBUG else 'Development'}")
    logger.info(f"Docker mode: {'Yes' if os.getenv('DOCKER_ENV') else 'No'}")
    
    uvicorn.run(
        "run:app",
        host=host,
        port=port,
        reload=settings.DEBUG and not os.getenv("DOCKER_ENV"),  # No reload in Docker
        log_level="info" if settings.DEBUG else "warning",
        access_log=settings.DEBUG
    )