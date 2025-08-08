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
- Invoice/billing setup
- Odoo Lead integration

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
- Terms acceptance and payment setup

### 2.4 Tenant-Specific Theming
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
- Billing: Organization-based billing

## 🎨 Frontend Component Structure

```
src/
├── components/
│   ├── business/
│   │   ├── BusinessRegistration.js
│   │   ├── SubdomainGenerator.js
│   │   ├── CompanyDetailsForm.js
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

# backend/app/services/odoo_service.py
import xmlrpc.client
from app.core.config import settings

class OdooService:
    def __init__(self):
        self.url = settings.ODOO_URL
        self.db = settings.ODOO_DATABASE
        self.username = settings.ODOO_USERNAME
        self.api_key = settings.ODOO_API_KEY
        self.enabled = settings.ODOO_LEAD_ENABLED
    
    async def create_lead(self, lead_data: dict) -> bool:
        """Create a lead in Odoo CRM"""
        if not self.enabled:
            return True
            
        try:
            # Connect to Odoo
            common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
            models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
            
            # Authenticate
            uid = common.authenticate(self.db, self.username, self.api_key, {})
            
            if not uid:
                raise Exception("Odoo authentication failed")
            
            # Create lead
            lead_id = models.execute_kw(
                self.db, uid, self.api_key,
                'crm.lead', 'create',
                [lead_data]
            )
            
            logger.info(f"Created Odoo lead with ID: {lead_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create Odoo lead: {e}")
            return False
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

@router.post("/organizations/register")
async def register_organization(org_data: OrganizationRegistrationRequest):
    try:
        # 1. Create organization in database
        organization = await create_organization(org_data)
        
        # 2. Create DNS record for subdomain
        dns_success = await dns_service.create_subdomain_record(
            subdomain=organization.subdomain,
            target_ip=settings.SERVER_PUBLIC_IP
        )
        
        if not dns_success:
            # Handle DNS creation failure
            await rollback_organization_creation(organization.id)
            raise HTTPException(
                status_code=500,
                detail="Failed to create DNS record for subdomain"
            )
        
        # 3. Create Lead in Odoo CRM
        odoo_success = await odoo_service.create_lead({
            "name": organization.name,
            "email": organization.admin_email,
            "phone": organization.phone,
            "website": f"{organization.subdomain}.sonicus.eu",
            "company_name": organization.name,
            "source": "sonicus_registration",
            "description": f"New business registration for {organization.name}"
        })
        
        if not odoo_success:
            # Log warning but don't fail registration
            logger.warning(f"Failed to create Odoo lead for organization {organization.id}")
        
        # 4. Mark domain as verified
        organization.domain_verified = True
        await db.commit()
        
        return {"message": "Organization created successfully", "subdomain": f"{organization.subdomain}.sonicus.eu"}
        
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

# Odoo CRM Integration
ODOO_URL=https://your-odoo-instance.com
ODOO_DATABASE=your_database_name
ODOO_USERNAME=your_api_username
ODOO_API_KEY=your_api_key
ODOO_LEAD_ENABLED=true
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
4. **Subdomain Generation** → System suggests subdomain based on company name
5. **Subdomain Customization** → User can modify suggested subdomain
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
Subdomain Confirmation → Payment Setup → Terms Acceptance
     ↓
Submit Registration → API Call → Organization Creation Process
```

#### **2.2 Backend Organization Creation**
```
Registration API Call → Input Validation → Subdomain Availability Check
     ↓
Database Transaction Start → Create Organization Record → Generate Admin User
     ↓
DNS Record Creation (IONOS API) → Database Provisioning → Odoo Lead Creation
     ↓
Email Notifications → DNS Propagation Wait → Domain Verification → Transaction Commit
     ↓
Success Response → Subdomain Ready → Business Can Access Platform
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
6. **CRM Integration**: Business registered as Lead in Odoo CRM system
7. **Verification**: DNS propagation and domain verification
8. **Access Granted**: Business receives `company.sonicus.eu` access
8. **End-User Onboarding**: Customers visit subdomain and register as customers
9. **Platform Usage**: Tenant-specific therapeutic sound platform access
10. **Ongoing Management**: Business admin manages users, content, analytics

---

**Note**: This implementation plan builds upon the existing B2B2C architecture already present in the Sonicus codebase. The multi-tenant session management and organization database isolation systems are already in place, which significantly simplifies this implementation.
