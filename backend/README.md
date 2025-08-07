# 🌿 Sonicus - B2B2C Therapeutic Sound Healing Platform

**From Direct-to-Consumer to Enterprise Wellness Solution**

Sonicus has evolved into a sophisticated B2B2C SaaS platform that enables businesses to provide therapeutic sound healing wellness programs to their employees. The platform features a unified authentication system with Authentik OIDC integration.

## 🏗️ **Architecture Overview**

### **Authentication System:**
- **🔐 Authentik OIDC Integration**: Unified authentication across all platform levels
- **🔑 Role-Based Access Control**: Groups-based permissions (sonicus-super-admin, sonicus-business-admin, sonicus-user)
- **📊 Comprehensive Audit Logging**: Structured logging with detailed activity tracking
- **⚡ FastAPI Dependencies**: Consistent auth dependencies across all routers

### **Platform Levels:**

1. **🔹 Super Admin** (Platform Owner - Sonicus)
   - Manages business customers and global content library
   - Controls platform-wide analytics and system administration
   - Authentik Group: `sonicus-super-admin`

2. **🔸 Business Admin** (Organization Customers)
   - Manages employee wellness programs and sound therapy packages
   - Tracks engagement metrics and communicates with team members
   - Authentik Group: `sonicus-business-admin`

3. **👤 End Users** (Employees/Members)
   - Access personalized sound therapy and wellness programs
   - Authentik Group: `sonicus-user`

## ⚡ **Current Development Status**

### **✅ Completed Features**
- **Authentication System Consolidation**: All routers now use unified Authentik OIDC authentication
- **Organization CRUD Operations**: Complete organization management with audit logging
- **Business Admin Routers**: Employee management, packages, communications, wellness tracking
- **Dashboard Systems**: Metrics, WebSocket, and management dashboards with Authentik auth
- **Audit Logging**: Comprehensive structured logging with user activity tracking
- **FastAPI Integration**: 94 routes successfully registered with consistent auth dependencies

### **🔧 Setup Required**
- **Authentik OIDC Configuration**: Need to create OIDC provider and application in Authentik
- **Environment Variables**: Configure AUTHENTIK_CLIENT_ID, AUTHENTIK_CLIENT_SECRET
- **User Groups**: Set up sonicus-super-admin, sonicus-business-admin, sonicus-user groups
- **Test Users**: Create development users for each role level

### **📊 Development Tools**
```bash
# Test Authentik connectivity
python3 scripts/comprehensive_discovery.py

# Validate environment setup
python3 scripts/validate_authentik_config.py

# Run authentication flow tests
python3 scripts/test_authentik_flow.py
```

## 🚀 **Quick Start**

### **Backend Development & Authentik Setup**
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Configure AUTHENTIK_* variables

# Test Authentik connectivity
python3 scripts/comprehensive_discovery.py

# Start development server
python3 run.py
# API available at http://localhost:8000
# API Docs at http://localhost:8000/docs
```

### **🔐 Authentik OIDC Setup**

**Required Authentik Configuration:**

1. **Access Authentik Admin**: https://authentik.elefefe.eu/if/admin/
2. **Create OIDC Provider**: Applications → Providers → Create OAuth2/OpenID Provider
3. **Create Application**: Applications → Applications → Create New Application
   - **Name**: Sonicus Platform
   - **Slug**: `sonicus-platform` (important for endpoints)
   - **Provider**: Link to the OIDC provider created above

4. **Configure Groups**: Directory → Groups
   - `sonicus-super-admin` - Platform administrators
   - `sonicus-business-admin` - Organization managers  
   - `sonicus-user` - End users/employees

5. **Environment Variables**:
```bash
AUTHENTIK_BASE_URL=https://authentik.elefefe.eu
AUTHENTIK_CLIENT_ID=your-client-id
AUTHENTIK_CLIENT_SECRET=your-client-secret
AUTHENTIK_REDIRECT_URI=http://localhost:3000/auth/callback
```

### **Frontend Development**
```bash
cd frontend
npm install
npm start
# Access at http://localhost:3001
```

### **Admin Access Points**
- **Main Site**: http://localhost:3001
- **Super Admin**: http://localhost:3001/super-admin
- **Business Admin**: http://localhost:3001/business-admin
- **Original Admin**: http://localhost:3001/admin

## 🎨 **Design Language**

### **Therapeutic Color Palette**
```css
/* Primary Colors - Calming & Natural */
--primary-sage: #87A96B;      /* Calming sage green */
--primary-lavender: #B4A5D6;  /* Soothing lavender */
--primary-ocean: #6B9BD2;     /* Peaceful ocean blue */

