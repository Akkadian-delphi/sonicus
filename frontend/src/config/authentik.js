/**
 * Authentik OIDC Configuration for Sonicus Frontend
 * Handles OIDC authentication flow with Authentik
 */

// Authentik OIDC Configuration
export const authentikConfig = {
  baseURL: process.env.REACT_APP_AUTHENTIK_BASE_URL || 'https://authentik.elefefe.eu',
  clientId: process.env.REACT_APP_AUTHENTIK_CLIENT_ID || 'HyqThUySJmHfm0ubuBWFhaoKDCphL5uf1IiokF2X',
  redirectUri: process.env.REACT_APP_AUTHENTIK_REDIRECT_URI || 'http://localhost:3000/auth/callback',
  scope: 'openid profile email groups',
  responseType: 'code',
  
  // OIDC endpoints (will be discovered dynamically)
  endpoints: {
    authorization: `${process.env.REACT_APP_AUTHENTIK_BASE_URL || 'https://authentik.elefefe.eu'}/application/o/authorize/`,
    token: `${process.env.REACT_APP_AUTHENTIK_BASE_URL || 'https://authentik.elefefe.eu'}/application/o/token/`,
    userinfo: `${process.env.REACT_APP_AUTHENTIK_BASE_URL || 'https://authentik.elefefe.eu'}/application/o/userinfo/`,
    logout: `${process.env.REACT_APP_AUTHENTIK_BASE_URL || 'https://authentik.elefefe.eu'}/application/o/sonicus/end-session/`
  }
};

/**
 * Generate OIDC authorization URL
 */
export const generateAuthURL = (state = null) => {
  const params = new URLSearchParams({
    client_id: authentikConfig.clientId,
    redirect_uri: authentikConfig.redirectUri,
    response_type: authentikConfig.responseType,
    scope: authentikConfig.scope,
    state: state || generateRandomState(),
  });

  return `${authentikConfig.endpoints.authorization}?${params.toString()}`;
};

/**
 * Generate OIDC logout URL
 */
export const generateLogoutURL = (postLogoutRedirectUri = null) => {
  const params = new URLSearchParams();
  
  if (postLogoutRedirectUri) {
    params.append('post_logout_redirect_uri', postLogoutRedirectUri);
  }

  return `${authentikConfig.endpoints.logout}?${params.toString()}`;
};

/**
 * Generate random state for OIDC security
 */
export const generateRandomState = () => {
  return Math.random().toString(36).substring(2, 15) + 
         Math.random().toString(36).substring(2, 15);
};

/**
 * Parse URL parameters (for callback handling)
 */
export const parseURLParams = (url = window.location.href) => {
  const urlObj = new URL(url);
  const params = {};
  
  for (const [key, value] of urlObj.searchParams) {
    params[key] = value;
  }
  
  return params;
};

/**
 * Validate OIDC state parameter
 */
export const validateState = (receivedState, expectedState = null) => {
  const storedState = expectedState || sessionStorage.getItem('oidc_state');
  return receivedState === storedState;
};

export default authentikConfig;
