# Multi-Tenant Subdomain Architecture Implementation Plan

## Overview
Transform Sonicus into a multi-tenant SaaS platform where:
- **Main Domain (`sonicus.eu`)**: Business registration and landing page
- **Subdomains (`company.sonicus.eu`)**: Individual tenant applications for end-users

## 🏗️ Phase 1: Backend Infrastructure

### 1.1 Tenant Detection Middleware
**File**: `backend/app/core/tenant_middleware.py`
- Create middleware to extract subdomain from request headers
- Detect main domain vs subdomain requests
- Store tenant context in request state
- Handle invalid/non-existent subdomains

**Implementation**:
```python
class TenantDetectionMiddleware:
    def extract_tenant_from_host(self, host: str) -> TenantContext
    def validate_subdomain(self, subdomain: str) -> bool
    def get_organization_by_subdomain(self, subdomain: str) -> Organization
```

### 1.2 Tenant Context Management
**File**: `backend/app/core/tenant_context.py`
- Create `TenantContext` dataclass
- Store organization info, subdomain, domain type
- Integrate with existing `B2B2CSessionManager`

### 1.3 Database Schema Updates
**Migration**: Add subdomain fields to organizations
```sql
ALTER TABLE organizations ADD COLUMN subdomain VARCHAR(100) UNIQUE;
ALTER TABLE organizations ADD COLUMN domain_verified BOOLEAN DEFAULT false;
ALTER TABLE organizations ADD COLUMN domain_settings JSONB;
CREATE INDEX idx_organizations_subdomain ON organizations(subdomain);
```

### 1.4 Organization Registration System
**File**: `backend/app/routers/organization_registration.py`
- Business registration endpoint
- Subdomain generation and validation
- Organization database creation
- Admin user provisioning
- Revolut payment integration and billing setup
- Odoo Lead integration
- Container deployment webhook triggers

**Endpoints**:
```
POST /api/v1/organizations/register
POST /api/v1/organizations/check-subdomain
GET  /api/v1/organizations/subdomain-suggestions
```

### 1.5 Enhanced Session Management
**File**: Update `backend/app/db/b2b2c_session.py`
- Integrate subdomain-based organization resolution
- Automatic tenant context from middleware
- Update existing methods to handle subdomain routing

## 🎨 Phase 2: Frontend Architecture

### 2.1 Domain Detection Utilities
**File**: `frontend/src/utils/domainDetection.js`
- Extract subdomain from window.location
- Determine if main domain or tenant subdomain
- Return domain context object

### 2.2 Conditional App Rendering
**File**: `frontend/src/App.js`
- Render different components based on domain type
- Main domain: Landing page with business registration
- Subdomain: Tenant-specific application

### 2.3 Business Registration Flow
**Files**: 
- `frontend/src/pages/BusinessRegistration.js`
- `frontend/src/components/SubdomainGenerator.js`
- `frontend/src/components/CompanyDetailsForm.js`

**Features**:
- Company information form (name, tax ID, billing address)
- Subdomain generation from company name
- Subdomain availability check
- Customizable subdomain input
- Revolut payment setup and subscription management
- Terms acceptance and plan selection

### **2.3 Business Registration Form UX**
**Frontend Message**: After successful registration submission:

```javascript
// Registration success response handling
{
  "message": "Organization registration successful! You will receive an email confirmation in a few minutes when your Sonicus instance is fully deployed and ready to use.",
  "subdomain": "company.sonicus.eu",
  "status": "deployment_pending",
  "estimated_deployment_time": "5-10 minutes"
}

// Display to user:
"✅ Registration Successful!

Your Sonicus instance is being prepared...

🚀 We're currently:
• Setting up your dedicated container
• Configuring your database  
• Preparing your sound library
• Setting up your admin dashboard

📧 You'll receive an email at admin@company.com in approximately 5-10 minutes with:
• Your login credentials
• Direct access to company.sonicus.eu  
• Getting started guide

Thank you for choosing Sonicus!"
```

