# 🔐 Authentik OIDC Setup Guide for Sonicus Platform

## **Current Status**
✅ **Authentication System**: Fully consolidated and ready for Authentik OIDC  
✅ **Backend Integration**: All routers updated with unified auth dependencies  
⏳ **Authentik Configuration**: Requires OIDC provider and application setup  

## **Prerequisites**
- Authentik instance running at `https://authentik.elefefe.eu` ✅
- Admin access to Authentik interface ✅  
- Backend application ready with authentication dependencies ✅

## **Step-by-Step Configuration**

### **1. Access Authentik Admin Interface**
```bash
# Navigate to Authentik admin
https://authentik.elefefe.eu/if/admin/
```

### **2. Create OIDC Provider**

**Navigate to**: Applications → Providers → Create

**Configuration**:
- **Type**: OAuth2/OpenID Provider
- **Name**: Sonicus Platform OIDC Provider
- **Authentication Flow**: default-authentication-flow (or create custom)
- **Authorization Flow**: default-provider-authorization-explicit-consent
- **Client Type**: Confidential
- **Client ID**: Generate or use custom (save for environment variables)
- **Client Secret**: Generate (save for environment variables)
- **Redirect URIs**: 
  ```
  http://localhost:3000/auth/callback
  http://localhost:8000/auth/callback
  https://sonicus.elefefe.eu/auth/callback
  ```
- **Scopes**: `openid profile email groups`
- **Subject Mode**: Based on User's Email
- **Include Claims in ID Token**: ✅ Enabled

### **3. Create Application**

**Navigate to**: Applications → Applications → Create

**Configuration**:
- **Name**: Sonicus Platform
- **Slug**: `sonicus-platform` ⚠️ **CRITICAL**: This must match backend config
- **Provider**: Select the OIDC provider created in step 2
- **Launch URL**: `https://sonicus.elefefe.eu`
- **Icon**: Upload Sonicus logo (optional)

### **4. Create User Groups**

**Navigate to**: Directory → Groups

**Create the following groups**:

#### **sonicus-super-admin**
- **Name**: Sonicus Super Administrators
- **Attributes**: 
  ```json
  {
    "role": "super_admin",
    "permissions": ["platform_management", "organization_management", "content_management"]
  }
  ```

#### **sonicus-business-admin**
- **Name**: Sonicus Business Administrators  
- **Attributes**:
  ```json
  {
    "role": "business_admin", 
    "permissions": ["employee_management", "package_management", "analytics_access"]
  }
  ```

#### **sonicus-user**
- **Name**: Sonicus Users
- **Attributes**:
  ```json
  {
    "role": "user",
    "permissions": ["content_access", "progress_tracking"]
  }
  ```

### **5. Create Test Users**

**Navigate to**: Directory → Users → Create

**Create test users for each role**:

#### **Super Admin Test User**
- **Username**: `admin@sonicus.dev`
- **Email**: `admin@sonicus.dev`
- **Name**: `Super Admin Development`
- **Groups**: `sonicus-super-admin`
- **Password**: Set secure password
- **Active**: ✅ Enabled

#### **Business Admin Test User**
- **Username**: `bizadmin@sonicus.dev`
- **Email**: `bizadmin@sonicus.dev`
- **Name**: `Business Admin Development`
- **Groups**: `sonicus-business-admin`
- **Password**: Set secure password
- **Active**: ✅ Enabled

#### **Regular User Test User**
- **Username**: `user@sonicus.dev`
- **Email**: `user@sonicus.dev`
- **Name**: `Regular User Development`
- **Groups**: `sonicus-user`
- **Password**: Set secure password
- **Active**: ✅ Enabled

### **6. Configure Environment Variables**

**Update `.env` file**:
```bash
# Authentik OIDC Configuration
AUTHENTIK_BASE_URL=https://authentik.elefefe.eu
AUTHENTIK_CLIENT_ID=your-client-id-from-step-2
AUTHENTIK_CLIENT_SECRET=your-client-secret-from-step-2
AUTHENTIK_REDIRECT_URI=http://localhost:3000/auth/callback

# Application Configuration  
AUTHENTIK_APPLICATION_SLUG=sonicus-platform
AUTHENTIK_ISSUER=https://authentik.elefefe.eu/application/o/sonicus-platform/
```

### **7. Test Configuration**

**Run discovery script**:
```bash
cd backend
python3 scripts/comprehensive_discovery.py
```

**Expected output**:
```
✅ Found OIDC config: /application/o/sonicus-platform/.well-known/openid_configuration
   Issuer: https://authentik.elefefe.eu/application/o/sonicus-platform/
   Auth endpoint: https://authentik.elefefe.eu/application/o/authorize/
   Token endpoint: https://authentik.elefefe.eu/application/o/token/
   UserInfo endpoint: https://authentik.elefefe.eu/application/o/userinfo/
```

**Test authentication flow**:
```bash
python3 scripts/test_authentik_flow.py
```

### **8. Verify Backend Integration**

**Test application startup**:
```bash
cd backend
python3 run.py
```

**Check logs for**:
```
✅ Authentik OIDC configuration loaded
✅ JWKS keys fetched successfully  
✅ All authentication dependencies initialized
```

**Test API endpoints**:
```bash
# Health check
curl http://localhost:8000/health

# OpenAPI documentation
curl http://localhost:8000/docs
```

## **Troubleshooting**

### **Common Issues**

#### **404 on OIDC Discovery**
- ❌ **Issue**: Application slug doesn't match
- ✅ **Solution**: Ensure application slug is exactly `sonicus-platform`

#### **403 Forbidden on API Endpoints** 
- ❌ **Issue**: Missing authentication or wrong permissions
- ✅ **Solution**: Verify user is in correct Authentik group

#### **Token Validation Errors**
- ❌ **Issue**: JWKS endpoint not accessible
- ✅ **Solution**: Check AUTHENTIK_BASE_URL and network connectivity

#### **Group Mapping Not Working**
- ❌ **Issue**: Groups not included in token claims
- ✅ **Solution**: Ensure "Include Claims in ID Token" is enabled in provider

### **Verification Commands**

```bash
# Test Authentik connectivity
python3 scripts/comprehensive_discovery.py

# Validate environment configuration  
python3 scripts/validate_authentik_config.py

# Test complete authentication flow
python3 scripts/test_authentik_flow.py

# Check backend integration
python3 -c "from app.core.authentik_auth import AuthentikAuth; print('✅ Import successful')"
```

## **Next Steps After Setup**

1. **Frontend Integration**: Update React app to use Authentik OIDC flow
2. **Production Deployment**: Configure production environment variables
3. **User Migration**: Import existing users into Authentik
4. **Role Assignment**: Assign appropriate groups to existing users
5. **Testing**: Comprehensive end-to-end authentication testing

## **Support & Documentation**

- **Authentik Documentation**: https://goauthentik.io/docs/
- **OIDC Specification**: https://openid.net/connect/
- **Sonicus Backend README**: `./README.md`
- **Development Scripts**: `./scripts/`
