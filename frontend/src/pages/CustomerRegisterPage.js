import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "../utils/axios";
import "../styles/RegisterPage.css";

function CustomerRegisterPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    
    // Validate required fields for individual customer registration
    if (!name.trim()) {
      setError("Name is required");
      setLoading(false);
      return;
    }
    
    try {
      const response = await axios.post("/customers/register", {
        email,
        password,
        name
      });
      
      if (response.data) {
        setSuccess(true);
        setTimeout(() => {
          navigate("/login");
        }, 2000);
      }
    } catch (err) {
      console.error('Customer registration error:', err.response || err);
      
      if (err.response?.status === 400 && err.response?.data?.detail === "Email already registered") {
        setError("An account with this email already exists. Please try logging in instead.");
      } else if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else if (err.message) {
        setError(`Network error: ${err.message}`);
      } else {
        setError("Registration failed. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="form-container">
      <h2 className="form-title">Get Started with Sonicus</h2>
      <p style={{
        textAlign: 'center', 
        color: '#666', 
        fontSize: '14px', 
        marginBottom: '25px',
        lineHeight: '1.5'
      }}>
        Create your personal account and begin your therapeutic sound healing journey
      </p>
      {success && (
        <div className="success-message">
          Account created successfully! Welcome to Sonicus, {name}. Redirecting to login...
        </div>
      )}
      {error && (
        <div className="error" style={{
          padding: '10px',
          marginBottom: '15px',
          backgroundColor: '#f8d7da',
          color: '#721c24',
          border: '1px solid #f1b0b7',
          borderRadius: '5px'
        }}>
          {error}
        </div>
      )}
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="form-label">Full Name *</label>
          <input
            type="text"
            className="form-input"
            value={name}
            onChange={(e) => setName(e.target.value)}
            autoComplete="name"
            required
            disabled={loading}
            placeholder="Enter your full name"
          />
        </div>

        <div className="form-group">
          <label className="form-label">Email *</label>
          <input
            type="email"
            className="form-input"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
            required
            disabled={loading}
            placeholder="Enter your email address"
          />
        </div>
        
        <div className="form-group">
          <label className="form-label">Password *</label>
          <input
            type="password"
            className="form-input"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="new-password"
            required
            minLength="8"
            disabled={loading}
            placeholder="Create a secure password"
          />
          <small style={{color: '#666', fontSize: '12px'}}>
            Password must be at least 8 characters long
          </small>
        </div>
        <button 
          type="submit" 
          className="form-button"
          disabled={loading}
          style={{
            opacity: loading ? 0.6 : 1,
            cursor: loading ? 'not-allowed' : 'pointer'
          }}
        >
          {loading ? 'Creating Account...' : 'Create Account'}
        </button>
        
        <div style={{
          marginTop: '15px',
          padding: '12px',
          backgroundColor: '#f8f9fa',
          borderRadius: '6px',
          fontSize: '12px',
          color: '#666',
          lineHeight: '1.4'
        }}>
          By creating an account, you agree to our Terms of Service and Privacy Policy. 
          We process your data in accordance with GDPR regulations.
        </div>
      </form>
      <div style={{marginTop: '20px', textAlign: 'center'}}>
        <p>Already have an account? <a href="/login" style={{color: '#007bff'}}>Login here</a></p>
      </div>
    </div>
  );
}

export default CustomerRegisterPage;
