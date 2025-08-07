# Authentication System Migration Guide

## Overview

The Sonicus platform has been upgraded from simple JWT authentication to support both JWT (legacy) and OIDC (enterprise) authentication systems with seamless backward compatibility.

## Architecture

### Backend Components

1. **app/core/auth_transition.py** - Main transition authentication system
   - Supports both JWT and OIDC token validation
   - Automatic user synchronization between systems
   - Backward compatibility layer

2. **app/core/authentik_auth.py** - OIDC authentication with Authentik
   - JWKS validation with improved error handling
   - User info retrieval from OIDC provider
   - Token verification with 'kid' support

3. **app/core/security.py** - Legacy JWT authentication
   - Maintains existing JWT token validation
   - User authentication and token generation

4. **app/routers/business_admin.py** - Enhanced business admin endpoints
   - Uses transition authentication for backward compatibility
   - Supports both JWT and OIDC authenticated users
   - Role-based access control with Union types

### Frontend Components

1. **src/hooks/useAuth.js** - Main authentication hook
   - React context provider for authentication state
   - Supports both JWT and OIDC authentication flows
   - Automatic token refresh and user info management
   - Role-based access control helpers

2. **src/utils/authentikOIDC.js** - OIDC client implementation
   - Complete OIDC flow with PKCE security
   - Token exchange and refresh handling
   - Discovery endpoint integration
   - Secure state and code challenge generation

3. **src/pages/LoginPage.js** - Enhanced login page
   - Toggle between JWT and OIDC authentication
   - Enterprise SSO integration
   - User-friendly authentication method selection

4. **src/pages/OIDCCallback.js** - OIDC callback handler
   - Processes OIDC authorization responses
   - Error handling and user feedback
   - Automatic redirection after successful authentication

## Authentication Flow

### OIDC Authentication (Enterprise)

1. **Initiation**: User clicks "Enterprise SSO" on login page
2. **Authorization**: Redirect to Authentik authorization endpoint with PKCE
3. **Callback**: Handle callback at `/auth/oidc/callback`
4. **Token Exchange**: Exchange authorization code for tokens
5. **User Info**: Retrieve user information from OIDC provider
6. **Synchronization**: Sync OIDC user with local database
7. **Session**: Establish authenticated session

### JWT Authentication (Legacy)

1. **Login**: User enters email/password on login page
2. **Validation**: Backend validates credentials
3. **Token**: Generate JWT token with user claims
4. **Session**: Establish authenticated session

## Configuration

### OIDC Configuration

```javascript
// Authentik OIDC Settings
const OIDC_CONFIG = {
  issuer: 'https://authentik.elefefe.eu/application/o/sonicus-platform/',
  clientId: 'JmD6PCGVTSNhfMn6qPBPRV5u0vSkJjqJOE4PEK9W',
  redirectUri: 'http://localhost:3001/auth/oidc/callback',
  scopes: ['openid', 'profile', 'email']
};
```

### Backend Environment Variables

```bash
# Authentik Configuration
AUTHENTIK_ISSUER=https://authentik.elefefe.eu/application/o/sonicus-platform/
AUTHENTIK_CLIENT_ID=JmD6PCGVTSNhfMn6qPBPRV5u0vSkJjqJOE4PEK9W
AUTHENTIK_CLIENT_SECRET=your_client_secret_here

# JWT Configuration (Legacy)
SECRET_KEY=your_jwt_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Usage Examples

### Using the Authentication Hook

```javascript
import { useAuth } from '../hooks/useAuth';

function MyComponent() {
  const { 
    user, 
    isAuthenticated, 
    loading, 
    login, 
    loginWithOIDC, 
    logout,
    hasRole 
  } = useAuth();

  // Check if user has specific role
  if (!hasRole(['business_admin', 'staff'])) {
    return <div>Access denied</div>;
  }

  // Login with OIDC
  const handleOIDCLogin = () => {
    loginWithOIDC('/dashboard');
  };

  // Login with JWT
  const handleJWTLogin = async () => {
    await login(email, password);
  };

  return (
    <div>
      {isAuthenticated ? (
        <div>Welcome, {user.email}!</div>
      ) : (
        <LoginButtons />
      )}
    </div>
  );
}
```

### Backend API Usage

```python
from app.core.auth_transition import get_transition_auth