/* Accent Colors - Warm & Supportive */
--accent-warm: #F4C2A1;       /* Warm peach accent */
--accent-success: #7FB069;    /* Success green */
```

### **Design Principles**
- **Soft, rounded corners** (8-12px) for therapeutic feel
- **Generous white space** for calm, uncluttered interface
- **Subtle shadows** for depth without harshness
- **Smooth animations** (300ms ease) for fluid interactions

## 🏢 **B2B2C Features**

### **Super Admin Panel** (`/super-admin`)
- **📊 Platform Dashboard**: Revenue, user growth, system health
- **🏢 Organization Management**: Business customer lifecycle
- **🎵 Global Content Library**: Sound therapy template management
- **⚙️ System Administration**: Platform-wide operations

### **Business Admin Panel** (`/business-admin`)
- **📈 Wellness Dashboard**: Employee engagement & impact metrics
- **👥 Employee Management**: User onboarding & progress tracking
- **📦 Package Management**: Sound therapy program assignment
- **💬 Communications**: Team wellness messaging & feedback

### **Multi-Tenant Database Architecture**
- Each organization gets isolated PostgreSQL database
- Secure data separation at the database level
- Scalable user management per organization
- Individual backup and recovery capabilities

## 🛠️ **Technology Stack**

### **Frontend**
- **React 18** with hooks and context
- **React Router** for SPA navigation
- **Custom CSS** with therapeutic design system
- **Error Boundaries** for graceful error handling
- **Firebase Auth** with development mode fallback

### **Backend** 
- **FastAPI** with automatic OpenAPI documentation
- **PostgreSQL** multi-tenant database architecture
- **SQLAlchemy ORM** with async support
- **Authentik OIDC Authentication** (https://authentik.elefefe.eu)
- **Redis** for caching and session management

### **DevOps & Infrastructure**
- **Docker** containerization with multi-service architecture
- **PostgreSQL 15** multi-tenant database with health checks
- **Redis 7** caching with password authentication
- **Authentik OIDC** integration for enterprise SSO
- **Environment-based** configuration management
- **Scalable deployment** with Docker Compose
- **Health monitoring** for all services

## 📱 **Responsive Design**

### **Mobile-First Approach**
```css
/* Breakpoints */
@media (min-width: 768px)  { /* Tablet */ }
@media (min-width: 1024px) { /* Desktop */ }
@media (min-width: 1440px) { /* Large Desktop */ }
```

### **Touch-Friendly Interface**
- **44px minimum** touch targets
- **Swipe gestures** for data tables
- **Collapsible navigation** on mobile
- **Progressive disclosure** of complex features

## 🔐 **Security & Authentication**

### **Authentik OIDC Integration**
The platform uses **Authentik OIDC** (https://authentik.elefefe.eu) for secure, centralized authentication:

- **🔗 Single Sign-On (SSO)** across all platform levels
- **🎯 Role-based Access Control** with group mapping
- **🔄 Automatic User Synchronization** with local database
- **🛡️ Stateless Authentication** with JWT tokens
- **📊 Audit Logging** for all authentication events

### **Authentication Endpoints**
```
GET  /auth/login     # Initiate OIDC login flow
POST /auth/callback  # Handle OIDC callback
GET  /auth/me        # Get current user info
POST /auth/logout    # Logout user
```

### **Role-Based Access Control**
```
Super Admin (Platform Owner)
├── Full platform access
├── Business management
├── Content & template control
└── System administration

Business Admin (Customer Organization)
├── Organization-specific access
├── End-user management
├── Business analytics
└── Communication tools

Staff Member (Within Organization)  
├── Limited user management
├── Basic reporting
└── Content assignment

