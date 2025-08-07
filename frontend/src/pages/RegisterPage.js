import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "../utils/axios";

function RegisterPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [businessType, setBusinessType] = useState("");
  const [country, setCountry] = useState("");
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  // Available Countries list (EU + Major English-speaking markets)
  const availableCountries = [
    // EU Countries
    { code: "AT", name: "Austria" },
    { code: "BE", name: "Belgium" },
    { code: "BG", name: "Bulgaria" },
    { code: "HR", name: "Croatia" },
    { code: "CY", name: "Cyprus" },
    { code: "CZ", name: "Czech Republic" },
    { code: "DK", name: "Denmark" },
    { code: "EE", name: "Estonia" },
    { code: "FI", name: "Finland" },
    { code: "FR", name: "France" },
    { code: "DE", name: "Germany" },
    { code: "GR", name: "Greece" },
    { code: "HU", name: "Hungary" },
    { code: "IE", name: "Ireland" },
    { code: "IT", name: "Italy" },
    { code: "LV", name: "Latvia" },
    { code: "LT", name: "Lithuania" },
    { code: "LU", name: "Luxembourg" },
    { code: "MT", name: "Malta" },
    { code: "NL", name: "Netherlands" },
    { code: "PL", name: "Poland" },
    { code: "PT", name: "Portugal" },
    { code: "RO", name: "Romania" },
    { code: "SK", name: "Slovakia" },
    { code: "SI", name: "Slovenia" },
    { code: "ES", name: "Spain" },
    { code: "SE", name: "Sweden" },
    // Additional Markets
    { code: "GB", name: "United Kingdom" },
    { code: "US", name: "United States" },
    { code: "CA", name: "Canada" },
    { code: "BR", name: "Brazil" }
  ];

  // Business types for B2B2C therapeutic sound platform
  const businessTypes = [
    "Healthcare & Medical",
    "Wellness & Spa",
    "Corporate Wellness",
    "Educational Institution",
    "Fitness & Recreation",
    "Mental Health Services",
    "Rehabilitation Center",
    "Hotel & Hospitality",
    "Therapy Practice",
    "Senior Care Facility",
    "Other"
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    
    // Validate required fields for B2B2C organization registration
    if (!companyName.trim()) {
      setError("Company name is required for business registration");
      setLoading(false);
      return;
    }
    
    if (!businessType) {
      setError("Please select your business type");
      setLoading(false);
      return;
    }
    
    if (!country) {
      setError("Please select your country");
      setLoading(false);
      return;
    }
    
    try {
      const response = await axios.post("/users", {
        email,
        password,
        company_name: companyName,
        business_type: businessType,
        country: country
      });
      
      if (response.data) {
        setSuccess(true);
        setTimeout(() => {
          navigate("/login");
        }, 2000);
      }
    } catch (err) {
      console.error('Organization registration error:', err.response || err);
      
      if (err.response?.status === 400 && err.response?.data?.detail === "Email already registered") {
        setError("An account with this email already exists. Please try logging in instead.");
      } else if (err.response?.status === 400 && err.response?.data?.detail?.includes("Company name")) {
        setError("Company name is required for business registration.");
      } else if (err.response?.status === 400 && err.response?.data?.detail?.includes("Business type")) {
        setError("Please select your business type.");
      } else if (err.response?.status === 400 && err.response?.data?.detail?.includes("Country")) {
        setError("Please select your country.");
      } else if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else if (err.message) {
        setError(`Network error: ${err.message}`);
      } else {
        setError("Organization registration failed. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="form-container">
      <h2 className="form-title">Register Your Organization</h2>
      <p style={{
        textAlign: 'center', 
        color: '#666', 
        fontSize: '14px', 
        marginBottom: '25px',
        lineHeight: '1.5'
      }}>
        Create your business account and become the administrator of your organization's therapeutic sound healing platform
      </p>
      {success && (
        <div className="success-message">
          Organization registered successfully! You are now the Business Administrator for {companyName}. Redirecting to login...
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
          <label className="form-label">Company Name *</label>
          <input
            type="text"
            className="form-input"
            value={companyName}
            onChange={(e) => setCompanyName(e.target.value)}
            required
            disabled={loading}
            placeholder="Enter your company or organization name"
          />
        </div>
        
        <div className="form-group">
          <label className="form-label">Business Type *</label>
          <select
            className="form-input"
            value={businessType}
            onChange={(e) => setBusinessType(e.target.value)}
            required
            disabled={loading}
            style={{
              appearance: 'none',
              backgroundImage: `url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6,9 12,15 18,9'%3e%3c/polyline%3e%3c/svg%3e")`,
              backgroundRepeat: 'no-repeat',
              backgroundPosition: 'right 1rem center',
              backgroundSize: '1em',
              paddingRight: '2.5rem'
            }}
          >
            <option value="">Select your business type</option>
            {businessTypes.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">Country *</label>
          <select
            className="form-input"
            value={country}
            onChange={(e) => setCountry(e.target.value)}
            required
            disabled={loading}
            style={{
              appearance: 'none',
              backgroundImage: `url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6,9 12,15 18,9'%3e%3c/polyline%3e%3c/svg%3e")`,
              backgroundRepeat: 'no-repeat',
              backgroundPosition: 'right 1rem center',
              backgroundSize: '1em',
              paddingRight: '2.5rem'
            }}
          >
            <option value="">Select your country</option>
            {availableCountries.map((countryOption) => (
              <option key={countryOption.code} value={countryOption.code}>
                {countryOption.name}
              </option>
            ))}
          </select>
          <small style={{color: '#666', fontSize: '12px', marginTop: '5px', display: 'block'}}>
            Available in EU countries plus UK, US, Canada, and Brazil
          </small>
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
            placeholder="Enter your business email"
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
          {loading ? 'Setting Up Organization...' : 'Create Organization'}
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

export default RegisterPage;
