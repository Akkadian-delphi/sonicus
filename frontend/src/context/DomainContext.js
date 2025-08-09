/**
 * Domain Context Provider for Multi-Tenant Architecture
 * Provides domain and tenant context throughout the application
 */

import React, { createContext, useContext, useEffect, useState } from 'react';
import { getDomainContext, getTenantContext } from '../utils/domainDetection';

const DomainContext = createContext(null);

export const DomainProvider = ({ children }) => {
  const [domainContext, setDomainContext] = useState(null);
  const [tenantContext, setTenantContext] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    try {
      const domain = getDomainContext();
      const tenant = getTenantContext();
      
      setDomainContext(domain);
      setTenantContext(tenant);
      setLoading(false);
      
      // Log context for debugging
      console.log('🌐 Domain Context Initialized:', { domain, tenant });
      
    } catch (err) {
      console.error('Error initializing domain context:', err);
      setError(err.message);
      setLoading(false);
    }
  }, []);

  const value = {
    domainContext,
    tenantContext,
    loading,
    error,
    
    // Helper methods
    isMainDomain: domainContext?.isMainDomain || false,
    isSubdomain: domainContext?.isSubdomain || false,
    subdomain: domainContext?.subdomain,
    organizationId: domainContext?.organizationIdentifier,
    isDevelopment: domainContext?.isDevelopment || false,
    domainType: domainContext?.domainType,
    
    // Refresh context (useful for dynamic subdomain changes)
    refresh: () => {
      const domain = getDomainContext();
      const tenant = getTenantContext();
      setDomainContext(domain);
      setTenantContext(tenant);
    }
  };

  if (loading) {
    return (
      <div className="domain-loading">
        <div className="loading-spinner"></div>
        <p>Detecting domain context...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="domain-error">
        <h2>Domain Detection Error</h2>
        <p>{error}</p>
        <button onClick={() => window.location.reload()}>
          Retry
        </button>
      </div>
    );
  }

  return (
    <DomainContext.Provider value={value}>
      {children}
    </DomainContext.Provider>
  );
};

export const useDomain = () => {
  const context = useContext(DomainContext);
  if (!context) {
    throw new Error('useDomain must be used within a DomainProvider');
  }
  return context;
};

export default DomainContext;
