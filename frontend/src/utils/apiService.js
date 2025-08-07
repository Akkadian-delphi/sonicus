/**
 * Sonicus API Service - Complete integration with B2B2C backend
 * Handles all API calls for Super Admin and Business Admin functionality
 */

import axios from './axios';

// =================== AUTHENTICATION ===================

/**
 * Get current authenticated user
 */
export const getCurrentUser = async () => {
  try {
    const response = await axios.get('/auth/me');
    return response.data;
  } catch (error) {
    console.error('Get current user error:', error);
    throw error;
  }
};

// =================== SUPER ADMIN APIs ===================

/**
 * Get platform-wide statistics
 */
export const getPlatformStats = async () => {
  try {
    const response = await axios.get('/super-admin/platform-stats');
    return response.data;
  } catch (error) {
    console.error('Get platform stats error:', error);
    throw error;
  }
};

/**
 * Get all organizations with filtering and pagination
 */
export const getOrganizations = async (params = {}) => {
  try {
    const queryParams = new URLSearchParams();
    
    // Add pagination
    if (params.skip) queryParams.append('skip', params.skip);
    if (params.limit) queryParams.append('limit', params.limit);
    
    // Add filters
    if (params.status_filter) queryParams.append('status_filter', params.status_filter);
    if (params.tier) queryParams.append('tier', params.tier);
    if (params.search) queryParams.append('search', params.search);
    
    const response = await axios.get(`/super-admin/organizations?${queryParams}`);
    return response.data;
  } catch (error) {
    console.error('Get organizations error:', error);
    throw error;
  }
};

/**
 * Get a specific organization by ID
 */
export const getOrganization = async (organizationId) => {
  try {
    const response = await axios.get(`/super-admin/organizations/${organizationId}`);
    return response.data;
  } catch (error) {
    console.error('Get organization error:', error);
    throw error;
  }
};

/**
 * Create a new organization
 */
export const createOrganization = async (organizationData) => {
  try {
    const response = await axios.post('/super-admin/organizations', organizationData);
    return response.data;
  } catch (error) {
    console.error('Create organization error:', error);
    throw error;
  }
};

/**
 * Update an organization
 */
export const updateOrganization = async (organizationId, updateData) => {
  try {
    const response = await axios.put(`/super-admin/organizations/${organizationId}`, updateData);
    return response.data;
  } catch (error) {
    console.error('Update organization error:', error);
    throw error;
  }
};

/**
 * Delete an organization
 */
export const deleteOrganization = async (organizationId) => {
  try {
    const response = await axios.delete(`/super-admin/organizations/${organizationId}`);
    return response.data;
  } catch (error) {
    console.error('Delete organization error:', error);
    throw error;
  }
};

/**
 * Get organization health check
 */
export const getOrganizationHealth = async (organizationId) => {
  try {
    const response = await axios.get(`/super-admin/organizations/${organizationId}/health`);
    return response.data;
  } catch (error) {
    console.error('Get organization health error:', error);
    throw error;
  }
};

// =================== BUSINESS ADMIN APIs ===================

/**
 * Get organization dashboard analytics
 */
export const getOrganizationAnalytics = async () => {
  try {
    const response = await axios.get('/business-admin/analytics');
    return response.data;
  } catch (error) {
    console.error('Get organization analytics error:', error);
    throw error;
  }
};

/**
 * Get organization customers
 */
export const getOrganizationCustomers = async (params = {}) => {
  try {
    const queryParams = new URLSearchParams();
    if (params.skip) queryParams.append('skip', params.skip);
    if (params.limit) queryParams.append('limit', params.limit);
    if (params.search) queryParams.append('search', params.search);
    
    const response = await axios.get(`/business-admin/customers?${queryParams}`);
    return response.data;
  } catch (error) {
    console.error('Get organization customers error:', error);
    throw error;
  }
};

/**
 * Get wellness packages for organization
 */
export const getWellnessPackages = async () => {
  try {
    const response = await axios.get('/business-admin/packages');
    return response.data;
  } catch (error) {
    console.error('Get wellness packages error:', error);
    throw error;
  }
};

/**
 * Get user engagement analytics
 */
export const getUserEngagementAnalytics = async (timeframe = '30d') => {
  try {
    const response = await axios.get(`/business-admin/analytics/engagement?timeframe=${timeframe}`);
    return response.data;
  } catch (error) {
    console.error('Get user engagement analytics error:', error);
    throw error;
  }
};

// =================== GENERAL APIs ===================

/**
 * Get therapeutic sounds with organization context
 */
export const getTherapeuticSounds = async (params = {}) => {
  try {
    const queryParams = new URLSearchParams();
    if (params.skip) queryParams.append('skip', params.skip);
    if (params.limit) queryParams.append('limit', params.limit);
    if (params.category) queryParams.append('category', params.category);
    if (params.q) queryParams.append('q', params.q);
    
    const response = await axios.get(`/sounds?${queryParams}`);
    return response.data;
  } catch (error) {
    console.error('Get therapeutic sounds error:', error);
    throw error;
  }
};

/**
 * Get sound categories
 */
export const getSoundCategories = async () => {
  try {
    const response = await axios.get('/sounds/categories');
    return response.data;
  } catch (error) {
    console.error('Get sound categories error:', error);
    throw error;
  }
};

// =================== ERROR HANDLING UTILITIES ===================

/**
 * Extract error message from API response
 */
