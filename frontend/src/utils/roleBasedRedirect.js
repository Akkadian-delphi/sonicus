/**
 * Role-based dashboard redirect utility for B2C Model
 * Determines the appropriate dashboard route based on user role in B2C architecture
 */

/**
 * Get the appropriate dashboard route for a user based on their role
 * @param {Object} user - User object containing role information
 * @param {string} user.role - User role (super_admin, user)
 * @param {string} defaultRoute - Fallback route if role is not recognized (default: '/profile')
 * @returns {string} - The route path to redirect to
 */
export const getDashboardRoute = (user, defaultRoute = '/profile') => {
  if (!user || !user.role) {
    return defaultRoute;
  }

  const role = user.role.toLowerCase();

  // B2C Role-based routing logic
  switch (role) {
    case 'super_admin':
    case 'superadmin':
      return '/super-admin';
      
    case 'user':
    case 'customer':
    default:
      return '/profile';
  }
};

/**
 * Check if a user has admin privileges (super admin only in B2C model)
 * @param {Object} user - User object
 * @returns {boolean} - True if user has admin privileges
 */
export const hasAdminPrivileges = (user) => {
  if (!user || !user.role) {
    return false;
  }

  const role = user.role.toLowerCase();
  return ['super_admin', 'superadmin'].includes(role);
};

/**
 * Check if a user is a super admin
 * @param {Object} user - User object
 * @returns {boolean} - True if user is super admin
 */
export const isSuperAdmin = (user) => {
  if (!user || !user.role) {
    return false;
  }

  const role = user.role.toLowerCase();
  return ['super_admin', 'superadmin'].includes(role);
};

/**
 * Check if a user is a regular customer (B2C model)
 * @param {Object} user - User object
 * @returns {boolean} - True if user is a regular customer
 */
export const isCustomer = (user) => {
  if (!user || !user.role) {
    return false;
  }

  const role = user.role.toLowerCase();
  return ['user', 'customer'].includes(role);
};

/**
 * Get user-friendly role name for display
 * @param {string} role - Raw role string
 * @returns {string} - Formatted role name
 */
export const getDisplayRole = (role) => {
  if (!role) return 'Customer';
  
  const roleMap = {
    'super_admin': 'Super Admin',
    'superadmin': 'Super Admin',
    'user': 'Customer',
    'customer': 'Customer'
  };
  
  return roleMap[role.toLowerCase()] || 'Customer';
};
