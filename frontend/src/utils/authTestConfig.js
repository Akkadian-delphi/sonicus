/**
 * Test configuration for the new authentication system
 * This file can be run to verify both JWT and OIDC authentication are working
 */

// Test configuration for OIDC
export const OIDC_TEST_CONFIG = {
  // Test URLs for OIDC flow
  authorizationUrl: 'https://authentik.elefefe.eu/application/o/authorize/',
  tokenUrl: 'https://authentik.elefefe.eu/application/o/token/',
  userInfoUrl: 'https://authentik.elefefe.eu/application/o/userinfo/',
  jwksUrl: 'https://authentik.elefefe.eu/application/o/sonicus-platform/jwks/',
  
  // Test client configuration
  clientId: 'JmD6PCGVTSNhfMn6qPBPRV5u0vSkJjqJOE4PEK9W',
  redirectUri: 'http://localhost:3001/auth/oidc/callback',
  
  // Test scopes
  scopes: ['openid', 'profile', 'email'],
  
  // Expected response types
  responseType: 'code',
  grantType: 'authorization_code'
};

// Test configuration for JWT (legacy)
export const JWT_TEST_CONFIG = {
  loginUrl: 'http://localhost:18100/api/v1/auth/login',
  testCredentials: {
    email: 'dev@elefefe.eu',
    password: 'your_test_password_here'
  }
};

// Test functions to verify authentication
export const testAuthentication = {
  
  // Test OIDC authentication flow
  async testOIDC() {
    console.log('Testing OIDC Authentication Flow...');
    
    try {
      // Test discovery endpoint
      const discoveryResponse = await fetch('https://authentik.elefefe.eu/.well-known/openid_configuration');
      const discoveryData = await discoveryResponse.json();
      
      console.log('✅ OIDC Discovery endpoint accessible');
      console.log('Authorization endpoint:', discoveryData.authorization_endpoint);
      console.log('Token endpoint:', discoveryData.token_endpoint);
      
      // Test JWKS endpoint
      const jwksResponse = await fetch(OIDC_TEST_CONFIG.jwksUrl);
      const jwksData = await jwksResponse.json();
      
      console.log('✅ JWKS endpoint accessible');
      console.log('Available keys:', jwksData.keys?.length || 0);
      
      return {
        success: true,
        discovery: discoveryData,
        jwks: jwksData
      };
      
    } catch (error) {
      console.error('❌ OIDC Test failed:', error);
      return { success: false, error: error.message };
    }
  },
  
  // Test JWT authentication (legacy)
  async testJWT() {
    console.log('Testing JWT Authentication...');
    
    try {
      // Test login endpoint availability
      const response = await fetch(JWT_TEST_CONFIG.loginUrl, {
        method: 'OPTIONS',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      console.log('✅ JWT Login endpoint accessible');
      console.log('Response status:', response.status);
      
      return { success: true };
      
    } catch (error) {
      console.error('❌ JWT Test failed:', error);
      return { success: false, error: error.message };
    }
  },
  
  // Test both authentication methods
  async runAllTests() {
    console.log('🧪 Running Authentication System Tests...\n');
    
    const results = {
      oidc: await this.testOIDC(),
      jwt: await this.testJWT()
    };
    
    console.log('\n📊 Test Results Summary:');
    console.log('OIDC Authentication:', results.oidc.success ? '✅ PASS' : '❌ FAIL');
    console.log('JWT Authentication:', results.jwt.success ? '✅ PASS' : '❌ FAIL');
    
    const allPassed = results.oidc.success && results.jwt.success;
    console.log('\nOverall Status:', allPassed ? '🎉 ALL TESTS PASSED' : '⚠️  SOME TESTS FAILED');
    
    return results;
  }
};

// Export for use in browser console or testing
if (typeof window !== 'undefined') {
  window.authTests = testAuthentication;
  console.log('🔧 Authentication tests available in browser console as window.authTests');
  console.log('Run window.authTests.runAllTests() to test both authentication systems');
}

export default testAuthentication;
