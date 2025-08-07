# Authentik Integration Setup Guide

## Overview

This guide explains how to set up Authentik integration for automatic user creation and management in the Sonicus platform.

## Prerequisites

1. **Authentik Server**: Running Authentik instance (https://authentik.elefefe.eu)
2. **API Access**: Authentik API token with appropriate permissions
3. **Application Configuration**: OIDC application configured in Authentik

## Configuration Steps

### 1. Create API Token in Authentik

1. Log in to Authentik Admin interface
2. Navigate to **Applications** → **Tokens**
3. Click **Create** to create a new token
4. Configure the token:
   - **Name**: `sonicus-api-token`
   - **User**: Select a service account or admin user
   - **Key**: Copy the generated key
   - **Expires**: Set appropriate expiration (or leave blank for no expiration)
5. **Permissions**: Ensure the user has permissions to:
   - Create users (`core.add_user`)
   - View users (`core.view_user`)
   - Change users (`core.change_user`)
   - Delete users (`core.delete_user`)
   - Create groups (`core.add_group`)
   - View groups (`core.view_group`)

### 2. Update Environment Configuration

Add the API token to your `.env` file:

```env
# Authentik API Configuration (for user management)
AUTHENTIK_API_TOKEN=ak_your_generated_token_here
```

### 3. Verify Authentik Groups

The system will automatically create these default groups if they don't exist:

- **sonicus-super-admin**: Platform administrators
- **sonicus-business-admin**: Organization administrators
- **sonicus-staff**: Organization staff members
- **sonicus-user**: Regular users

### 4. Test the Integration

You can test the integration using the built-in test functions:

```python
# In your backend environment
from app.services.authentik_service import authentik_service

# Test if service is configured
if authentik_service.is_configured():
    print("✓ Authentik service is properly configured")
else:
    print("✗ Authentik service is not configured")
```

## User Registration Flow

### With Authentik Integration Enabled

1. **User registers** via `/api/v1/users` endpoint
2. **Local user created** in PostgreSQL database
3. **Authentik user created** via API call
4. **User linked** - Local user gets `authentik_user_id`
5. **Group assignment** - User added to appropriate Authentik group
6. **Dual authentication** - User can use both JWT and OIDC

### Registration Process Details

```python
# Registration with Authentik integration
{
    "email": "admin@company.com",
    "password": "secure_password",
    "company_name": "ACME Corp",
    "business_type": "technology",
    "country": "US"
}
```

**Backend Process:**
1. Validate registration data
2. Create organization in local database
3. Create user in local database
4. Create user in Authentik (if configured)
5. Link local and Authentik users
6. Add user to `sonicus-business-admin` group

## Authentication Options

### For New Users (Registered with Authentik)

**Option 1: OIDC Authentication**
- Navigate to login page
- Select "Enterprise SSO"
- Redirect to Authentik for authentication
- Return with OIDC tokens

**Option 2: JWT Authentication**
- Navigate to login page  
- Select "Email & Password"
- Authenticate with local credentials
- Receive JWT token

### For Existing Users (JWT Only)

Users registered before Authentik integration can be migrated:

```python
# Manual sync existing user
from app.services.user_registration_service import user_registration_service

await user_registration_service.sync_user_with_authentik(
    user=existing_user,
    db=db_session,
    password="user_password"  # Optional
)
```

## API Reference

### Authentik Service Methods

```python
from app.services.authentik_service import authentik_service

# Create user
user_data = await authentik_service.create_user(
    email="user@company.com",
    username="username",
    name="Full Name",
    password="password",
    groups=["sonicus-business-admin"]
)

# Get user by email
user = await authentik_service.get_user_by_email("user@company.com")

# Update user
updated = await authentik_service.update_user(user_pk, {"name": "New Name"})

# Delete user
deleted = await authentik_service.delete_user(user_pk)
```

### Registration Service Methods

```python
from app.services.user_registration_service import user_registration_service

# Register with Authentik
user, org, authentik_user = await user_registration_service.register_organization_user(
    user_data=user_data_dict,
    db=db_session,
    create_in_authentik=True
)

# Sync existing user
authentik_user = await user_registration_service.sync_user_with_authentik(
    user=local_user,
    db=db_session
)
```

## Error Handling

### Common Issues

1. **API Token Invalid**
   ```
   ERROR: Authentik API error 401: Unauthorized
   ```
   **Solution**: Verify `AUTHENTIK_API_TOKEN` is correct and user has permissions

2. **User Already Exists**
   ```
   ERROR: API request failed: User with email already exists
   ```
   **Solution**: Check if user exists in Authentik, link existing user instead

3. **Group Not Found**
   ```
   WARNING: Group 'sonicus-business-admin' not found in Authentik
   ```
   **Solution**: Run startup tasks to create default groups

4. **Network Issues**
   ```
   ERROR: Request failed: Connection timeout
   ```
   **Solution**: Check network connectivity to Authentik server

### Graceful Degradation

The system is designed to continue working even if Authentik is unavailable:

- **Registration**: Creates local user only, logs warning
- **Authentication**: JWT authentication continues to work
- **User Management**: Local database operations unaffected

## Security Considerations

### API Token Security

- **Environment Variables**: Store token in environment variables only
- **Rotation**: Regularly rotate API tokens
- **Permissions**: Grant minimum required permissions
- **Monitoring**: Monitor API token usage

### User Data Synchronization

- **Password Handling**: Passwords are hashed before storage/transmission
- **Data Consistency**: Regular sync jobs ensure data consistency
- **Audit Logs**: All user operations are logged

### Network Security

- **HTTPS**: All API calls use HTTPS
- **Certificate Validation**: SSL certificates are validated
- **Rate Limiting**: API calls are rate-limited to prevent abuse

## Monitoring and Maintenance

### Health Checks

```python
# Check Authentik service health
from app.services.authentik_service import authentik_service

is_healthy = authentik_service.is_configured()
groups = await authentik_service.get_groups()
```

### Logs to Monitor

- User creation success/failure
- Group assignment operations
- API token authentication issues
- Network connectivity problems

### Regular Maintenance

1. **Token Rotation**: Rotate API tokens periodically
2. **Group Audit**: Verify group memberships are correct
3. **User Sync**: Run periodic sync for data consistency
4. **Health Monitoring**: Monitor Authentik service availability

## Troubleshooting

### Debug Mode

Enable debug logging in your environment:

```env
DEBUG=True
LOG_LEVEL=DEBUG
```

### Test Commands

```bash
# Test Authentik connectivity
curl -H "Authorization: Bearer YOUR_TOKEN" \
     "https://authentik.elefefe.eu/api/v3/core/users/"

# Test OIDC endpoints
curl "https://authentik.elefefe.eu/.well-known/openid_configuration"
```

### Support Resources

- **Authentik Documentation**: https://docs.goauthentik.io/
- **API Reference**: https://docs.goauthentik.io/developer-docs/api/
- **Community**: https://github.com/goauthentik/authentik/discussions

This integration provides enterprise-grade authentication while maintaining backward compatibility with existing JWT-based authentication.