### **2.4 Tenant-Specific Theming**"
```
**File**: `frontend/src/context/TenantContext.js`
- Dynamic branding based on organization
- Custom colors, logos, company name
- Tenant-specific navigation

### 2.5 Updated Authentication Flow
**File**: `frontend/src/context/useAuth.js`
- Handle tenant-specific authentication
- Organization context in auth state
- Different user flows for main vs subdomain

## 🔧 Phase 3: API Enhancements

### 3.1 Tenant-Aware Endpoints
**Update existing routers**:
- Modify all routers to handle tenant context
- Add organization filtering to queries
- Update response schemas to include tenant info

### 3.2 Cross-Tenant Security
**File**: `backend/app/core/tenant_security.py`
- Prevent cross-tenant data access
- Validate organization membership
- Audit trail for tenant operations

### 3.3 Admin Panel Updates
**Files**: Update admin routers
- Super admin: Cross-tenant management
- Business admin: Tenant-specific management
- Add subdomain management features

## 🗄️ Phase 4: Database & Models

### 4.1 Enhanced Organization Model
**File**: `backend/app/models/organization.py`
- Add subdomain field
- Domain verification status
- Custom domain settings (future)
- Tenant-specific configuration

### 4.2 User Model Updates
**File**: `backend/app/models/user.py`  
- Ensure proper organization relationships
- Tenant-specific user roles
- Cross-tenant user prevention

### 4.3 Migration Scripts
**File**: `backend/scripts/migrate_to_subdomain_architecture.py`
- Migrate existing organizations
- Generate subdomains for existing data
- Verify data integrity

## 🚀 Phase 5: Infrastructure & Deployment

### 5.1 DNS Configuration
- Setup wildcard DNS: `*.sonicus.eu`
- Configure load balancer for subdomain routing
- SSL certificate management (wildcard cert)

### 5.2 Environment Configuration
**File**: `backend/app/core/config.py`
- Add tenant-related settings
- Main domain configuration
- Subdomain validation rules

### 5.3 Docker & Deployment Updates
**Files**: 
- `docker-compose.yml`: Environment variables for multi-tenant
- `Dockerfile`: No changes needed
- Deployment scripts: Handle subdomain routing

## 📝 Phase 6: Testing & Validation

### 6.1 Unit Tests
**Files**:
- `backend/tests/test_tenant_middleware.py`
- `backend/tests/test_organization_registration.py`
- `backend/tests/test_subdomain_routing.py`

### 6.2 Integration Tests
**File**: `backend/tests/test_multi_tenant_flow.py`
- End-to-end business registration
- Subdomain creation and access
- Cross-tenant isolation validation

### 6.3 Frontend Tests
**Files**:
- `frontend/src/tests/domainDetection.test.js`
- `frontend/src/tests/BusinessRegistration.test.js`

## 🎯 Implementation Priority Order

### Sprint 1 (Backend Foundation)
1. ✅ Database schema updates and migration
2. ✅ Tenant detection middleware
3. ✅ Enhanced B2B2C session management
4. ✅ Organization registration API

### Sprint 2 (Frontend Core)
1. ✅ Domain detection utilities
2. ✅ Conditional app rendering
3. ✅ Business registration form
4. ✅ Subdomain generator component

### Sprint 3 (Integration)
1. ✅ API integration for registration flow
2. ✅ Tenant-specific authentication
3. ✅ Cross-tenant security implementation
4. ✅ Admin panel updates

### Sprint 4 (Polish & Deploy)
1. ✅ Testing and validation
2. ✅ Infrastructure setup
3. ✅ DNS and SSL configuration
4. ✅ Production deployment

## 🔐 Security Considerations

### Subdomain Security
- Validate subdomain format (alphanumeric, hyphens)
- Prevent subdomain takeover attacks
- Blacklist reserved subdomains (admin, api, www, etc.)

### Data Isolation
- Ensure complete database isolation between tenants
- Validate organization membership on all operations
- Audit trail for cross-tenant access attempts

### Authentication
- Tenant-specific JWT tokens
- Session isolation between subdomains
- Prevent session sharing across tenants

## 📊 Database Schema Changes

```sql
-- Organizations table updates
ALTER TABLE organizations ADD COLUMN subdomain VARCHAR(100) UNIQUE;
ALTER TABLE organizations ADD COLUMN domain_verified BOOLEAN DEFAULT false;
ALTER TABLE organizations ADD COLUMN custom_domain VARCHAR(255);
ALTER TABLE organizations ADD COLUMN tenant_settings JSONB DEFAULT '{}';

-- Indexes for performance
CREATE INDEX idx_organizations_subdomain ON organizations(subdomain);
CREATE INDEX idx_organizations_domain_verified ON organizations(domain_verified);

-- Reserved subdomains table
CREATE TABLE reserved_subdomains (
    subdomain VARCHAR(100) PRIMARY KEY,
    reason VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert reserved subdomains
INSERT INTO reserved_subdomains (subdomain, reason) VALUES 
('www', 'Web standard'),
('api', 'API endpoints'),
('admin', 'Administration'),
('app', 'Application'),
('mail', 'Email services'),
('ftp', 'File transfer'),
('blog', 'Blog subdomain'),
('shop', 'E-commerce'),
('support', 'Customer support'),
('docs', 'Documentation');
```

## 🔄 API Endpoint Changes

### New Endpoints
```
# Organization Registration
POST /api/v1/organizations/register
POST /api/v1/organizations/check-subdomain  
GET  /api/v1/organizations/subdomain-suggestions

# Tenant Management
GET  /api/v1/tenant/info
PUT  /api/v1/tenant/settings
POST /api/v1/tenant/verify-domain

# Admin - Tenant Management  
GET  /api/v1/super-admin/tenants
PUT  /api/v1/super-admin/tenants/{id}/subdomain
POST /api/v1/super-admin/tenants/{id}/suspend
```

### Modified Endpoints
All existing endpoints will include tenant context:
- User management: Tenant-scoped users
- Content: Organization-specific content
- Analytics: Tenant-specific metrics
- Billing: Revolut-based subscription management

## 🎨 Frontend Component Structure

```
src/
├── components/
│   ├── business/
│   │   ├── BusinessRegistration.js
│   │   ├── SubdomainGenerator.js
│   │   ├── CompanyDetailsForm.js
│   │   ├── RevolutPaymentForm.js
│   │   └── PlanSelection.js
│   ├── tenant/
│   │   ├── TenantApp.js
│   │   ├── TenantNavigation.js
│   │   └── TenantTheme.js
│   └── shared/
│       └── ConditionalRenderer.js
├── context/
│   ├── TenantContext.js
│   └── DomainContext.js
├── pages/
│   ├── LandingPage.js (main domain)
│   ├── TenantDashboard.js (subdomain)
│   └── BusinessOnboarding.js
├── utils/
│   ├── domainDetection.js
│   ├── subdomainValidation.js
│   ├── revolutPayment.js
│   └── tenantApi.js
└── hooks/
    ├── useTenant.js
    └── useDomain.js
```

## 🚦 Success Metrics

### Technical Metrics
- [ ] 100% tenant data isolation
- [ ] <200ms subdomain resolution time  
- [ ] Zero cross-tenant data leaks
- [ ] 99.9% uptime for all subdomains

### Business Metrics
- [ ] Business registration conversion rate
- [ ] Average time to first tenant user
- [ ] Subdomain activation rate
- [ ] Customer onboarding completion

## 🎯 Next Steps

1. **Start with Phase 1**: Backend infrastructure and tenant detection
2. **Create migration script**: For existing organizations to have subdomains
3. **Set up development environment**: With local subdomain testing
4. **Implement security first**: Cross-tenant isolation before features
5. **Test thoroughly**: Each phase before moving to the next

## 📋 Definition of Done

Each phase is complete when:
- [ ] Code implemented and reviewed
- [ ] Unit tests written and passing
- [ ] Integration tests passing
- [ ] Security validation complete
- [ ] Documentation updated
- [ ] Deployed to staging environment
- [ ] User acceptance testing passed

## 🌐 DNS Configuration for Subdomains with IONOS

Based on the IONOS DNS API documentation, here's how to programmatically add subdomain DNS records:

### IONOS DNS API Integration

#### Authentication
All DNS API requests require the `X-API-Key` header. Obtain your API key from the [IONOS Developer Portal](https://developer.hosting.ionos.de/docs/getstarted).

#### API Endpoints for DNS Management
- **Zones Management**: `GET /v1/zones` - List all DNS zones
- **Records Management**: `POST /v1/zones/{zoneId}/records` - Create new DNS records
- **Record Updates**: `PUT /v1/zones/{zoneId}/records/{recordId}` - Update existing records

### Implementation Steps

#### 1. Automated Subdomain Creation
When a new organization registers, automatically create DNS records and CRM leads:

```python
# backend/app/services/dns_service.py
import requests
from app.core.config import settings

class IONOSDNSService:
    def __init__(self):
        self.api_key = settings.IONOS_API_KEY
        self.base_url = "https://api.hosting.ionos.com/dns/v1"
        self.headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
    
    async def create_subdomain_record(self, subdomain: str, target_ip: str) -> bool:
        """Create A record for subdomain pointing to server IP"""
        try:
            # 1. Get zone ID for sonicus.eu domain
            zone_id = await self.get_zone_id("sonicus.eu")
            
            # 2. Create A record for subdomain
            record_data = {
                "name": subdomain,
                "type": "A",
                "content": target_ip,
                "ttl": 3600,
                "prio": 0,
                "disabled": False
            }
            
            response = requests.post(
                f"{self.base_url}/zones/{zone_id}/records",
                headers=self.headers,
                json=record_data
            )
            
            return response.status_code == 201
            
        except Exception as e:
            logger.error(f"Failed to create DNS record for {subdomain}: {e}")
            return False

# backend/app/services/deployment_service.py
import requests
import asyncio
from app.core.config import settings

class ContainerDeploymentService:
    def __init__(self):
        self.webhook_url = settings.DEPLOYMENT_WEBHOOK_URL
        self.webhook_secret = settings.DEPLOYMENT_WEBHOOK_SECRET
        self.enabled = settings.CONTAINER_DEPLOYMENT_ENABLED
    
    async def trigger_container_deployment(self, deployment_data: dict) -> bool:
        """Trigger webhook to deploy dedicated Sonicus container"""
        if not self.enabled:
            logger.info("Container deployment disabled in settings")
            return True
            
        try:
            # Prepare webhook payload
            webhook_payload = {
                "event": "organization.container.deploy",
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "organization_id": deployment_data["organization_id"],
                    "subdomain": deployment_data["subdomain"],
                    "admin_email": deployment_data["admin_email"],
                    "organization_name": deployment_data["organization_name"],
                    "container_config": {
                        "image": "sonicus:latest",
                        "subdomain": deployment_data["subdomain"],
                        "environment": {
                            "SUBDOMAIN": deployment_data["subdomain"],
                            "ORG_ID": deployment_data["organization_id"],
                            "ORG_NAME": deployment_data["organization_name"],
                            "ADMIN_EMAIL": deployment_data["admin_email"],
                            "DATABASE_NAME": deployment_data["database_config"]["name"],
                            "DATABASE_HOST": deployment_data["database_config"]["host"]
                        },
                        "resources": {
                            "cpu": "0.5",
                            "memory": "512Mi",
                            "storage": "1Gi"
                        }
                    }
                }
            }
            
            # Add webhook signature for security
            headers = {
                "Content-Type": "application/json",
                "X-Webhook-Secret": self.webhook_secret,
                "X-Event-Type": "organization.container.deploy"
            }
            
            # Send webhook
            response = requests.post(
                self.webhook_url,
                json=webhook_payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"Container deployment webhook triggered successfully for {deployment_data['subdomain']}")
                return True
            else:
                logger.error(f"Container deployment webhook failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to trigger container deployment webhook: {e}")
            return False
    
    async def check_deployment_status(self, organization_id: str) -> dict:
        """Check the status of container deployment"""
        try:
            status_url = f"{self.webhook_url}/status/{organization_id}"
            response = requests.get(status_url, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"status": "unknown", "message": "Unable to check deployment status"}
                
        except Exception as e:
            logger.error(f"Failed to check deployment status: {e}")
            return {"status": "error", "message": str(e)}

# Global instance
deployment_service = ContainerDeploymentService()
```

#### 2. DNS Record Types for Subdomains

**Option A: Individual A Records** (Recommended for production)
```json
{
  "name": "company1",
  "type": "A", 
  "content": "YOUR_SERVER_IP",
  "ttl": 3600
}
```

**Option B: Wildcard Record** (For development/testing)
```json
{
  "name": "*",
  "type": "A",
  "content": "YOUR_SERVER_IP", 
  "ttl": 3600
}
```

#### 3. Integration with Organization Registration

```python
# backend/app/routers/organization_registration.py
from app.services.dns_service import dns_service
from app.services.odoo_service import odoo_service
from app.services.deployment_service import deployment_service
from app.services.revolut_service import revolut_service

@router.post("/organizations/register")
async def register_organization(org_data: OrganizationRegistrationRequest):
    try:
        # 1. Create organization in database
        organization = await create_organization(org_data)
        
        # 2. Create Revolut customer and subscription
        revolut_customer = await revolut_service.create_customer({
            "name": organization.name,
            "email": organization.admin_email,
            "phone": organization.phone,
            "address": {
                "street_line_1": org_data.billing_address.street,
                "city": org_data.billing_address.city,
                "postcode": org_data.billing_address.postal_code,
                "country": org_data.billing_address.country
            }
        })
        
        if not revolut_customer:
            await rollback_organization_creation(organization.id)
            raise HTTPException(status_code=500, detail="Failed to create Revolut customer")
        
        # Store Revolut customer ID
        organization.revolut_customer_id = revolut_customer["id"]
        
        # Create subscription based on selected plan
        subscription = await revolut_service.create_subscription({
            "customer_id": revolut_customer["id"],
            "plan_id": org_data.subscription_plan_id,
            "payment_method": org_data.payment_method,
            "metadata": {
                "organization_id": str(organization.id),
                "subdomain": organization.subdomain
            }
        })
        
        if not subscription:
            await rollback_organization_creation(organization.id)
            raise HTTPException(status_code=500, detail="Failed to create Revolut subscription")
        
        organization.revolut_subscription_id = subscription["id"]
        
        # 3. Create DNS record for subdomain
        dns_success = await dns_service.create_subdomain_record(
            subdomain=organization.subdomain,
            target_ip=settings.SERVER_PUBLIC_IP
        )
        
        if not dns_success:
            # Rollback Revolut subscription and organization
            await revolut_service.cancel_subscription(subscription["id"])
            await rollback_organization_creation(organization.id)
            raise HTTPException(
                status_code=500,
                detail="Failed to create DNS record for subdomain"
            )
        
        # 4. Trigger container deployment webhook
        deployment_success = await deployment_service.trigger_container_deployment({
            "organization_id": str(organization.id),
            "subdomain": organization.subdomain,
            "admin_email": organization.admin_email,
            "organization_name": organization.name,
            "subscription_id": subscription["id"],
            "database_config": {
                "name": f"sonicus_{organization.subdomain}",
                "host": settings.DATABASE_HOST,
                "credentials": "auto_generated"
            }
        })
        
        if not deployment_success:
            logger.warning(f"Container deployment failed for organization {organization.id}")
            # Continue with registration - deployment can be retried
        
        # 5. Create Lead in Odoo CRM
        odoo_success = await odoo_service.create_lead({
            "name": organization.name,
            "email": organization.admin_email,
            "phone": organization.phone,
            "website": f"{organization.subdomain}.sonicus.eu",
            "company_name": organization.name,
            "source": "sonicus_registration",
            "subscription_plan": org_data.subscription_plan_id,
            "revolut_customer_id": revolut_customer["id"],
            "description": f"New business registration for {organization.name}"
        })
        
        if not odoo_success:
            # Log warning but don't fail registration
            logger.warning(f"Failed to create Odoo lead for organization {organization.id}")
        
        # 6. Mark domain as verified and send confirmation
        organization.domain_verified = True
        organization.subscription_status = "active"
        await db.commit()
        
        # 7. Send confirmation email with deployment status
        await send_registration_confirmation_email(
            organization.admin_email,
            organization.name,
            organization.subdomain,
            deployment_pending=True
        )
        
        return {
            "message": "Organization registration successful! You will receive an email confirmation in a few minutes when your Sonicus instance is fully deployed and ready to use.",
            "subdomain": f"{organization.subdomain}.sonicus.eu",
            "status": "deployment_pending",
            "subscription": {
                "id": subscription["id"],
                "status": "active",
                "plan": org_data.subscription_plan_id
            }
        }
        
    except Exception as e:
        logger.error(f"Organization registration failed: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")