End User
├── Personal dashboard
├── Sound therapy access
└── Progress tracking
```

### **Data Isolation & Security**
- **Database-level** tenant separation
- **API-level** access controls with Authentik OIDC
- **Role-based** feature access
- **Audit logging** for all admin actions
- **HTTPS enforcement** in production
- **Token-based authentication** with automatic refresh

## 🚀 **Development Workflow**

### **Prerequisites**
```bash
# Node.js 18+ for frontend
node --version

# Python 3.11+ for backend
python --version

# PostgreSQL 15+ for database
psql --version

# Docker & Docker Compose for containerized development
docker --version
docker compose --version
```

### **Environment Setup**

#### **Option 1: Docker Development (Recommended)**
```bash
# Clone repository
git clone <repository-url>
cd Sonicus

# Start all services with Docker
docker compose up -d

# Access services:
# - Backend API: http://localhost:18100
# - Frontend: http://localhost:3001
# - PostgreSQL: localhost:5433
# - Redis: localhost:6379
```

#### **Option 2: Local Development**
```bash
# Clone repository
git clone <repository-url>
cd Sonicus

# Start database and Redis with Docker
docker compose up -d postgres redis

# Frontend setup
cd frontend
npm install
cp .env.example .env.local
npm start

# Backend setup (in separate terminal)
cd backend
pip install -r requirements.txt
cp .env.example .env
# Configure AUTHENTIK_* environment variables
python run.py
```

#### **Required Environment Variables**
```bash
# Authentik OIDC Configuration
AUTHENTIK_BASE_URL=https://authentik.elefefe.eu
AUTHENTIK_CLIENT_ID=your-client-id
AUTHENTIK_CLIENT_SECRET=your-client-secret
AUTHENTIK_REDIRECT_URI=http://localhost:18100/auth/callback

# Database Configuration
POSTGRES_SERVER=localhost
POSTGRES_PORT=5433
POSTGRES_USER=postgres
POSTGRES_PASSWORD=e1efefe
POSTGRES_DB=sonicus_db
POSTGRES_SCHEMA=sonicus

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=e1efefe
```

### **Development URLs**
- **Frontend**: http://localhost:3001
- **Backend API**: http://localhost:18100
- **API Documentation**: http://localhost:18100/docs
- **Authentication**: http://localhost:18100/auth/login

## 📊 **Analytics & Metrics**

### **Platform-Level Metrics** (Super Admin)
- Total organizations and growth trends
- Platform-wide user engagement
- Revenue analytics (MRR, ARR, churn)
- Content usage across organizations
- System performance monitoring

### **Business-Level Metrics** (Business Admin)
- Employee wellness program participation
- Individual and team progress tracking
- Program effectiveness measurements
- ROI calculations for wellness initiatives
- Custom reporting for stakeholders

## 🎵 **Content Management**

### **Global Content Library** (Super Admin)
- **Sleep & Relaxation**: 234+ therapeutic sounds
- **Meditation & Mindfulness**: 189+ guided sessions
- **Focus & Productivity**: 156+ concentration aids
- **Nature & Ambient**: 298+ environmental sounds

### **Package Management** (Business Admin)
- Create custom sound therapy packages
- Assign packages to specific employees
- Schedule automated content delivery
- Track package usage and effectiveness
- Customize content based on wellness goals

## 🌐 **API Documentation**

### **Authentication Endpoints (Authentik OIDC)**
```
GET  /auth/login      # Initiate OIDC login flow
POST /auth/callback   # Handle OIDC callback with authorization code
GET  /auth/me         # Get current authenticated user info
POST /auth/logout     # Logout user (client-side token cleanup)
```

### **Super Admin Endpoints**
```
GET  /api/v1/super-admin/organizations/       # List all organizations
POST /api/v1/super-admin/organizations/       # Create organization
GET  /api/v1/super-admin/platform-analytics/  # Platform metrics
GET  /api/v1/super-admin/content-templates/   # Global content
```

### **Business Admin Endpoints**  
```
GET  /api/v1/business-admin/users/            # Organization users
POST /api/v1/business-admin/packages/         # Create sound package
GET  /api/v1/business-admin/analytics/        # Business metrics
POST /api/v1/business-admin/communications/   # Send messages
```

## 🔄 **Migration from D2C to B2B2C**

### **Recent Updates: Authentication Consolidation** ✅

**August 2025: Complete Authentication System Overhaul**
- ✅ **Replaced JWT-based auth** with Authentik OIDC across all routers
- ✅ **Consolidated authentication dependencies** into centralized system
- ✅ **Re-enabled dashboard routers** (metrics, websocket, management)
- ✅ **Unified role-based access control** with Authentik group mapping
- ✅ **Removed duplicate authentication functions** from individual routers
- ✅ **Improved security** with stateless OIDC tokens and automatic user sync

**Active Routers with Authentik OIDC:**
- `business_admin_communications` - Team messaging & announcements
- `enhanced_admin_tools` - Super admin organization management
- `business_admin_employees` - Employee lifecycle management
- `business_admin_packages` - Sound therapy package assignment
- `organization_metrics` - Business analytics & reporting
- `wellness_impact_tracking` - Wellness program effectiveness
- `dashboard_metrics` - Real-time platform metrics
- `dashboard_websocket` - Live dashboard updates
- `dashboard_management` - System cache & operations

### **Database Schema Updates**
```sql
-- Organizations table
CREATE TABLE organizations (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    subscription_tier VARCHAR(50),
    max_users INTEGER DEFAULT 10
);

