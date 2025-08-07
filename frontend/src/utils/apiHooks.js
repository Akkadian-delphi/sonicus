/**
 * Custom React hooks for API state management
 * Provides loading, error, and data state for API calls
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { getErrorMessage, isAuthError } from './apiService';

/**
 * Generic hook for API calls with loading, error, and data state
 */
export const useApiCall = (apiFunction, dependencies = [], options = {}) => {
  const [data, setData] = useState(options.initialData || null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const execute = useCallback(async (...args) => {
    try {
      setLoading(true);
      setError(null);
      const result = await apiFunction(...args);
      setData(result);
      return result;
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      setError(errorMessage);
      
      // Handle auth errors
      if (isAuthError(err) && options.onAuthError) {
        options.onAuthError(err);
      }
      
      throw err;
    } finally {
      setLoading(false);
    }
  }, [apiFunction, options]);

  // Auto-execute on mount if autoExecute is enabled
  useEffect(() => {
    if (options.autoExecute !== false) {
      execute();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, dependencies);

  const refresh = useCallback(() => {
    execute();
  }, [execute]);

  return {
    data,
    loading,
    error,
    execute,
    refresh,
    setData,
    setError
  };
};

/**
 * Hook for paginated API calls
 */
export const usePaginatedApi = (apiFunction, options = {}) => {
  const [data, setData] = useState([]);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastExecutionTime, setLastExecutionTime] = useState(0);
  const executionRef = useRef(false);
  
  const pageSize = options.pageSize || 20;
  const minExecutionInterval = 2000; // Increased to 2 seconds

  const fetchPage = useCallback(async (page = 0, additionalParams = {}) => {
    const currentTime = Date.now();
    
    // Prevent concurrent executions and throttling
    if (executionRef.current || loading || (currentTime - lastExecutionTime < minExecutionInterval)) {
      console.log('API call prevented - concurrent execution or throttling');
      return;
    }
    
    executionRef.current = true;
    setLastExecutionTime(currentTime);
    
    try {
      setLoading(true);
      setError(null);
      
      const params = {
        skip: page * pageSize,
        limit: pageSize,
        ...additionalParams
      };
      
      const result = await apiFunction(params);
      
      if (result.organizations) {
        // Handle organization list response
        setData(result.organizations);
        setTotal(result.total);
      } else if (Array.isArray(result)) {
        // Handle direct array response
        setData(result);
        setTotal(result.length);
      } else {
        setData([]);
        setTotal(0);
      }
      
      setCurrentPage(page);
      return result;
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
      executionRef.current = false;
    }
  }, [apiFunction, pageSize, lastExecutionTime, loading, minExecutionInterval]);

  const nextPage = useCallback(() => {
    const next = currentPage + 1;
    if (next * pageSize < total) {
      fetchPage(next);
    }
  }, [currentPage, pageSize, total, fetchPage]);

  const prevPage = useCallback(() => {
    if (currentPage > 0) {
      fetchPage(currentPage - 1);
    }
  }, [currentPage, fetchPage]);

  const goToPage = useCallback((page) => {
    if (page >= 0 && page * pageSize < total) {
      fetchPage(page);
    }
  }, [pageSize, total, fetchPage]);

  // Initial load and dependency reload
  useEffect(() => {
    // Additional guard to prevent rapid consecutive calls
    if (options.autoExecute !== false && !loading && !executionRef.current) {
      const timeoutId = setTimeout(() => {
        if (!executionRef.current) {
          fetchPage(0);
        }
      }, 500); // Increased delay

      return () => clearTimeout(timeoutId);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fetchPage, options.autoExecute, ...(options.dependencies || [])]);

  return {
    data,
    total,
    currentPage,
    pageSize,
    loading,
    error,
    fetchPage,
    nextPage,
    prevPage,
    goToPage,
    refresh: () => fetchPage(currentPage),
    hasNext: (currentPage + 1) * pageSize < total,
    hasPrev: currentPage > 0,
    totalPages: Math.ceil(total / pageSize)
  };
};

/**
 * Hook for form submission with API calls
 */
export const useApiSubmit = (apiFunction, options = {}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const submit = useCallback(async (data) => {
    try {
      setLoading(true);
      setError(null);
      setSuccess(false);
      
      const result = await apiFunction(data);
      setSuccess(true);
      
      if (options.onSuccess) {
        options.onSuccess(result);
      }
      
      return result;
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      setError(errorMessage);
      
      if (options.onError) {
        options.onError(err);
      }
      
      throw err;
    } finally {
      setLoading(false);
    }
  }, [apiFunction, options]);

  const reset = useCallback(() => {
    setError(null);
    setSuccess(false);
  }, []);

  return {
    submit,
    loading,
    error,
    success,
    reset
  };
};

/**
 * Hook for real-time data that auto-refreshes
 */
export const useRealTimeApi = (apiFunction, refreshInterval = 30000, dependencies = []) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await apiFunction();
      setData(result);
      setLastUpdated(new Date());
      return result;
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [apiFunction]);

  // Initial load and setup refresh interval
  useEffect(() => {
    fetchData();
    
    const interval = setInterval(() => {
      fetchData();
    }, refreshInterval);

    return () => clearInterval(interval);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fetchData, refreshInterval, ...dependencies]);

  return {
    data,
    loading,
    error,
    lastUpdated,
    refresh: fetchData
  };
};

/**
 * Hook for managing multiple API calls in sequence or parallel
 */
export const useMultipleApiCalls = (apiCalls, options = {}) => {
  const [results, setResults] = useState({});
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const [completed, setCompleted] = useState(false);

  const executeAll = useCallback(async (parallel = true) => {
    try {
      setLoading(true);
      setErrors({});
      setCompleted(false);
      
      const newResults = {};
      const newErrors = {};

      if (parallel) {
        // Execute all API calls in parallel
        const promises = Object.entries(apiCalls).map(async ([key, apiCall]) => {
          try {
            const result = await apiCall();
            newResults[key] = result;
          } catch (err) {
            newErrors[key] = getErrorMessage(err);
            throw err;
          }
        });

        await Promise.allSettled(promises);
      } else {
        // Execute API calls in sequence
        for (const [key, apiCall] of Object.entries(apiCalls)) {
          try {
            const result = await apiCall();
            newResults[key] = result;
          } catch (err) {
            newErrors[key] = getErrorMessage(err);
            if (options.stopOnError) {
              break;
            }
          }
        }
      }

      setResults(newResults);
      setErrors(newErrors);
      setCompleted(true);
      
      return { results: newResults, errors: newErrors };
    } catch (err) {
      // Overall error handling
      console.error('Multiple API calls error:', err);
    } finally {
      setLoading(false);
    }
  }, [apiCalls, options]);

  return {
    results,
    errors,
    loading,
    completed,
    executeAll,
    hasErrors: Object.keys(errors).length > 0,
    successCount: Object.keys(results).length,
    errorCount: Object.keys(errors).length
  };
};
