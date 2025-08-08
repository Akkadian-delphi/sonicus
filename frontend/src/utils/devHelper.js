/**
 * Development helper utilities
 * Only available in development mode
 */

import { clearCache } from './platformService';

const devHelper = {
  // Clear platform service cache
  clearPlatformCache() {
    clearCache();
    console.log('✅ Platform service cache cleared');
  },

  // Test platform service endpoints
  async testPlatformService() {
    const { hasOrganizations, getPlatformMode, getRegistrationPath, getRegistrationText } = 
      await import('./platformService');
    
    console.group('🧪 Platform Service Test');
    
    try {
      const hasOrgs = await hasOrganizations();
      const mode = await getPlatformMode();
      const regPath = await getRegistrationPath();
      const regText = await getRegistrationText();
      
      console.log('Has Organizations:', hasOrgs);
      console.log('Platform Mode:', mode);
      console.log('Registration Path:', regPath);
      console.log('Registration Text:', regText);
      
      console.log('✅ Platform service test completed successfully');
    } catch (error) {
      console.error('❌ Platform service test failed:', error);
    } finally {
      console.groupEnd();
    }
  },

  // Test backend connectivity
  async testBackendConnection() {
    console.group('🔗 Backend Connection Test');
    
    try {
      // Temporarily disabled - endpoint doesn't exist yet
      // const axios = (await import('./axios')).default;
      // const response = await axios.get('/public/platform/organization-count');
      console.log('✅ Backend connection test skipped (endpoint not implemented)');
      // console.log('Organization count:', response.data.count);
    } catch (error) {
      console.error('❌ Backend connection failed:', error);
      if (error.response) {
        console.error('Status:', error.response.status);
        console.error('Data:', error.response.data);
      } else if (error.request) {
        console.error('No response received. Is the backend running?');
      } else {
        console.error('Request setup error:', error.message);
      }
    } finally {
      console.groupEnd();
    }
  },

  // Show current cache status
  showCacheStatus() {
    if (window.platformServiceCache) {
      console.log('📊 Platform Service Cache Status:', window.platformServiceCache);
    } else {
      console.log('No cache status available');
    }
  }
};

// Only expose in development mode
if (process.env.NODE_ENV === 'development') {
  window.devHelper = devHelper;
  console.log('🛠️ Development helper available at window.devHelper');
  console.log('Commands: clearPlatformCache(), testPlatformService(), testBackendConnection(), showCacheStatus()');
}

export default devHelper;
