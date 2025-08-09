import React, { createContext, useContext, useState, useEffect } from "react";
import axios from "../utils/axios";
import { getDomainContext, getTenantContext, buildTenantApiRequest } from "../utils/domainDetection";

const TenantContext = createContext();

export function TenantProvider({ children }) {
  const [tenantMode, setTenantMode] = useState('b2c'); // 'b2c' or 'b2b2c'
  const [organization, setOrganization] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [domainContext, setDomainContext] = useState(null);

  useEffect(() => {
    const detectTenant = async () => {
      try {
        setLoading(true);
        setError(null);

        // Get domain context using new detection utilities
        const domain = getDomainContext();
        const tenant = getTenantContext();
        
        setDomainContext(domain);

        console.log('🌐 Tenant detection:', { domain, tenant });

        // Call backend tenant status endpoint with proper headers
        const { url, options } = buildTenantApiRequest('/api/v1/organizations/status');
        
        const response = await fetch(url, {
          method: 'GET',
          ...options
        });

        if (!response.ok) {
          throw new Error(`Status check failed: ${response.status}`);
        }

        const tenantInfo = await response.json();

        console.log('🏢 Tenant info from backend:', tenantInfo);

        if (tenantInfo.tenant_mode === 'b2b2c') {
          setTenantMode('b2b2c');
          setOrganization(tenantInfo.organization);
        } else {
          setTenantMode('b2c');
          setOrganization(null);
        }

      } catch (error) {
        console.error('❌ Error detecting tenant:', error);
        // Default to B2C mode on error
        setTenantMode('b2c');
        setOrganization(null);
        setError('Failed to detect organization context');
      } finally {
        setLoading(false);
      }
    };

    detectTenant();
  }, []);

  // Helper function to extract subdomain (kept for backward compatibility)
  const getSubdomain = (hostname) => {
    if (hostname === 'localhost' || hostname.startsWith('127.0.0.1')) {
      return null;
    }

    const parts = hostname.split('.');
    if (parts.length > 2) {
      return parts[0];
    }
    return null;
  };

  // Switch between tenant modes (useful for testing)
  const switchTenantMode = (mode, orgData = null) => {
    setTenantMode(mode);
    setOrganization(orgData);
  };

  // Check if user is in organization context
  const isB2B2CMode = () => tenantMode === 'b2b2c';
  const isB2CMode = () => tenantMode === 'b2c';

  // Get organization branding
  const getOrganizationBranding = () => {
    if (!organization || !organization.branding_config) {
      return {
        primaryColor: '#007bff',
        secondaryColor: '#6c757d',
        logo: null,
        companyName: 'Sonicus'
      };
    }

    return {
      primaryColor: organization.branding_config.primary_color || '#007bff',
      secondaryColor: organization.branding_config.secondary_color || '#6c757d',
      logo: organization.branding_config.logo_url,
      companyName: organization.display_name || organization.name
    };
  };

  // Check if organization has feature enabled
  const hasFeature = (feature) => {
    if (tenantMode !== 'b2b2c' || !organization) {
      return false;
    }
    return organization.features_enabled?.[feature] || false;
  };

  // Get organization limits
  const getOrganizationLimits = () => {
    if (tenantMode !== 'b2b2c' || !organization) {
      return {
        maxUsers: Infinity,
        maxSoundLibraries: Infinity
      };
    }

    return {
      maxUsers: organization.max_users || 10,
      maxSoundLibraries: organization.max_sound_libraries || 3
    };
  };

  const value = {
    // Core tenant state
    tenantMode,
    organization,
    loading,
    error,
    domainContext,

    // New domain context properties
    isMainDomain: domainContext?.isMainDomain || false,
    isSubdomain: domainContext?.isSubdomain || false,
    subdomain: domainContext?.subdomain,
    organizationIdentifier: domainContext?.organizationIdentifier,
    isDevelopment: domainContext?.isDevelopment || false,
    domainType: domainContext?.domainType,

    // Helper functions
    isB2B2CMode,
    isB2CMode,
    switchTenantMode,

    // Organization utilities
    getOrganizationBranding,
    hasFeature,
    getOrganizationLimits,

    // Enhanced domain info
    currentDomain: window.location.hostname,
    subdomain: domainContext?.subdomain || getSubdomain(window.location.hostname),
    
    // Tenant API utilities
    buildTenantApiRequest: (endpoint, options = {}) => buildTenantApiRequest(endpoint, options)
  };

  return (
    <TenantContext.Provider value={value}>
      {children}
    </TenantContext.Provider>
  );
}

export function useTenant() {
  const context = useContext(TenantContext);
  if (!context) {
    throw new Error('useTenant must be used within a TenantProvider');
  }
  return context;
}

export default TenantContext;
