/**
 * Authentik OIDC Authentication Service
 * Handles OIDC authentication flow with Authentik
 */

// OIDC Configuration
const OIDC_CONFIG = {
  baseUrl: process.env.REACT_APP_AUTHENTIK_BASE_URL || 'https://authentik.elefefe.eu',
  clientId: process.env.REACT_APP_AUTHENTIK_CLIENT_ID || 'HyqThUySJmHfm0ubuBWFhaoKDCphL5uf1IiokF2X',
  redirectUri: process.env.REACT_APP_AUTHENTIK_REDIRECT_URI || `${window.location.origin}/auth/oidc/callback`,
  scope: 'openid profile email',
  responseType: 'code',
};

class AuthentikOIDC {
  constructor() {
    this.config = OIDC_CONFIG;
    this.discovery = null;
  }

  /**
   * Get OIDC discovery document
   */
  async getDiscoveryDocument() {
    if (this.discovery) {
      return this.discovery;
    }

    try {
      const response = await fetch(
        `${this.config.baseUrl}/.well-known/openid_configuration`
      );
      
      if (!response.ok) {
        throw new Error(`Failed to fetch OIDC discovery: ${response.status}`);
      }
      
      this.discovery = await response.json();
      return this.discovery;
    } catch (error) {
      console.error('OIDC discovery failed:', error);
      throw error;
    }
  }

  /**
   * Generate authorization URL
   */
  async getAuthorizationUrl(state = null) {
    const discovery = await this.getDiscoveryDocument();
    
    // Generate state parameter for security
    const authState = state || this.generateState();
    localStorage.setItem('oidc_state', authState);
    
    // Generate PKCE challenge
    const codeVerifier = this.generateCodeVerifier();
    const codeChallenge = await this.generateCodeChallenge(codeVerifier);
    localStorage.setItem('oidc_code_verifier', codeVerifier);
    
    const params = new URLSearchParams({
      response_type: this.config.responseType,
      client_id: this.config.clientId,
      redirect_uri: this.config.redirectUri,
      scope: this.config.scope,
      state: authState,
      code_challenge: codeChallenge,
      code_challenge_method: 'S256',
    });
    
    return `${discovery.authorization_endpoint}?${params.toString()}`;
  }

  /**
   * Handle callback from authorization server
   */
  async handleCallback(callbackUrl) {
    const url = new URL(callbackUrl);
    const params = new URLSearchParams(url.search);
    
    const code = params.get('code');
    const state = params.get('state');
    const error = params.get('error');
    
    if (error) {
      throw new Error(`OIDC Error: ${error} - ${params.get('error_description')}`);
    }
    
    // Verify state parameter
    const storedState = localStorage.getItem('oidc_state');
    if (state !== storedState) {
      throw new Error('Invalid state parameter - possible CSRF attack');
    }
    
    if (!code) {
      throw new Error('No authorization code received');
    }
    
    // Exchange code for tokens
    return await this.exchangeCodeForTokens(code);
  }

  /**
   * Exchange authorization code for tokens
   */
  async exchangeCodeForTokens(code) {
    const discovery = await this.getDiscoveryDocument();
    const codeVerifier = localStorage.getItem('oidc_code_verifier');
    
    if (!codeVerifier) {
      throw new Error('Code verifier not found - invalid PKCE flow');
    }
    
    const body = new URLSearchParams({
      grant_type: 'authorization_code',
      client_id: this.config.clientId,
      code: code,
      redirect_uri: this.config.redirectUri,
      code_verifier: codeVerifier,
    });
    
    try {
      const response = await fetch(discovery.token_endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: body.toString(),
      });
      
      if (!response.ok) {
        const errorData = await response.text();
        throw new Error(`Token exchange failed: ${response.status} - ${errorData}`);
      }
      
      const tokens = await response.json();
      
      // Store tokens securely
      localStorage.setItem('access_token', tokens.access_token);
      localStorage.setItem('refresh_token', tokens.refresh_token);
      localStorage.setItem('id_token', tokens.id_token);
      localStorage.setItem('token_expires_at', Date.now() + (tokens.expires_in * 1000));
      
      // Clean up OIDC session data
      localStorage.removeItem('oidc_state');
      localStorage.removeItem('oidc_code_verifier');
      
      return tokens;
    } catch (error) {
      console.error('Token exchange error:', error);
      throw error;
    }
  }

  /**
   * Refresh access token
   */
  async refreshToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }
    
    const discovery = await this.getDiscoveryDocument();
    
    const body = new URLSearchParams({
      grant_type: 'refresh_token',
      client_id: this.config.clientId,
      refresh_token: refreshToken,
    });
    
    try {
      const response = await fetch(discovery.token_endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: body.toString(),
      });
      
      if (!response.ok) {
        // If refresh fails, redirect to login
        this.logout();
        throw new Error('Token refresh failed');
      }
      
      const tokens = await response.json();
      
      // Update stored tokens
      localStorage.setItem('access_token', tokens.access_token);
      localStorage.setItem('token_expires_at', Date.now() + (tokens.expires_in * 1000));
      
      if (tokens.refresh_token) {
        localStorage.setItem('refresh_token', tokens.refresh_token);
      }
      
      return tokens;
    } catch (error) {
      console.error('Token refresh error:', error);
      throw error;
    }
  }

  /**
   * Get user info from token
   */
  async getUserInfo() {
    const accessToken = localStorage.getItem('access_token');
    if (!accessToken) {
      throw new Error('No access token available');
    }
    
    const discovery = await this.getDiscoveryDocument();
    
    try {
      const response = await fetch(discovery.userinfo_endpoint, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
      });
      
      if (!response.ok) {
        if (response.status === 401) {
          // Try to refresh token
          await this.refreshToken();
          return await this.getUserInfo(); // Retry with new token
        }
        throw new Error(`Failed to fetch user info: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Get user info error:', error);
      throw error;
    }
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated() {
    const accessToken = localStorage.getItem('access_token');
    const expiresAt = localStorage.getItem('token_expires_at');
    
    if (!accessToken || !expiresAt) {
      return false;
    }
    
    // Check if token is expired (with 5 minute buffer)
    const now = Date.now();
    const expiry = parseInt(expiresAt);
    
    return now < (expiry - 5 * 60 * 1000); // 5 minutes before expiry
  }

  /**
   * Check if token needs refresh
   */
  needsRefresh() {
    const expiresAt = localStorage.getItem('token_expires_at');
    if (!expiresAt) return false;
    
    const now = Date.now();
    const expiry = parseInt(expiresAt);
    
    // Refresh if token expires within 10 minutes
    return now > (expiry - 10 * 60 * 1000);
  }

  /**
   * Logout user
   */
  async logout() {
    const accessToken = localStorage.getItem('access_token');
    
    // Clear local storage
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('id_token');
    localStorage.removeItem('token_expires_at');
    localStorage.removeItem('oidc_state');
    localStorage.removeItem('oidc_code_verifier');
    
    // Revoke tokens if possible
    if (accessToken) {
      try {
        const discovery = await this.getDiscoveryDocument();
        if (discovery.revocation_endpoint) {
          await fetch(discovery.revocation_endpoint, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
              token: accessToken,
              client_id: this.config.clientId,
            }).toString(),
          });
        }
      } catch (error) {
        console.warn('Token revocation failed:', error);
      }
    }
    
    // Redirect to home or login page
    window.location.href = '/';
  }

  /**
   * Generate random state parameter
   */
  generateState() {
    return Array.from(crypto.getRandomValues(new Uint8Array(32)))
      .map(b => b.toString(16).padStart(2, '0'))
      .join('');
  }

  /**
   * Generate PKCE code verifier
   */
  generateCodeVerifier() {
    const array = new Uint8Array(32);
    crypto.getRandomValues(array);
    return btoa(String.fromCharCode.apply(null, array))
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=/g, '');
  }

  /**
   * Generate PKCE code challenge
   */
  async generateCodeChallenge(verifier) {
    const encoder = new TextEncoder();
    const data = encoder.encode(verifier);
    const digest = await crypto.subtle.digest('SHA-256', data);
    return btoa(String.fromCharCode.apply(null, new Uint8Array(digest)))
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=/g, '');
  }
}

// Export singleton instance
const authentikOIDC = new AuthentikOIDC();
export default authentikOIDC;
