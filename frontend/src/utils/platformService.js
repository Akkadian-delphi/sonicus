/**
 * Platform service for B2C Therapeutic Sound Healing Platform  
 * Pure B2C model - no organization management needed
 */

/**
 * Get registration path for B2C customers
 * @returns {string} registration path
 */
export const getRegistrationPath = () => '/register';

/**
 * Get registration button text for B2C customers
 * @returns {string} button text  
 */
export const getRegistrationText = () => 'Get Started';

/**
 * Get platform mode - always B2C
 * @returns {string} platform mode
 */
export const getPlatformMode = () => 'b2c';

// Legacy compatibility exports (deprecated)
export const hasOrganizations = async () => false;
export const clearCache = () => {};