# Use in FastAPI endpoints
@router.get("/protected-endpoint")
async def protected_endpoint(
    current_user: User = Depends(get_transition_auth)
):
    # Works with both JWT and OIDC authenticated users
    return {"user_id": current_user.id}
```

## Migration Steps

### For Existing Users

1. **No action required** - JWT authentication continues to work
2. **Optional**: Switch to OIDC for enhanced security features
3. **Organization admins**: Can enable OIDC for their organization

### For New Organizations

1. **Recommended**: Use OIDC authentication for enhanced security
2. **Fallback**: JWT authentication available if OIDC unavailable

## Security Features

### OIDC Security (Enterprise)

- **PKCE**: Proof Key for Code Exchange prevents authorization code interception
- **State Validation**: Prevents CSRF attacks
- **Token Refresh**: Automatic token refresh for seamless user experience
- **JWKS Validation**: Cryptographic token validation
- **Secure Storage**: Tokens stored securely in httpOnly cookies (when configured)

### JWT Security (Legacy)

- **Token Expiration**: Short-lived tokens with refresh capability
- **Role-based Access**: User roles encoded in JWT claims
- **Signature Validation**: HMAC-based token validation

## Error Handling

### Common Issues and Solutions

1. **'kid' Error in OIDC**: 
   - Check JWKS endpoint accessibility
   - Verify token format and claims
   - Ensure client configuration matches Authentik

2. **Token Refresh Failures**:
   - Check token expiration settings
   - Verify refresh token storage
   - Ensure network connectivity to auth server

3. **Role Access Issues**:
   - Verify user roles in both JWT and OIDC claims
   - Check role mapping in transition system
   - Ensure proper role synchronization

## Testing

### Manual Testing

1. **OIDC Flow**:
   - Navigate to login page
   - Select "Enterprise SSO"
   - Complete Authentik authentication
   - Verify callback handling

2. **JWT Flow**:
   - Navigate to login page  
   - Select "Email & Password"
   - Enter valid credentials
   - Verify authentication success

### Automated Testing

```javascript
// Use the test configuration
import authTests from '../utils/authTestConfig';

// Run all authentication tests
authTests.runAllTests().then(results => {
  console.log('Test results:', results);
});
```

## Advantages of OIDC over JWT

### Security Benefits

1. **Standardized Protocol**: OIDC is an industry standard built on OAuth 2.0
2. **Enhanced Security**: Built-in protection against common attack vectors
3. **Token Validation**: Cryptographic validation using JWKS
4. **Automatic Key Rotation**: Supports automatic key rotation
5. **Audit Trail**: Better logging and audit capabilities

### Enterprise Features

1. **Single Sign-On**: Seamless access across multiple applications
2. **Identity Federation**: Connect with existing enterprise identity systems
3. **Advanced User Management**: Rich user profiles and attributes
4. **Compliance**: Meets enterprise security and compliance requirements
5. **Scalability**: Better suited for large-scale enterprise deployments

### User Experience

1. **Simplified Authentication**: Single login for multiple services
2. **Reduced Password Fatigue**: Fewer passwords to remember
3. **Faster Login**: Quick authentication through existing sessions
4. **Mobile-Friendly**: Better mobile and PWA support
5. **Session Management**: Superior session handling and timeout management

## Support and Troubleshooting

### Debug Information

Enable debug logging by adding to your environment:

```bash
# Frontend debugging
REACT_APP_DEBUG_AUTH=true

# Backend debugging  
LOG_LEVEL=DEBUG
```

### Common Commands

```bash
# Test OIDC endpoints
curl -X GET "https://authentik.elefefe.eu/.well-known/openid_configuration"

# Test JWKS endpoint
curl -X GET "https://authentik.elefefe.eu/application/o/sonicus-platform/jwks/"

# Test backend health
curl -X GET "http://localhost:18100/api/v1/health"
```

### Contact

For authentication issues or questions:
- Technical: Check browser console and backend logs
- Configuration: Review environment variables and OIDC client settings
- Authentik Issues: Check Authentik admin interface and logs

## Roadmap

### Future Enhancements

1. **Complete JWT Deprecation**: Gradually migrate all users to OIDC
2. **Multi-factor Authentication**: Enhanced MFA support through Authentik
3. **Social Login**: Google, Microsoft, and other social providers
4. **API Key Authentication**: For machine-to-machine communication
5. **Advanced Role Management**: More granular permissions and roles

This migration maintains full backward compatibility while providing a clear path to enhanced security and enterprise features.
