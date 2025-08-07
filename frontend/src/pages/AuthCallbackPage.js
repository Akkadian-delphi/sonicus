import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { getDashboardRoute } from '../utils/roleBasedRedirect';

const AuthCallbackPage = () => {
  const [status, setStatus] = useState('processing');
  const [error, setError] = useState(null);
  const navigate = useNavigate();
  const { handleAuthCallback } = useAuth();

  useEffect(() => {
    const processCallback = async () => {
      try {
        setStatus('processing');
        const result = await handleAuthCallback();
        setStatus('success');
        
        // Determine redirect destination
        const returnTo = sessionStorage.getItem('returnTo');
        sessionStorage.removeItem('returnTo');
        
        let redirectRoute;
        if (returnTo === 'dashboard') {
          // Use role-based dashboard routing
          redirectRoute = getDashboardRoute(result.user);
        } else {
          // Use stored return URL or default to role-based dashboard
          redirectRoute = returnTo || getDashboardRoute(result.user);
        }
        
        setTimeout(() => {
          navigate(redirectRoute, { replace: true });
        }, 1500);
        
      } catch (err) {
        console.error('Auth callback error:', err);
        setError(err.message || 'Authentication failed');
        setStatus('error');
        
        // Redirect to login after error
        setTimeout(() => {
          navigate('/login', { replace: true });
        }, 3000);
      }
    };

    processCallback();
  }, [handleAuthCallback, navigate]);

  if (status === 'processing') {
    return (
      <div style={{ 
        display: 'flex', 
        flexDirection: 'column',
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        fontFamily: 'Arial, sans-serif'
      }}>
        <div style={{
          width: '50px',
          height: '50px',
          border: '5px solid #f3f3f3',
          borderTop: '5px solid #3498db',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite',
          marginBottom: '20px'
        }} />
        <h2 style={{ color: '#333', marginBottom: '10px' }}>Completing Sign In...</h2>
        <p style={{ color: '#666', textAlign: 'center' }}>
          Please wait while we finish setting up your session.
        </p>
        <style>{`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  if (status === 'success') {
    return (
      <div style={{ 
        display: 'flex', 
        flexDirection: 'column',
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        fontFamily: 'Arial, sans-serif'
      }}>
        <div style={{
          width: '50px',
          height: '50px',
          backgroundColor: '#4CAF50',
          borderRadius: '50%',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          marginBottom: '20px',
          color: 'white',
          fontSize: '24px'
        }}>
          ✓
        </div>
        <h2 style={{ color: '#4CAF50', marginBottom: '10px' }}>Sign In Successful!</h2>
        <p style={{ color: '#666', textAlign: 'center' }}>
          Redirecting you to the application...
        </p>
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div style={{ 
        display: 'flex', 
        flexDirection: 'column',
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        fontFamily: 'Arial, sans-serif'
      }}>
        <div style={{
          width: '50px',
          height: '50px',
          backgroundColor: '#f44336',
          borderRadius: '50%',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          marginBottom: '20px',
          color: 'white',
          fontSize: '24px'
        }}>
          ✕
        </div>
        <h2 style={{ color: '#f44336', marginBottom: '10px' }}>Sign In Failed</h2>
        <p style={{ color: '#666', textAlign: 'center', marginBottom: '10px' }}>
          {error}
        </p>
        <p style={{ color: '#999', fontSize: '14px', textAlign: 'center' }}>
          You will be redirected to the login page shortly.
        </p>
      </div>
    );
  }

  return null;
};

export default AuthCallbackPage;
