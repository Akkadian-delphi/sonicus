import React, { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { getDashboardRoute } from "../utils/roleBasedRedirect";
import "../styles/LoginPage.css";

function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [loginMethod, setLoginMethod] = useState("password"); // "password" or "oidc"
  const { loginWithJWT, loginWithOIDC, isAuthenticated, loading, user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated && !loading && user) {
      const returnTo = location.state?.returnTo || getDashboardRoute(user);
      navigate(returnTo, { replace: true });
    }
  }, [isAuthenticated, loading, user, navigate, location.state]);

  const handlePasswordLogin = async (e) => {
    e.preventDefault();
    setError("");
    setIsSubmitting(true);
    
    try {
      await loginWithJWT(email, password);
      // Navigation will be handled by the useEffect above
    } catch (err) {
      console.error('Login error:', err);
      // Better error handling
      if (err.response?.status === 401) {
        setError("Invalid email or password");
      } else if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else if (err.message) {
        setError(`Login error: ${err.message}`);
      } else {
        setError("Invalid email or password");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOIDCLogin = async () => {
    setError("");
    setIsSubmitting(true);
    
    try {
      const returnTo = location.state?.returnTo || getDashboardRoute(user);
      await loginWithOIDC(returnTo);
      // loginWithOIDC will redirect to Authentik, so no navigation needed here
    } catch (err) {
      console.error('OIDC login error:', err);
      setError(err.message || "OIDC login failed. Please try again.");
      setIsSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="form-container">
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <div className="loading-spinner" style={{ 
            border: '4px solid #f3f3f3',
            borderTop: '4px solid #007bff',
            borderRadius: '50%',
            width: '40px',
            height: '40px',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 20px'
          }}></div>
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="form-container">
      <h2 className="form-title">Sign In</h2>
      {error && <div className="error">{error}</div>}
      
      {/* Login Method Toggle */}
      <div className="login-methods" style={{ marginBottom: '20px', textAlign: 'center' }}>
        <button
          type="button"
          onClick={() => setLoginMethod("oidc")}
          className={`method-button ${loginMethod === "oidc" ? "active" : ""}`}
          style={{
            padding: '10px 20px',
            margin: '5px',
            border: '2px solid #007bff',
            backgroundColor: loginMethod === "oidc" ? '#007bff' : 'white',
            color: loginMethod === "oidc" ? 'white' : '#007bff',
            borderRadius: '5px',
            cursor: 'pointer'
          }}
        >
          Single Sign-On (SSO)
        </button>
        <button
          type="button"
          onClick={() => setLoginMethod("password")}
          className={`method-button ${loginMethod === "password" ? "active" : ""}`}
          style={{
            padding: '10px 20px',
            margin: '5px',
            border: '2px solid #007bff',
            backgroundColor: loginMethod === "password" ? '#007bff' : 'white',
            color: loginMethod === "password" ? 'white' : '#007bff',
            borderRadius: '5px',
            cursor: 'pointer'
          }}
        >
          Email & Password
        </button>
      </div>

      {loginMethod === "oidc" ? (
        /* OIDC Login */
        <div style={{ textAlign: 'center', padding: '20px' }}>
          <p style={{ marginBottom: '20px', color: '#666' }}>
            Sign in securely with your organization credentials
          </p>
          <button
            onClick={handleOIDCLogin}
            disabled={isSubmitting}
            style={{
              padding: '12px 30px',
              fontSize: '16px',
              backgroundColor: isSubmitting ? '#6c757d' : '#28a745',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              cursor: isSubmitting ? 'not-allowed' : 'pointer',
              boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
              opacity: isSubmitting ? 0.6 : 1
            }}
          >
            {isSubmitting ? 'Redirecting to SSO...' : 'Continue with Single Sign-On'}
          </button>
        </div>
      ) : (
        /* Password Login */
        <form onSubmit={handlePasswordLogin}>
          <div className="form-group">
            <label className="form-label">Email</label>
            <input
              type="email"
              className="form-input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              required
              disabled={isSubmitting}
            />
          </div>
          <div className="form-group">
            <label className="form-label">Password</label>
            <input
              type="password"
              className="form-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
              disabled={isSubmitting}
            />
          </div>
          <button 
            type="submit" 
            className="form-button"
            disabled={isSubmitting}
            style={{ opacity: isSubmitting ? 0.6 : 1 }}
          >
            {isSubmitting ? 'Signing in...' : 'Login'}
          </button>
        </form>
      )}
      
      <div className="form-footer">
        <p>
          Forgot your password?{' '}
          <button 
            onClick={() => navigate('/forgot-password')}
            className="link-button"
            type="button"
          >
            Reset it here
          </button>
        </p>
        <p>
          Don't have an account?{' '}
          <button 
            onClick={() => navigate('/register')}
            className="link-button"
            type="button"
          >
            Sign up
          </button>
        </p>
      </div>
    </div>
  );
}

export default LoginPage;
