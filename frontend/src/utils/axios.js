import axios from "axios";

// Simple cache to reduce API calls for same endpoints
const cache = new Map();
const CACHE_DURATION = 30000; // 30 seconds

// Simple rate limiting cache to prevent API flooding  
const rateLimitCache = new Map();
const RATE_LIMIT_WINDOW = 2000; // 2 seconds
const MAX_REQUESTS_PER_WINDOW = 2; // Max 2 requests per 2 seconds per endpoint

const axiosInstance = axios.create({
  baseURL: 'http://localhost:18100/api/v1',
  timeout: 10000,
});

// Request interceptor to add authentication token and rate limiting
axiosInstance.interceptors.request.use(
  config => {
    // Rate limiting check for specific endpoints
    const endpoint = config.url;
    const now = Date.now();
    const cacheKey = endpoint;
    
    // Only apply rate limiting to platform detection endpoints
    if (endpoint && endpoint.includes('/platform/')) {
      // Get or initialize rate limit data for this endpoint
      if (!rateLimitCache.has(cacheKey)) {
        rateLimitCache.set(cacheKey, { requests: [], lastCleanup: now });
      }
      
      const rateLimitData = rateLimitCache.get(cacheKey);
      
      // Clean up old requests outside the time window
      rateLimitData.requests = rateLimitData.requests.filter(
        timestamp => now - timestamp < RATE_LIMIT_WINDOW
      );
      
      // Check if we've exceeded the rate limit
      if (rateLimitData.requests.length >= MAX_REQUESTS_PER_WINDOW) {
        console.warn(`Rate limit exceeded for endpoint: ${endpoint}. Max ${MAX_REQUESTS_PER_WINDOW} requests per ${RATE_LIMIT_WINDOW}ms`);
        return Promise.reject(new Error(`Rate limit exceeded for ${endpoint}`));
      }
      
      // Add current request timestamp
      rateLimitData.requests.push(now);
      rateLimitCache.set(cacheKey, rateLimitData);
    }

    // Get token from localStorage - using 'access_token' to match backend
    const token = localStorage.getItem('access_token') || localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// Response interceptor for global error handling
axiosInstance.interceptors.response.use(
  response => response,
  error => {
    // Handle authentication errors globally
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('access_token');
      localStorage.removeItem('authToken');
      // Only redirect if not already on login page
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    
    // Log API errors for debugging (but don't flood console)
    if (error.response?.status >= 500) {
      console.error(`API Error ${error.response.status}:`, error.config?.url);
    } else if (error.response?.status === 404 && error.config?.url?.includes('/platform/')) {
      console.warn(`Platform endpoint not found: ${error.config.url}. Check if backend is running.`);
    }
    
    return Promise.reject(error);
  }
);

// Periodic cleanup of rate limit cache to prevent memory leaks
setInterval(() => {
  const now = Date.now();
  for (const [key, data] of rateLimitCache.entries()) {
    // Remove entries older than 5 minutes
    if (now - data.lastCleanup > 5 * 60 * 1000) {
      rateLimitCache.delete(key);
    }
  }
  // Also clean up general cache
  for (const [key, data] of cache.entries()) {
    if (now - data.timestamp > CACHE_DURATION * 2) {
      cache.delete(key);
    }
  }
}, 60000); // Clean up every minute

export default axiosInstance;
