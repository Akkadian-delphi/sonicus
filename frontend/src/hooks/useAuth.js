/**
 * Authentication Hook with OIDC and JWT Support
 * Handles transition between authentication methods
 */

import { useState, useEffect, useContext, createContext, useCallback } from 'react';
import authentikOIDC from '../utils/authentikOIDC';
import axios from '../utils/axios';

// Auth Context
const AuthContext = createContext(null);

// Auth Provider Component
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authType, setAuthType] = useState('jwt'); // 'jwt' or 'oidc'

  const loadOIDCUser = useCallback(async () => {
    try {
      const userInfo = await authentikOIDC.getUserInfo();
      setUser({
        ...userInfo,
        authType: 'oidc'
      });
    } catch (error) {
      console.error('Failed to load OIDC user:', error);
      throw error;
    }
  }, []);

  const loadJWTUser = useCallback(async () => {
    try {
      const response = await axios.get('/users/me');
      setUser({
        ...response.data,
        authType: 'jwt'
      });
    } catch (error) {
      console.error('Failed to load JWT user:', error);
      throw error;
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      if (authType === 'oidc') {
        await authentikOIDC.logout();
      } else {
        // Clear JWT tokens
        localStorage.removeItem('access_token');
        localStorage.removeItem('authToken');
      }
    } catch (error) {
      console.warn('Logout cleanup failed:', error);
    } finally {
      setUser(null);
      setAuthType('jwt');
      window.location.href = '/';
    }
  }, [authType]);

  const refreshAuthentication = useCallback(async () => {
    try {
      if (authType === 'oidc') {
        await authentikOIDC.refreshToken();
        await loadOIDCUser();
      }
      // JWT tokens are handled by the backend
    } catch (error) {
      console.error('Token refresh failed:', error);
      logout();
    }
  }, [authType, loadOIDCUser, logout]);

  const initializeAuth = useCallback(async () => {
    setLoading(true);
    
    try {
      // Check if we have tokens
      const accessToken = localStorage.getItem('access_token');
      const refreshToken = localStorage.getItem('refresh_token');
      
      if (!accessToken) {
        setLoading(false);
        return;
      }

      // Try to determine auth type
      if (refreshToken && authentikOIDC.isAuthenticated()) {
        // Looks like OIDC tokens
        setAuthType('oidc');
        await loadOIDCUser();
      } else {
        // Try JWT authentication
        setAuthType('jwt');
        await loadJWTUser();
      }
    } catch (error) {
      console.error('Auth initialization failed:', error);
      // Clear potentially corrupted tokens
      logout();
    } finally {
      setLoading(false);
    }
  }, [loadOIDCUser, loadJWTUser, logout]);

  // Initialize authentication
  useEffect(() => {
    initializeAuth();
  }, [initializeAuth]);

  // Check for token refresh periodically
  useEffect(() => {
    if (authType === 'oidc' && user) {
      const interval = setInterval(() => {
        if (authentikOIDC.needsRefresh()) {
          refreshAuthentication();
        }
      }, 60000); // Check every minute

      return () => clearInterval(interval);
    }
  }, [authType, user, refreshAuthentication]);

  // Login with OIDC
  const loginWithOIDC = async (returnTo = '/profile') => {
    try {
      // Store return URL for after callback
      if (returnTo) {
        sessionStorage.setItem('oidc_return_to', returnTo);
      }
      
      const authUrl = await authentikOIDC.getAuthorizationUrl();
      window.location.href = authUrl;
    } catch (error) {
      console.error('OIDC login failed:', error);
      throw error;
    }
  };

  // Login with JWT (legacy)
  const loginWithJWT = async (email, password) => {
    try {
      console.log('🔍 Attempting login with:', { email, password: password.substring(0, 3) + '*'.repeat(password.length - 3) });
      
      const response = await axios.post('/token', 
        new URLSearchParams({
          username: email,
          password: password
        }), {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
          }
        }
      );

      console.log('✅ Login successful, token received');
      const { access_token } = response.data;
      localStorage.setItem('access_token', access_token);
      
      setAuthType('jwt');
      await loadJWTUser();
      
      return response.data;
    } catch (error) {
      console.error('❌ JWT login failed:', {
        status: error.response?.status,
        data: error.response?.data,
        message: error.message
      });
      throw error;
    }
  };

  // Handle OIDC callback
  const handleOIDCCallback = async (callbackUrl) => {
    try {
      const tokens = await authentikOIDC.handleCallback(callbackUrl);
      setAuthType('oidc');
      await loadOIDCUser();
      return tokens;
    } catch (error) {
      console.error('OIDC callback failed:', error);
      throw error;
    }
  };

  // Check if user has specific role
  const hasRole = (requiredRole) => {
    if (!user || !user.role) return false;
    
    // Handle both string and array of roles
    if (Array.isArray(requiredRole)) {
      return requiredRole.some(role => 
        user.role.toLowerCase() === role.toLowerCase()
      );
    }
    
    // Case-insensitive comparison for single role
    return user.role.toLowerCase() === requiredRole.toLowerCase();
  };

  // Check if user is business admin
  const isBusinessAdmin = () => {
    return hasRole('business_admin') || hasRole('super_admin');
  };

  // Check if user is super admin
  const isSuperAdmin = () => {
    return hasRole('super_admin');
  };

  const value = {
    user,
    loading,
    authType,
    isAuthenticated: !!user,
    loginWithOIDC,
    loginWithJWT,
    handleOIDCCallback,
    logout,
    hasRole,
    isBusinessAdmin,
    isSuperAdmin,
    refreshAuthentication,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Custom hook to use auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
