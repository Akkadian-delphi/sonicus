"""
This module customizes OpenAPI documentation for the Sonicus Therapy Sound API.
"""
from fastapi.openapi.utils import get_openapi

def custom_openapi(app):
    """
    Customize OpenAPI documentation with enhanced details about the Sonicus API,
    including detailed endpoint documentation and examples.
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Sonicus B2B2C Therapeutic Sound Platform API",
        version="0.2.0",
        description="""
        # Sonicus B2B2C Therapeutic Sound Platform API
        
        This API provides comprehensive B2B2C platform services for therapeutic sound content delivery,
        organization management, and employee wellness tracking.
        
        ## Platform Architecture
        
        * **Multi-tenant B2B2C platform** with organization isolation
        * **Authentik OIDC authentication** for secure, centralized access
        * **Role-based access control** (Super Admin, Business Admin, User)
        * **Real-time analytics** and wellness impact tracking
        * **WebSocket support** for live dashboard updates
        * **Comprehensive audit logging** for all administrative actions
        
        ## Key Features
        
        * **Organization Management**: Complete CRUD operations with onboarding workflows
        * **Employee Lifecycle Management**: User invitations, role assignments, analytics
        * **Sound Package Management**: Custom therapeutic content curation
        * **Wellness Impact Tracking**: Real-time progress bars, engagement analytics
        * **Business Communications**: Team announcements, surveys, feedback systems
        * **Dashboard Analytics**: Platform metrics, revenue analytics, system health
        * **WebSocket Services**: Real-time updates for dashboards and notifications
        
        ## Authentication Flows
        
        ### Authentik OIDC Integration
        The platform uses **Authentik OIDC** (https://authentik.elefefe.eu) for secure, centralized authentication:
        
        1. **Initiate Login**: Use `/auth/login` to start the OIDC flow
        2. **Authorization**: User is redirected to Authentik for authentication
        3. **Callback Handling**: Authorization code is exchanged for tokens via `/auth/callback`
        4. **API Access**: Include JWT token in Authorization header for subsequent requests:
           `Authorization: Bearer <jwt_token>`
        
        ### Role-Based Access Control
        ```
        Super Admin (Platform Owner)
        ├── Full platform access
        ├── Organization management (/super-admin/*)
        ├── Dashboard metrics & analytics
        └── System administration
        
        Business Admin (Customer Organization)
        ├── Organization-specific access
        ├── Employee management (/business-admin/employees/*)
        ├── Package management (/business-admin/packages/*)
        ├── Communications (/business-admin/communications/*)
        └── Wellness tracking (/wellness/*)
        
        User (Employee within Organization)
        ├── Personal dashboard
        ├── Sound therapy access
        └── Progress tracking
        ```
        
        ## Endpoint Overview
        
        ### Authentication (Authentik OIDC)
        * `GET /auth/login` - Initiate OIDC login flow
        * `POST /auth/callback` - Handle OIDC callback with authorization code
        * `GET /auth/me` - Get current authenticated user info
        * `POST /auth/logout` - Logout user (client-side token cleanup)
        
        ### Super Admin Endpoints
        * `GET /super-admin/dashboard/stats` - Platform-wide statistics
        * `GET /super-admin/dashboard/revenue` - Revenue analytics
        * `GET /super-admin/dashboard/growth` - Growth trends
        * `GET /super-admin/dashboard/health` - System health monitoring
        * `POST /super-admin/dashboard/manage/refresh` - Refresh dashboard data
        * `GET /super-admin/dashboard/manage/cache/status` - Cache status
        * `POST /super-admin/dashboard/manage/cache/clear` - Clear cache
        
        ### Organization Management
        * `POST /organizations` - Create new organization
        * `GET /organizations` - List all organizations
        * `GET /organizations/{org_id}` - Get organization details
        * `PUT /organizations/{org_id}` - Update organization
        * `DELETE /organizations/{org_id}` - Archive/delete organization
        * `GET /organizations/{org_id}/onboarding` - Get onboarding status
        * `PUT /organizations/{org_id}/subscription` - Update subscription
        * `POST /organizations/{org_id}/suspend` - Suspend organization
        * `POST /organizations/{org_id}/reactivate` - Reactivate organization
        
        ### Business Admin - Employee Management
        * `GET /business-admin/employees` - List organization employees
        * `POST /business-admin/employees` - Create employee
        * `PUT /business-admin/employees/{employee_id}` - Update employee
        * `DELETE /business-admin/employees/{employee_id}` - Remove employee
        * `POST /business-admin/employees/invite` - Send employee invitation
        * `GET /business-admin/employees/{employee_id}/analytics` - Employee analytics
        
        ### Business Admin - Package Management
        * `GET /business-admin/packages` - List sound packages
        * `POST /business-admin/packages` - Create custom package
        * `PUT /business-admin/packages/{package_id}` - Update package
        * `DELETE /business-admin/packages/{package_id}` - Delete package
        * `POST /business-admin/packages/{package_id}/assign` - Assign to employees
        * `GET /business-admin/packages/{package_id}/analytics` - Package usage analytics
        
        ### Business Admin - Communications
        * `POST /business-admin/communications/announcements` - Create announcement
        * `GET /business-admin/communications/announcements` - List announcements
        * `POST /business-admin/communications/surveys` - Create survey
        * `GET /business-admin/communications/surveys/{survey_id}/results` - Survey results
        * `GET /business-admin/communications/feedback` - Feedback summary
        * `POST /business-admin/communications/reminders` - Set up reminders
        
        ### Wellness Impact Tracking
        * `GET /wellness/progress/{employee_id}` - Employee progress tracking
        * `GET /wellness/trends/{organization_id}` - Organization wellness trends
        * `GET /wellness/engagement/heatmap` - Employee engagement heatmap
        * `GET /wellness/roi/calculations` - ROI calculations
        * `POST /wellness/dashboard/widgets` - Configure dashboard widgets
        * `GET /wellness/metrics/realtime` - Real-time wellness metrics
        
        ### WebSocket Endpoints
        * `WS /ws/admin/dashboard` - Real-time dashboard updates for admins
        * `WS /ws/analytics/{organization_id}` - Organization-specific analytics stream
        * `WS /ws/system-analytics` - System-wide analytics stream
        
        ### Sound Content (Legacy - Being Updated)
        * `GET /sounds` - List available sounds (supports pagination and search)
        * `GET /sounds/categories` - List sound categories
        * `GET /sounds/{sound_id}` - Get sound details
        * `GET /sounds/stream/{sound_id}` - Stream sound audio
        
        ### User Management (Legacy - Being Updated)
        * `GET /users/profile` - Get user profile
        * `PUT /users/profile` - Update user profile
        
        ## WebSocket Integration
        
        The platform supports real-time updates via WebSocket connections:
        
        * **Dashboard Updates**: Live metrics for admin dashboards
        * **Analytics Streaming**: Real-time analytics data
        * **Notifications**: System alerts and user notifications
        * **Progress Updates**: Live wellness progress tracking
        
        ## Security Considerations
        
        All protected endpoints require a valid JWT token from Authentik OIDC:
        
        ```
        Authorization: Bearer <jwt_token>
        ```
        
        * **Stateless Authentication**: JWT tokens contain user and role information
        * **Role-based Access**: Endpoints automatically enforce role requirements
        * **Audit Logging**: All administrative actions are logged with user context
        * **Multi-tenant Isolation**: Organizations are strictly isolated
        * **Rate Limiting**: Authentication endpoints have rate limiting to prevent abuse
        """,
        routes=app.routes,
    )
    
    # Add security schemes for Swagger UI
    openapi_schema["components"] = openapi_schema.get("components", {})
    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2PasswordBearer": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": f"{app.root_path}/auth/login",
                    "scopes": {}
                }
            }
        }
    }
    
    # Apply security globally
    openapi_schema["security"] = [{"OAuth2PasswordBearer": []}]
    
    # Add tag descriptions for better organization
    openapi_schema["tags"] = [
        {
            "name": "users",
            "description": "User registration, authentication, and profile management"
        },
        {
            "name": "sounds",
            "description": "Browse and stream therapeutic sound content"
        },
        {
            "name": "sales",
            "description": "Subscription and invoice management for premium content"
        }
    ]
    
    # Add examples for request and response bodies
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
    
    if "examples" not in openapi_schema["components"]:
        openapi_schema["components"]["examples"] = {}
    
    # Add login example
    openapi_schema["components"]["examples"]["LoginExample"] = {
        "summary": "Login credentials",
        "value": {
            "username": "user@example.com",
            "password": "SecurePassword123!"
        }
    }
    
    # Add registration example
    openapi_schema["components"]["examples"]["RegisterExample"] = {
        "summary": "User registration data",
        "value": {
            "email": "newuser@example.com",
            "password": "SecurePassword123!"
        }
    }
    
    # Add subscription example
    openapi_schema["components"]["examples"]["SubscriptionExample"] = {
        "summary": "Create subscription",
        "value": {
            "sound_id": 1
        }
    }
    
    # Add sound search example
    openapi_schema["components"]["examples"]["SoundSearchExample"] = {
        "summary": "Search sounds",
        "value": {
            "q": "meditation",
            "category": "relaxation",
            "skip": 0,
            "limit": 20
        }
    }
    
    # Add common responses
    openapi_schema["components"]["responses"] = {
        "UnauthorizedError": {
            "description": "Authentication information is missing or invalid",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {
                                "type": "string",
                                "example": "Could not validate credentials"
                            }
                        }
                    }
                }
            }
        }
    }
    
    # Add rate limiting response
    openapi_schema["components"]["responses"]["RateLimitError"] = {
        "description": "Too many requests",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "detail": {
                            "type": "string",
                            "example": "Rate limit exceeded. Try again later."
                        }
                    }
                }
            }
        }
    }
    
    # Apply common response patterns to endpoints
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            # Skip if this is an open endpoint
            if "/auth/login" in path or (path.endswith("/users") and method == "post"):
                continue
                
            # Add common error responses
            if "responses" not in openapi_schema["paths"][path][method]:
                openapi_schema["paths"][path][method]["responses"] = {}
                
            # Add 401 response for protected endpoints
            if "401" not in openapi_schema["paths"][path][method]["responses"]:
                openapi_schema["paths"][path][method]["responses"]["401"] = {
                    "$ref": "#/components/responses/UnauthorizedError"
                }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema
