/**
 * Domain Detection Utilities for Multi-Tenant Architecture
 * Phase 2.1 implementation from NEXT.md
 * 
 * Handles:
 * - Subdomain extraction from current URL
 * - Domain type detection (main domain vs tenant subdomain)
 * - Organization context determination
 */

/**
 * Extract subdomain from current window location
 * @returns {Object} Domain context information
 */
export const getDomainContext = () => {
  const hostname = window.location.hostname.toLowerCase();
  const protocol = window.location.protocol;
  const port = window.location.port;
  
  // Development environment detection
  const isDevelopment = hostname.includes('localhost') || hostname.startsWith('127.0.0.1') || hostname.startsWith('192.168.');
  
  // Base domain configuration
  const baseDomain = 'sonicus.eu';
  const devBaseDomain = 'sonicus.local'; // For local development
  
  const context = {
    hostname,
    protocol,
    port,
    isDevelopment,
    isMainDomain: false,
    isSubdomain: false,
    subdomain: null,
    organizationIdentifier: null,
    domainType: 'unknown',
    fullDomain: hostname,
    baseDomain: isDevelopment ? devBaseDomain : baseDomain
  };
  
  // Development environment handling
  if (isDevelopment) {
    // For development, we can simulate subdomains with port or query parameters
    const urlParams = new URLSearchParams(window.location.search);
    const subdomainParam = urlParams.get('subdomain') || urlParams.get('org');
    
    if (subdomainParam) {
      context.isSubdomain = true;
      context.subdomain = subdomainParam.toLowerCase();
      context.organizationIdentifier = subdomainParam.toLowerCase();
      context.domainType = 'b2b2c_dev';
    } else {
      context.isMainDomain = true;
      context.domainType = 'b2c_dev';
    }
    
    return context;
  }
  
  // Production environment - subdomain detection
  if (hostname.endsWith(`.${baseDomain}`)) {
    // Extract subdomain from hostname
    const subdomainMatch = hostname.match(/^([a-zA-Z0-9-]+)\.sonicus\.eu$/);
    
    if (subdomainMatch) {
      const extractedSubdomain = subdomainMatch[1];
      
      // Check if it's an excluded/system subdomain
      const excludedSubdomains = ['www', 'api', 'admin', 'app', 'dashboard', 'static', 'cdn', 'assets'];
      
      if (excludedSubdomains.includes(extractedSubdomain)) {
        // System subdomain - treat as main domain
        context.isMainDomain = true;
        context.domainType = 'b2c_system';
        context.subdomain = extractedSubdomain;
      } else {
        // Organization subdomain
        context.isSubdomain = true;
        context.subdomain = extractedSubdomain;
        context.organizationIdentifier = extractedSubdomain;
        context.domainType = 'b2b2c';
      }
    } else {
      // Malformed subdomain or base domain
      context.isMainDomain = true;
      context.domainType = 'b2c';
    }
  } else if (hostname === baseDomain) {
    // Main domain
    context.isMainDomain = true;
    context.domainType = 'b2c';
  } else {
    // Custom domain (future feature)
    context.isSubdomain = true;
    context.domainType = 'b2b2c_custom';
    context.organizationIdentifier = hostname;
  }
  
  return context;
};

/**
 * Check if current domain is main domain (sonicus.eu)
 * @returns {boolean}
 */
export const isMainDomain = () => {
  const context = getDomainContext();
  return context.isMainDomain;
};

/**
 * Check if current domain is a tenant subdomain
 * @returns {boolean}
 */
export const isSubdomain = () => {
  const context = getDomainContext();
  return context.isSubdomain;
};

/**
 * Get current subdomain if exists
 * @returns {string|null}
 */
export const getCurrentSubdomain = () => {
  const context = getDomainContext();
  return context.subdomain;
};

/**
 * Get organization identifier from current domain
 * @returns {string|null}
 */
export const getOrganizationIdentifier = () => {
  const context = getDomainContext();
  return context.organizationIdentifier;
};

/**
 * Get full tenant context for API calls
 * @returns {Object}
 */
export const getTenantContext = () => {
  const context = getDomainContext();
  
  return {
    mode: context.isSubdomain ? 'b2b2c' : 'b2c',
    identifier: context.organizationIdentifier,
    subdomain: context.subdomain,
    domainType: context.domainType,
    isDevelopment: context.isDevelopment,
    fullDomain: context.fullDomain,
    baseDomain: context.baseDomain
  };
};

/**
 * Build API URL with proper tenant headers
 * @param {string} endpoint - API endpoint path
 * @param {Object} options - Additional options
 * @returns {Object} Fetch options with headers
 */
export const buildTenantApiRequest = (endpoint, options = {}) => {
  const context = getDomainContext();
  const baseUrl = context.isDevelopment 
    ? 'http://127.0.0.1:18100'
    : `${context.protocol}//${context.fullDomain}`;
  
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers
  };
  
  // Add tenant identifier header for B2B2C requests
  if (context.isSubdomain && context.organizationIdentifier) {
    headers['X-Tenant-ID'] = context.organizationIdentifier;
  }
  
  return {
    url: `${baseUrl}${endpoint}`,
    options: {
      ...options,
      headers
    }
  };
};

/**
 * Redirect to appropriate domain
 * @param {string} targetDomain - Target domain/subdomain
 * @param {string} path - Path to redirect to
 */
export const redirectToDomain = (targetDomain, path = '/') => {
  const context = getDomainContext();
  
  if (context.isDevelopment) {
    // In development, use query parameters for subdomain simulation
    if (targetDomain === 'main' || targetDomain === context.baseDomain) {
      window.location.href = `${context.protocol}//localhost:3000${path}`;
    } else {
      window.location.href = `${context.protocol}//localhost:3000${path}?subdomain=${targetDomain}`;
    }
  } else {
    // Production redirect
    if (targetDomain === 'main') {
      window.location.href = `${context.protocol}//${context.baseDomain}${path}`;
    } else {
      window.location.href = `${context.protocol}//${targetDomain}.${context.baseDomain}${path}`;
    }
  }
};

/**
 * Generate subdomain suggestions based on organization name
 * @param {string} organizationName - Organization name
 * @returns {string[]} Array of subdomain suggestions
 */
export const generateSubdomainSuggestions = (organizationName) => {
  if (!organizationName) return [];
  
  // Clean organization name for subdomain use
  const cleanName = organizationName
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, '') // Remove special characters
    .replace(/\s+/g, '-') // Replace spaces with hyphens
    .replace(/-+/g, '-') // Remove multiple consecutive hyphens
    .replace(/^-+|-+$/g, ''); // Remove leading/trailing hyphens
  
  if (!cleanName) return [];
  
  const suggestions = [cleanName];
  
  // Add variations if base name is short enough
  if (cleanName.length <= 10) {
    suggestions.push(`${cleanName}-corp`);
    suggestions.push(`${cleanName}-inc`);
    suggestions.push(`${cleanName}-co`);
  }
  
  // Add abbreviated versions for longer names
  if (cleanName.length > 6) {
    // Take first few characters
    const abbreviated = cleanName.substring(0, 6);
    suggestions.push(abbreviated);
    
    // Remove vowels for shorter version
    const consonants = cleanName.replace(/[aeiou]/g, '');
    if (consonants.length >= 3 && consonants.length <= 8) {
      suggestions.push(consonants);
    }
  }
  
  // Add numeric suffixes as fallback
  for (let i = 1; i <= 3; i++) {
    suggestions.push(`${cleanName}${i}`);
  }
  
  // Return unique suggestions
  return [...new Set(suggestions)];
};

/**
 * Validate subdomain format
 * @param {string} subdomain - Subdomain to validate
 * @returns {Object} Validation result
 */
export const validateSubdomain = (subdomain) => {
  const result = {
    isValid: false,
    errors: [],
    suggestions: []
  };
  
  if (!subdomain) {
    result.errors.push('Subdomain is required');
    return result;
  }
  
  // Length validation
  if (subdomain.length < 3) {
    result.errors.push('Subdomain must be at least 3 characters long');
  }
  
  if (subdomain.length > 63) {
    result.errors.push('Subdomain must be 63 characters or less');
  }
  
  // Format validation
  const formatRegex = /^[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]$/;
  if (subdomain.length === 1) {
    if (!/^[a-zA-Z0-9]$/.test(subdomain)) {
      result.errors.push('Single character subdomains must be alphanumeric');
    }
  } else if (!formatRegex.test(subdomain)) {
    result.errors.push('Subdomain must start and end with a letter or number, and contain only letters, numbers, and hyphens');
  }
  
  // Reserved subdomain validation
  const reserved = ['www', 'api', 'admin', 'app', 'dashboard', 'static', 'cdn', 'assets', 'mail', 'ftp', 'blog', 'support', 'docs', 'help', 'status'];
  if (reserved.includes(subdomain.toLowerCase())) {
    result.errors.push(`'${subdomain}' is a reserved subdomain`);
    result.suggestions = [`${subdomain}-app`, `${subdomain}-co`, `my-${subdomain}`];
  }
  
  result.isValid = result.errors.length === 0;
  return result;
};

/**
 * Debug function to log current domain context
 */
export const logDomainContext = () => {
  const context = getDomainContext();
  console.group('🌐 Domain Detection Context');
  console.log('Full Context:', context);
  console.log('Is Main Domain:', context.isMainDomain);
  console.log('Is Subdomain:', context.isSubdomain);
  console.log('Organization ID:', context.organizationIdentifier);
  console.log('Domain Type:', context.domainType);
  console.groupEnd();
  
  return context;
};

export default {
  getDomainContext,
  isMainDomain,
  isSubdomain,
  getCurrentSubdomain,
  getOrganizationIdentifier,
  getTenantContext,
  buildTenantApiRequest,
  redirectToDomain,
  generateSubdomainSuggestions,
  validateSubdomain,
  logDomainContext
};
