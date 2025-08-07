import React, { createContext, useContext, useState, useEffect } from "react";
import axios from "../utils/axios"; // Use configured axios instance
import { 
  generateAuthURL, 
  generateLogoutURL, 
  parseURLParams, 
  validateState,
  generateRandomState 
} from "../config/authentik";

const AuthContext = createContext();

export function AuthProvider({ children }) {
  // Explicitly disable any Firebase functionality
  if (typeof window !== 'undefined') {
    window.FIREBASE_DISABLED = true;
    window.FIREBASE_CONFIG_DISABLED = true;
  }

  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  
  // Enhanced authentication state for B2C model
  const [userRole, setUserRole] = useState('user');
  const [permissions, setPermissions] = useState([]);
  const [sessionType, setSessionType] = useState('standard');

  useEffect(() => {
    const initializeAuth = async () => {
      // Check for stored tokens first (JWT-based auth)
      const storedToken = localStorage.getItem('access_token');
      if (storedToken) {
        try {
          axios.defaults.headers.common["Authorization"] = `Bearer ${storedToken}`;
          const response = await axios.get("/users/me");
          const userData = response.data;
          
      // Set authentication state
      setUser(userData);
      setUserRole(userData.role || 'user');
      setPermissions(userData.permissions || ['read']);
      setSessionType(userData.role?.includes('admin') ? 'admin' : 'standard');        } catch (error) {
          console.warn('Stored token is invalid, clearing...');
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          delete axios.defaults.headers.common["Authorization"];
        }
      }
      
      setLoading(false);
    };

    initializeAuth();
  }, []);

  const clearAuthState = () => {
    setUser(null);
    setUserRole('user');
    setPermissions([]);
    setSessionType('standard');
    delete axios.defaults.headers.common["Authorization"];
  };

  // Enhanced login for B2C customers
  const login = async (email, password) => {
    try {
      setLoading(true);
      
      // Use working backend authentication endpoint
      const response = await axios.post('/token', 
        new URLSearchParams({
          username: email,
          password: password,
          grant_type: 'password'
        }), 
        {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
          }
        }
      );
      
      const authData = response.data;
      
      // Get user details from /users/me endpoint
      axios.defaults.headers.common["Authorization"] = `Bearer ${authData.access_token}`;
      const userResponse = await axios.get('/users/me');
      const userData = userResponse.data;
      
      // Set authentication state
      setUser(userData);
      setUserRole(userData.role || 'user');
      setPermissions(userData.permissions || ['read']);
      setSessionType(userData.role?.includes('admin') ? 'admin' : 'standard');
      
      // Store tokens securely - use access_token to match backend
      localStorage.setItem('access_token', authData.access_token);
      if (authData.refresh_token) {
        localStorage.setItem('refresh_token', authData.refresh_token);
      }
      
      return { ...authData, user: userData };
      
    } catch (error) {
      throw error;
    } finally {
      setLoading(false);
    }
  };

  // Authentik OIDC Login (redirect-based)
  const loginWithAuthentik = async () => {
    try {
      const state = generateRandomState();
      sessionStorage.setItem('oidc_state', state);
      
      const authURL = generateAuthURL(state);
      window.location.href = authURL;
      
    } catch (error) {
      console.error("Authentik OIDC login failed:", error);
      throw error;
    }
  };

  // Handle OIDC callback
  const handleAuthCallback = async () => {
    try {
      setLoading(true);
      
      const params = parseURLParams();
      const { code, state, error } = params;
      
      if (error) {
        throw new Error(`OIDC Error: ${error}`);
      }
      
      if (!code) {
        throw new Error('Authorization code not received');
      }
      
      // Validate state parameter
      const storedState = sessionStorage.getItem('oidc_state');
      if (!validateState(state, storedState)) {
        throw new Error('Invalid state parameter');
      }
      
      // Exchange code for tokens via backend
      const response = await axios.post('/auth/callback', {
        code: code,
        redirect_uri: process.env.REACT_APP_AUTHENTIK_REDIRECT_URI
      });
      
      const authData = response.data;
      
      // Set authentication state
      setUser(authData.user);
      setCurrentOrganization(authData.organization || null);
      setUserRole(authData.role || 'user');
      setPermissions(authData.permissions || ['read']);
      setSessionType(authData.session_type || 'standard');
      
      // Store tokens
      localStorage.setItem('access_token', authData.access_token);
      if (authData.refresh_token) {
        localStorage.setItem('refresh_token', authData.refresh_token);
      }
      
      // Clear OIDC state
      sessionStorage.removeItem('oidc_state');
      
      // Set axios header
      axios.defaults.headers.common["Authorization"] = `Bearer ${authData.access_token}`;
      
      return authData;
      
    } catch (error) {
      console.error("OIDC callback failed:", error);
      setLoading(false);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  // Send organization invitation
  const sendInvitation = async (email, role, organizationId = null, message = null) => {
    try {
      const response = await axios.post('/auth/invite', {
        email,
        role,
        organization_id: organizationId,
        message
      });
      
      return response.data;
    } catch (error) {
      console.error("Invitation failed:", error);
      throw error;
    }
  };

  // Accept organization invitation
  const acceptInvitation = async (invitationToken) => {
    try {
      const response = await axios.post('/auth/accept-invitation', {
        token: invitationToken
      });
      
      // Refresh user data after accepting invitation
      await refreshUserData();
      
      return response.data;
    } catch (error) {
      console.error("Accept invitation failed:", error);
      throw error;
    }
  };

  // Refresh user authentication data
  const refreshUserData = async () => {
    try {
      const response = await axios.get('/users/me');
      const userData = response.data;
      
      setUser(userData);
      setUserRole(userData.role);
      setPermissions(userData.permissions || []);
      
    } catch (error) {
      console.error("Failed to refresh user data:", error);
    }
  };

  // Get audit log
  const getAuditLog = async (days = 7) => {
    try {
      const response = await axios.get(`/auth/audit-log?days=${days}`);
      return response.data;
    } catch (error) {
      console.error("Failed to get audit log:", error);
      throw error;
    }
  };

  // Enhanced logout with token revocation
  const logout = async () => {
    try {
      // Revoke tokens on server (this endpoint might not exist for local JWT)
      try {
        await axios.post('/auth/logout');
      } catch (error) {
        console.warn("Token revocation failed:", error);
      }
      
      // Clear local storage
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      sessionStorage.removeItem('oidc_state');
      
      // Clear authentication state
      clearAuthState();
      
      // For local development with JWT, just redirect to home page
      // Only redirect to Authentik if we're actually using OIDC
      const isUsingOIDC = false; // Set to true when actually using Authentik OIDC
      
      if (isUsingOIDC) {
        const logoutURL = generateLogoutURL(window.location.origin);
        window.location.href = logoutURL;
      } else {
        // For local JWT authentication, just redirect to home page
        window.location.href = '/';
      }
      
    } catch (error) {
      console.error("Logout failed:", error);
      // Force clear state even if logout fails
      clearAuthState();
      // Always redirect to home page on error
      window.location.href = '/';
    }
  };

  // Role and permission checking utilities for B2C model
  const hasRole = (requiredRole) => {
    const roleHierarchy = {
      'guest': 0,
      'user': 1,
      'customer': 1,
      'super_admin': 2
    };
    
    const currentRoleLevel = roleHierarchy[userRole] || 0;
    const requiredRoleLevel = roleHierarchy[requiredRole] || 0;
    
    return currentRoleLevel >= requiredRoleLevel;
  };

  const hasPermission = (permission) => {
    return permissions.includes(permission);
  };

  // B2C model - simplified access control (no organizations)
  const canAccessContent = (contentTier) => {
    if (userRole === 'super_admin') return true;
    
    // Check user's subscription tier access
    const userTier = user?.subscription_tier || 'starter';
    const tierHierarchy = {
      'starter': 0,
      'premium': 1,
      'pro': 2
    };
    
    return (tierHierarchy[userTier] || 0) >= (tierHierarchy[contentTier] || 0);
  };

  // Check if user is authenticated
  const isAuthenticated = !!user;

  const value = {
    // Core authentication state
    user,
    isAuthenticated,
    loading,
    
    // B2C authentication state (simplified)
    userRole,
    permissions,
    sessionType,
    
    // Authentication methods
    login,
    loginWithAuthentik,
    handleAuthCallback,
    logout,
    
    // Utility functions for B2C model
    refreshUserData,
    
    // Utility methods
    hasRole,
    hasPermission,
    canAccessContent,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