-- Update users table
ALTER TABLE users ADD COLUMN organization_id UUID;
ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT 'user';
```

### **Data Migration Process**
1. **Backup existing user data**
2. **Create default organization** for existing users
3. **Update user roles** based on current permissions
4. **Migrate sound libraries** to organization packages
5. **Verify data integrity** and relationships

## 🎯 **Roadmap & Future Features**

### **Phase 1: Foundation** ✅
- [x] Multi-tenant database architecture
- [x] Super Admin panel implementation
- [x] Business Admin panel creation
- [x] Role-based access control
- [x] **Authentik OIDC integration**
- [x] **Consolidated authentication system**
- [x] **Dashboard routers re-enabled**

### **Phase 2: Enhancement** 🚧
- [x] Advanced analytics dashboard
- [ ] Custom branding per organization
- [x] API rate limiting and monitoring
- [ ] Automated billing integration

### **Phase 3: Scale** 📋
- [ ] Mobile application
- [ ] Advanced AI-powered recommendations
- [ ] Integration marketplace
- [ ] White-label solutions

## 📞 **Support & Contact**

### **For Platform Issues**
- **Email**: platform@sonicus.com
- **Documentation**: [docs.sonicus.com](https://docs.sonicus.com)
- **Status Page**: [status.sonicus.com](https://status.sonicus.com)

### **For Business Partnerships**
- **Email**: business@sonicus.com
- **Phone**: +1 (555) 123-4567
- **Demo**: [schedule a demo](https://sonicus.com/demo)

---

## 🐳 **Docker Development Environment**

### **Running the Containers**

The project includes a complete Docker environment with PostgreSQL, Redis, and the backend service.

#### **Quick Start**
```bash
# Start all services in background
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down
```

#### **Service Configuration**
- **PostgreSQL 15**: `localhost:5433` (user: postgres, password: e1efefe)
- **Redis 7**: `localhost:6379` (password: e1efefe)
- **Backend API**: `localhost:18100` (with hot reload)

#### **Health Checks**
All services include health checks:
```bash
# Check service status
docker compose ps

# View health check logs
docker compose logs postgres
docker compose logs redis
```

#### **Development with Hot Reload**
The backend container is configured for development with volume mounting:
- Code changes are automatically reloaded
- Logs are accessible via `docker compose logs backend`
- Database and Redis persist data in Docker volumes

#### **Production Deployment**
For production deployments:
1. Update environment variables in docker-compose.yml
2. Configure proper secrets management
3. Set up reverse proxy (nginx/traefik)
4. Enable HTTPS with SSL certificates
5. Configure backup strategies for volumes

---

**Sonicus B2B2C Platform** - *Transforming workplace wellness through therapeutic sound healing at enterprise scale.*

*Built with ❤️ for human wellness and organizational health.*

For questions or support, open an issue in this repository.