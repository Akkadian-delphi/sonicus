/**
 * Subdomain Generator Component
 * Handles subdomain creation, validation, and availability checking
 */

import React, { useState, useEffect, useCallback } from 'react';
import { 
  generateSubdomainSuggestions, 
  validateSubdomain,
  buildTenantApiRequest 
} from '../../utils/domainDetection';
import './SubdomainGenerator.css';

const SubdomainGenerator = ({ 
  companyName, 
  selectedDomain, 
  onDomainSelect, 
  onNext, 
  onBack 
}) => {
  const [currentDomain, setCurrentDomain] = useState(selectedDomain || '');
  const [suggestions, setSuggestions] = useState([]);
  const [checking, setChecking] = useState(false);
  const [availability, setAvailability] = useState(null);
  const [validation, setValidation] = useState({ isValid: false, errors: [] });
  const [customInput, setCustomInput] = useState('');
  const [showCustomInput, setShowCustomInput] = useState(false);

  // Generate initial suggestions when component mounts
  useEffect(() => {
    if (companyName && !selectedDomain) {
      const generated = generateSubdomainSuggestions(companyName);
      setSuggestions(generated);
      if (generated.length > 0) {
        const firstSuggestion = generated[0];
        setCurrentDomain(firstSuggestion);
        checkAvailability(firstSuggestion);
      }
    }
  }, [companyName, selectedDomain]);

  // Validate domain format
  useEffect(() => {
    if (currentDomain) {
      const validation = validateSubdomain(currentDomain);
      setValidation(validation);
      
      if (validation.isValid) {
        checkAvailability(currentDomain);
      } else {
        setAvailability(null);
      }
    }
  }, [currentDomain]);

  // Check domain availability with backend
  const checkAvailability = useCallback(async (domain) => {
    if (!domain || !validateSubdomain(domain).isValid) {
      return;
    }

    setChecking(true);
    try {
      const { url } = buildTenantApiRequest(`/api/v1/organizations/domain-availability/${domain}`);
      
      const response = await fetch(url, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });

      if (response.ok) {
        const result = await response.json();
        setAvailability(result);
        
        // Update suggestions if domain is not available
        if (!result.available && result.suggested_alternatives) {
          setSuggestions(prev => {
            const combined = [...prev, ...result.suggested_alternatives];
            return [...new Set(combined)]; // Remove duplicates
          });
        }
      } else {
        console.error('Failed to check domain availability');
        setAvailability(null);
      }
    } catch (error) {
      console.error('Error checking domain availability:', error);
      setAvailability(null);
    } finally {
      setChecking(false);
    }
  }, []);

  const handleDomainSelect = (domain) => {
    setCurrentDomain(domain);
    setShowCustomInput(false);
    setCustomInput('');
  };

  const handleCustomSubmit = () => {
    if (customInput.trim()) {
      const cleanDomain = customInput.trim().toLowerCase();
      setCurrentDomain(cleanDomain);
      setShowCustomInput(false);
      setCustomInput('');
    }
  };

  const handleNext = () => {
    if (currentDomain && validation.isValid && availability?.available) {
      onDomainSelect(currentDomain);
      onNext();
    }
  };

  const renderAvailabilityStatus = () => {
    if (checking) {
      return (
        <div className="availability-status checking">
          <div className="spinner"></div>
          <span>Checking availability...</span>
        </div>
      );
    }

    if (!availability) {
      return null;
    }

    if (availability.available) {
      return (
        <div className="availability-status available">
          <span className="icon">✅</span>
          <span>{currentDomain}.sonicus.eu is available!</span>
        </div>
      );
    } else {
      return (
        <div className="availability-status unavailable">
          <span className="icon">❌</span>
          <span>{availability.message}</span>
        </div>
      );
    }
  };

  const renderValidationErrors = () => {
    if (validation.errors.length === 0) {
      return null;
    }

    return (
      <div className="validation-errors">
        {validation.errors.map((error, index) => (
          <div key={index} className="error-message">
            {error}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="subdomain-generator">
      <div className="step-header">
        <h2>Choose Your Subdomain</h2>
        <p>Your subdomain will be your organization's unique address on Sonicus</p>
      </div>

      {/* Current Selection */}
      <div className="current-selection">
        <div className="domain-preview">
          <div className="domain-parts">
            <span className="subdomain">{currentDomain || 'your-domain'}</span>
            <span className="separator">.</span>
            <span className="base-domain">sonicus.eu</span>
          </div>
        </div>
        
        {renderAvailabilityStatus()}
        {renderValidationErrors()}
      </div>

      {/* Suggestions */}
      <div className="suggestions-section">
        <h3>Suggested Subdomains</h3>
        <div className="suggestions-grid">
          {suggestions.map((suggestion, index) => (
            <button
              key={index}
              className={`suggestion-item ${currentDomain === suggestion ? 'selected' : ''}`}
              onClick={() => handleDomainSelect(suggestion)}
            >
              <span className="suggestion-domain">{suggestion}</span>
              <span className="suggestion-full">.sonicus.eu</span>
            </button>
          ))}
        </div>
      </div>

      {/* Custom Input */}
      <div className="custom-section">
        {showCustomInput ? (
          <div className="custom-input-container">
            <div className="custom-input-group">
              <input
                type="text"
                value={customInput}
                onChange={(e) => setCustomInput(e.target.value)}
                placeholder="Enter custom subdomain"
                className="custom-input"
                onKeyPress={(e) => e.key === 'Enter' && handleCustomSubmit()}
              />
              <span className="input-suffix">.sonicus.eu</span>
            </div>
            <div className="custom-actions">
              <button
                type="button"
                onClick={handleCustomSubmit}
                className="btn btn-sm btn-primary"
                disabled={!customInput.trim()}
              >
                Check Availability
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowCustomInput(false);
                  setCustomInput('');
                }}
                className="btn btn-sm btn-secondary"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <button
            type="button"
            onClick={() => setShowCustomInput(true)}
            className="btn btn-outline"
          >
            + Use Custom Subdomain
          </button>
        )}
      </div>

      {/* Requirements */}
      <div className="requirements-section">
        <h4>Subdomain Requirements:</h4>
        <ul>
          <li>3-63 characters long</li>
          <li>Start and end with a letter or number</li>
          <li>Only letters, numbers, and hyphens allowed</li>
          <li>No consecutive hyphens</li>
        </ul>
      </div>

      {/* Step Actions */}
      <div className="step-actions">
        <button
          type="button"
          onClick={onBack}
          className="btn btn-secondary"
        >
          Back
        </button>
        <button
          type="button"
          onClick={handleNext}
          className="btn btn-primary"
          disabled={!currentDomain || !validation.isValid || !availability?.available || checking}
        >
          Continue with {currentDomain || 'this subdomain'}
        </button>
      </div>
    </div>
  );
};

export default SubdomainGenerator;