```

#### 4. DNS Verification Process

```python
# backend/app/services/dns_verification.py
import dns.resolver
import asyncio

class DNSVerificationService:
    async def verify_subdomain_resolution(self, subdomain: str, expected_ip: str) -> bool:
        """Verify that subdomain resolves to expected IP"""
        try:
            domain = f"{subdomain}.sonicus.eu"
            result = dns.resolver.resolve(domain, 'A')
            
            for rdata in result:
                if str(rdata) == expected_ip:
                    return True
            return False
            
        except Exception as e:
            logger.error(f"DNS verification failed for {subdomain}: {e}")
            return False
    
    async def wait_for_dns_propagation(self, subdomain: str, max_attempts: int = 30):
        """Wait for DNS propagation with retry logic"""
        for attempt in range(max_attempts):
            if await self.verify_subdomain_resolution(subdomain, settings.SERVER_PUBLIC_IP):
                return True
            await asyncio.sleep(10)  # Wait 10 seconds between attempts
        return False
```

#### 5. Environment Configuration

```python
# backend/app/core/config.py
class Settings:
    # ... existing settings ...
    
    # IONOS DNS API Configuration
    IONOS_API_KEY: str = Field(..., env="IONOS_API_KEY")
    SERVER_PUBLIC_IP: str = Field(..., env="SERVER_PUBLIC_IP")
    
    # DNS Settings
    DNS_TTL: int = Field(default=3600, env="DNS_TTL")
    DNS_VERIFICATION_TIMEOUT: int = Field(default=300, env="DNS_VERIFICATION_TIMEOUT")
    
    # Odoo CRM Integration
    ODOO_URL: str = Field(..., env="ODOO_URL")
    ODOO_DATABASE: str = Field(..., env="ODOO_DATABASE")
    ODOO_USERNAME: str = Field(..., env="ODOO_USERNAME")
    ODOO_API_KEY: str = Field(..., env="ODOO_API_KEY")
    ODOO_LEAD_ENABLED: bool = Field(default=True, env="ODOO_LEAD_ENABLED")
    
    # Revolut Payment Integration
    REVOLUT_API_KEY: str = Field(..., env="REVOLUT_API_KEY")
    REVOLUT_API_URL: str = Field(default="https://business-api.revolut.com", env="REVOLUT_API_URL")
    REVOLUT_WEBHOOK_SECRET: str = Field(..., env="REVOLUT_WEBHOOK_SECRET")
    REVOLUT_ENABLED: bool = Field(default=True, env="REVOLUT_ENABLED")
    
    # Container Deployment
    DEPLOYMENT_WEBHOOK_URL: str = Field(..., env="DEPLOYMENT_WEBHOOK_URL")
    DEPLOYMENT_WEBHOOK_SECRET: str = Field(..., env="DEPLOYMENT_WEBHOOK_SECRET")
    CONTAINER_DEPLOYMENT_ENABLED: bool = Field(default=True, env="CONTAINER_DEPLOYMENT_ENABLED")
    
    # Email Configuration
    SMTP_HOST: str = Field(..., env="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USERNAME: str = Field(..., env="SMTP_USERNAME")
    SMTP_PASSWORD: str = Field(..., env="SMTP_PASSWORD")
    FROM_EMAIL: str = Field(..., env="FROM_EMAIL")
```

#### 6. Error Handling & Rollback

```python
# backend/app/services/organization_service.py
async def create_organization_with_dns(org_data: OrganizationRegistrationRequest):
    organization = None
    dns_created = False
    odoo_lead_created = False
    
    try:
        # Step 1: Create organization
        organization = await create_organization(org_data)
        
        # Step 2: Create DNS record
        dns_created = await dns_service.create_subdomain_record(
            organization.subdomain, 
            settings.SERVER_PUBLIC_IP
        )
        
        if not dns_created:
            raise Exception("DNS record creation failed")
        
        # Step 3: Create Odoo Lead (non-blocking)
        try:
            odoo_lead_created = await odoo_service.create_lead({
                "name": organization.name,
                "email": organization.admin_email,
                "website": f"{organization.subdomain}.sonicus.eu"
            })
        except Exception as e:
            logger.warning(f"Odoo lead creation failed (non-critical): {e}")
        
        # Step 4: Wait for DNS propagation
        propagated = await dns_verification_service.wait_for_dns_propagation(
            organization.subdomain
        )
        
        if propagated:
            organization.domain_verified = True
            await db.commit()
            return organization
        else:
            raise Exception("DNS propagation timeout")
            
    except Exception as e:
        # Rollback operations
        if dns_created:
            await dns_service.delete_subdomain_record(organization.subdomain)
        if organization:
            await delete_organization(organization.id)
        # Note: Odoo leads are typically not rolled back as they serve as audit trail
        raise e
```

### DNS Management Dashboard

Add DNS management to the super admin panel:

```python
# backend/app/routers/super_admin.py
@router.post("/organizations/{org_id}/dns/recreate")
async def recreate_dns_record(org_id: uuid.UUID):
    """Recreate DNS record for organization subdomain"""
    organization = await get_organization(org_id)
    
    success = await dns_service.create_subdomain_record(
        organization.subdomain,
        settings.SERVER_PUBLIC_IP
    )
    
    return {"success": success, "subdomain": f"{organization.subdomain}.sonicus.eu"}

@router.delete("/organizations/{org_id}/dns")
async def delete_dns_record(org_id: uuid.UUID):
    """Delete DNS record for organization subdomain"""
    organization = await get_organization(org_id)
    
    success = await dns_service.delete_subdomain_record(organization.subdomain)
    
    return {"success": success}
```

### Required Environment Variables

Add to your `.env` file:
```env
# IONOS DNS API Configuration
IONOS_API_KEY=your_ionos_api_key_here
SERVER_PUBLIC_IP=your_server_public_ip
DNS_TTL=3600
DNS_VERIFICATION_TIMEOUT=300

# Revolut Payment Integration
REVOLUT_API_KEY=your_revolut_api_key
REVOLUT_API_URL=https://business-api.revolut.com
REVOLUT_WEBHOOK_SECRET=your_webhook_secret
REVOLUT_ENABLED=true

# Odoo CRM Integration
ODOO_URL=https://your-odoo-instance.com
ODOO_DATABASE=your_database_name
ODOO_USERNAME=your_api_username
ODOO_API_KEY=your_api_key
ODOO_LEAD_ENABLED=true

# Container Deployment Webhooks
DEPLOYMENT_WEBHOOK_URL=https://your-deployment-service.com/webhook
DEPLOYMENT_WEBHOOK_SECRET=your_webhook_secret
CONTAINER_DEPLOYMENT_ENABLED=true

# Email Configuration
SMTP_HOST=smtp.your-provider.com
SMTP_PORT=587
SMTP_USERNAME=your_smtp_username
SMTP_PASSWORD=your_smtp_password
FROM_EMAIL=noreply@sonicus.eu
```

### Production Considerations

1. **Rate Limiting**: IONOS API has rate limits - implement proper queuing
2. **Error Handling**: Robust error handling for DNS API failures
3. **Monitoring**: Monitor DNS record creation and propagation
4. **Backup DNS**: Consider secondary DNS provider for redundancy
5. **SSL Certificates**: Ensure wildcard SSL certificates cover new subdomains

---

## 🔄 **Complete Workflow Analysis**

### **🎯 High-Level User Journey**

#### **For Business Customers (Main Domain - sonicus.eu):**
1. **Landing Page Visit** → User visits `sonicus.eu`
2. **"Get Started" Click** → Triggers business registration flow
3. **Company Registration** → Fill company details, tax info, billing
4. **Revolut Payment Setup** → Choose subscription plan and payment method
5. **Subdomain Creation** → System generates and validates unique subdomain
6. **Subdomain Customization** → User can modify suggested subdomain
6. **DNS Creation** → Automatic DNS record creation via IONOS API
7. **Organization Provisioning** → Database, admin user, billing setup
8. **Access Granted** → Business can access their `company.sonicus.eu` subdomain

#### **For End-Users (Subdomain - company.sonicus.eu):**
1. **Subdomain Visit** → User visits `company.sonicus.eu`
2. **"Get Started" Click** → Triggers customer registration for that company
3. **Customer Registration** → User registers as customer of that business
4. **Tenant-Specific App** → Access to company-branded therapeutic sound platform

---

## 🏗️ **Technical Implementation Workflow**

### **Phase 1: Request Processing Flow**

#### **1.1 Tenant Detection Pipeline**
```
HTTP Request → TenantDetectionMiddleware → Extract Host Header → Parse Subdomain
     ↓
Domain Type Detection → Main Domain vs Subdomain → Store TenantContext
     ↓
Organization Lookup → Database Query by Subdomain → Validate Tenant
     ↓
Session Management → B2B2CSessionManager → Route to Correct Database
```

#### **1.2 Database Routing Logic**
```
Request with Tenant Context → Session Manager → Organization Database
     ↓
No Tenant Context → Master Database (Main Domain)
     ↓
Invalid/Missing Tenant → Error Handling → 404/Redirect
```

### **Phase 2: Business Registration Workflow**

#### **2.1 Frontend Registration Flow**
```
User Clicks "Get Started" → Domain Detection (sonicus.eu) → Business Registration Form
     ↓
Company Details Entry → Real-time Subdomain Generation → Availability Check
     ↓
Revolut Payment Setup → Subscription Plan Selection → Payment Method Configuration
     ↓
Subdomain Confirmation → Terms Acceptance → Submit Registration → API Call
     ↓
Organization Creation Process
```

#### **2.2 Backend Organization Creation**
```
Registration API Call → Input Validation → Subdomain Availability Check
     ↓
Database Transaction Start → Create Organization Record → Generate Admin User
     ↓
DNS Record Creation (IONOS API) → Database Provisioning → Container Deployment Webhook
     ↓
Odoo Lead Creation → Email Notifications → DNS Propagation Wait → Domain Verification
     ↓
Transaction Commit → Success Response → Email Confirmation Pending
```

### **Phase 3: DNS Management Workflow**

#### **3.1 Automated DNS Creation**
```
Organization Registration → IONOS DNS Service → Get Zone ID for sonicus.eu
     ↓
Create A Record → subdomain.sonicus.eu → Points to SERVER_PUBLIC_IP
     ↓
DNS Propagation → Verification Loop → Domain Verified Flag Update
     ↓
Rollback on Failure → Delete DNS + Organization → Error Response
```

#### **3.2 DNS Verification Process**
```
DNS Record Created → DNS Resolver Check → Verify IP Resolution
     ↓
Retry Logic (30 attempts, 10s intervals) → Propagation Confirmation
     ↓
Success: domain_verified = TRUE → Failure: Rollback + Error
```

---

## 🎨 **Frontend Architecture Flow**

### **App Rendering Decision Tree**
```
App.js Load → domainDetection.js → Extract window.location.hostname
     ↓
Is Main Domain? → YES: Render Landing Page + Business Registration
     ↓
Is Subdomain? → YES: Extract Tenant → Render Tenant-Specific App
     ↓
Invalid Domain? → Error Page or Redirect to Main Domain
```

### **Tenant-Specific Features**
```
Subdomain Detected → TenantContext Provider → Load Organization Data
     ↓
Custom Branding → Colors, Logo, Company Name → Tenant Navigation
     ↓
Scoped Authentication → Organization-specific Users → Isolated Data Access
```

---

## 🔐 **Security & Data Isolation Workflow**

### **Multi-Tenant Security Pipeline**
```
Request → Tenant Detection → Organization Validation → Database Routing
     ↓
Cross-Tenant Validation → User Organization Membership Check
     ↓
Data Query Filtering → Organization-Scoped Results Only
     ↓
Response Sanitization → Remove Cross-Tenant References
```

### **Authentication Flow**
```
Login Request → Tenant Context → Organization-Specific Auth
     ↓
JWT Token Generation → Include Organization ID → Tenant-Scoped Permissions
     ↓
Session Storage → Subdomain-Specific Sessions → Cross-Domain Prevention
```

---

## 📊 **Database Operations Workflow**

### **Session Management Flow**
```
API Request → B2B2CSessionManager → Get User/Tenant Context
     ↓
Organization Member? → Organization Database Connection
     ↓
Super Admin? → Master Database Connection  
     ↓
Legacy User? → User-Specific Database Connection
     ↓
Fallback → Master Database with Limited Access
```

### **Data Migration Process**
```
Existing Organizations → Generate Subdomains → Update Database Schema
     ↓
Reserved Subdomains Check → Conflict Resolution → Subdomain Assignment
     ↓
DNS Record Creation → Verification → Production Migration
```

---

## 🚀 **Deployment & Infrastructure Workflow**

### **DNS Infrastructure Setup**
```
Wildcard DNS (*.sonicus.eu) → Load Balancer Configuration → SSL Certificate
     ↓
IONOS API Integration → Automated Record Management → Monitoring Setup
     ↓
Production Deployment → Health Checks → Performance Monitoring
```

### **Error Handling & Rollback**
```
Registration Failure → DNS Cleanup → Database Rollback → User Notification
     ↓
DNS Failure → Organization Deletion → Payment Refund → Error Logging
     ↓
Propagation Timeout → Retry Logic → Manual Intervention → Support Alert
```

---

## 🎯 **Success Metrics & Monitoring**

### **Technical KPIs**
- **Tenant Isolation**: 100% data separation validation
- **Response Time**: <200ms subdomain resolution
- **Uptime**: 99.9% availability across all subdomains
- **Security**: Zero cross-tenant data access incidents

### **Business KPIs**
- **Conversion Rate**: Business registration to active subdomain
- **Time to Value**: Registration to first end-user onboarding
- **Platform Adoption**: Active subdomains vs total registrations
- **Customer Success**: Subdomain usage and engagement metrics

---

## 🔄 **Complete End-to-End Flow Summary**

1. **Business Discovery**: Company visits `sonicus.eu` landing page
2. **Registration Intent**: Clicks "Get Started" for business registration
3. **Information Gathering**: Provides company details, tax info, billing
4. **Subdomain Creation**: System generates and validates unique subdomain
5. **Technical Provisioning**: DNS records, database, admin user creation
6. **Container Deployment**: Trigger webhook to deploy dedicated Sonicus instance
7. **CRM Integration**: Business registered as Lead in Odoo CRM system
8. **Verification**: DNS propagation and domain verification
9. **Access Granted**: Business receives `company.sonicus.eu` access
10. **End-User Onboarding**: Customers visit subdomain and register as customers
9. **Platform Usage**: Tenant-specific therapeutic sound platform access
10. **Ongoing Management**: Business admin manages users, content, analytics

---

**Note**: This implementation plan builds upon the existing B2B2C architecture already present in the Sonicus codebase. The multi-tenant session management and organization database isolation systems are already in place, which significantly simplifies this implementation.