export const getErrorMessage = (error) => {
  if (error.response?.data?.detail) {
    return error.response.data.detail;
  }
  if (error.response?.data?.message) {
    return error.response.data.message;
  }
  if (error.message) {
    return error.message;
  }
  return 'An unexpected error occurred';
};

/**
 * Check if error is authentication related
 */
export const isAuthError = (error) => {
  return error.response?.status === 401 || error.response?.status === 403;
};

// =================== BUSINESS ADMIN ADDITIONAL APIs ===================

/**
 * Get organization details by ID
 */
export const getOrganizationDetails = async (orgId) => {
  try {
    // Use the actual backend route - business admin gets their own organization
    const response = await axios.get(`/business-admin/organization`);
    return response.data;
  } catch (error) {
    console.error('Get organization details error:', error);
    throw error;
  }
};

/**
 * Get organization statistics
 */
export const getOrganizationStats = async (orgId) => {
  try {
    // Use the actual backend route for business admin dashboard stats
    const response = await axios.get(`/business-admin/dashboard/stats`);
    return response.data;
  } catch (error) {
    console.error('Get organization stats error:', error);
    throw error;
  }
};

/**
 * Get wellness analytics
 */
export const getWellnessAnalytics = async (orgId) => {
  try {
    // Use the actual backend route for business admin analytics
    const response = await axios.get(`/business-admin/analytics/summary`);
    return response.data;
  } catch (error) {
    console.error('Get wellness analytics error:', error);
    throw error;
  }
};

/**
 * Get organization packages
 */
export const getOrganizationPackages = async (orgId) => {
  try {
    // Use the actual backend route for business admin packages
    const response = await axios.get(`/business-admin/packages`);
    return response.data;
  } catch (error) {
    console.error('Get organization packages error:', error);
    throw error;
  }
};

/**
 * Update customer information
 */
export const updateCustomer = async (customerId, data) => {
  try {
    const response = await axios.put(`/business-admin/customer/${customerId}`, data);
    return response.data;
  } catch (error) {
    console.error('Update customer error:', error);
    throw error;
  }
};

/**
 * Assign package to customer
 */
export const assignPackageToCustomer = async (customerId, packageId) => {
  try {
    const response = await axios.post(`/business-admin/customer/${customerId}/assign-package`, {
      package_id: packageId
    });
    return response.data;
  } catch (error) {
    console.error('Assign package to customer error:', error);
    throw error;
  }
};

/**
 * Remove package from customer
 */
export const removePackageFromCustomer = async (customerId, packageId) => {
  try {
    const response = await axios.delete(`/business-admin/customer/${customerId}/remove-package/${packageId}`);
    return response.data;
  } catch (error) {
    console.error('Remove package from customer error:', error);
    throw error;
  }
};

// =================== DATA TRANSFORMATION UTILITIES ===================

/**
 * Transform backend organization data for frontend display
 */
export const transformOrganizationData = (org) => {
  return {
    id: org.id,
    name: org.name,
    displayName: org.display_name || org.name,
    domain: org.domain,
    status: org.subscription_status,
    plan: org.subscription_tier,
    users: org.current_user_count || 0,
    maxUsers: org.max_users,
    contactEmail: org.primary_contact_email,
    trialEndDate: org.trial_end_date,
    createdAt: org.created_at,
    updatedAt: org.updated_at,
    // Calculate MRR based on subscription tier (simplified)
    mrr: calculateMRR(org.subscription_tier, org.current_user_count || 0)
  };
};

/**
 * Calculate Monthly Recurring Revenue based on tier and user count
 */
const calculateMRR = (tier, userCount) => {
  const tierPricing = {
    'BASIC': 10,      // $10 per user per month
    'PROFESSIONAL': 25, // $25 per user per month  
    'ENTERPRISE': 50   // $50 per user per month
  };
  
  return (tierPricing[tier] || 0) * userCount;
};

/**
 * Transform platform stats for dashboard display
 */
export const transformPlatformStats = (stats) => {
  const orgsByStatus = stats.organizations_by_status || {};
  
  return {
    totalOrganizations: stats.total_organizations || 0,
    totalUsers: stats.total_users_across_platform || 0,
    totalActiveUsers: stats.total_active_users || 0,
    activeOrganizations: orgsByStatus.ACTIVE || 0,
    trialOrganizations: orgsByStatus.TRIAL || 0,
    cancelledOrganizations: orgsByStatus.CANCELLED || 0,
    systemHealth: stats.platform_health?.system_status || 'Unknown',
    platformUptime: 99.5, // This would come from monitoring service
    // Calculate total MRR - this would need more detailed data in real implementation
    monthlyRecurringRevenue: 0 // Placeholder - needs billing integration
  };
};

// API service object with all endpoints
const apiService = {
  // Auth
  getCurrentUser,
  
  // Super Admin
  getPlatformStats,
  getOrganizations,
  getOrganization,
  createOrganization,
  updateOrganization,
  deleteOrganization,
  getOrganizationHealth,
  
  // Business Admin
  getOrganizationAnalytics,
  getOrganizationCustomers,
  getWellnessPackages,
  getUserEngagementAnalytics,
  getOrganizationDetails,
  getOrganizationStats,
  getWellnessAnalytics,
  getOrganizationPackages,
  updateCustomer,
  assignPackageToCustomer,
  removePackageFromCustomer,
  
  // General
  getTherapeuticSounds,
  getSoundCategories,
  
  // Utilities
  getErrorMessage,
  isAuthError,
  transformOrganizationData,
  transformPlatformStats
};

export default apiService;
