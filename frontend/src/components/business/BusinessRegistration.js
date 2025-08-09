/**
 * Business Registration Component
 * Phase 2.3 implementation from NEXT.md
 * 
 * Complete organization registration flow with:
 * - Company information form
 * - Subdomain generation and availability checking
 * - Stripe payment integration
 * - Terms acceptance
 */

import React, { useState, useEffect } from 'react';
import { 
  generateSubdomainSuggestions, 
  validateSubdomain,
  buildTenantApiRequest 
} from '../../utils/domainDetection';
import SubdomainGenerator from './SubdomainGenerator';
import CompanyDetailsForm from './CompanyDetailsForm';
import StripePaymentForm from './StripePaymentForm';
import './BusinessRegistration.css';

const BusinessRegistration = () => {
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    // Company Details
    name: '',
    display_name: '',
    domain: '',
    primary_contact_email: '',
    phone: '',
    industry: '',
    company_size: '',
    
    // Address
    address_line1: '',
    address_line2: '',
    city: '',
    state: '',
    country: '',
    postal_code: '',
    
    // Subscription
    subscription_plan: 'starter',
    payment_method: null,
    
    // Legal
    terms_accepted: false,
    privacy_accepted: false
  });
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [registrationResult, setRegistrationResult] = useState(null);

  const steps = [
    { id: 1, title: 'Company Details', component: 'company' },
    { id: 2, title: 'Subdomain Setup', component: 'subdomain' },
    { id: 3, title: 'Subscription Plan', component: 'payment' },
    { id: 4, title: 'Review & Submit', component: 'review' }
  ];

  const updateFormData = (updates) => {
    setFormData(prev => ({ ...prev, ...updates }));
  };

  const handleNext = () => {
    if (currentStep < steps.length) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);

    try {
      // Validate required fields
      const requiredFields = ['name', 'domain', 'primary_contact_email'];
      for (const field of requiredFields) {
        if (!formData[field]) {
          throw new Error(`${field.replace('_', ' ')} is required`);
        }
      }

      if (!formData.terms_accepted) {
        throw new Error('You must accept the terms of service');
      }

      // Submit registration
      const { url, options } = buildTenantApiRequest('/api/v1/organizations/register');
      
      const response = await fetch(url, {
        method: 'POST',
        ...options,
        body: JSON.stringify({
          name: formData.name,
          display_name: formData.display_name || formData.name,
          domain: formData.domain,
          primary_contact_email: formData.primary_contact_email,
          phone: formData.phone,
          industry: formData.industry,
          company_size: formData.company_size,
          address_line1: formData.address_line1,
          address_line2: formData.address_line2,
          city: formData.city,
          state: formData.state,
          country: formData.country,
          postal_code: formData.postal_code
        })
      });

      if (response.ok) {
        const result = await response.json();
        setRegistrationResult(result);
        setSuccess(true);
        console.log('✅ Registration successful:', result);
      } else {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Registration failed');
      }

    } catch (err) {
      console.error('❌ Registration error:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const renderStep = () => {
    const step = steps.find(s => s.id === currentStep);
    
    switch (step.component) {
      case 'company':
        return (
          <CompanyDetailsForm
            data={formData}
            onChange={updateFormData}
            onNext={handleNext}
          />
        );
      
      case 'subdomain':
        return (
          <SubdomainGenerator
            companyName={formData.name}
            selectedDomain={formData.domain}
            onDomainSelect={(domain) => updateFormData({ domain })}
            onNext={handleNext}
            onBack={handleBack}
          />
        );
      
      case 'payment':
        return (
          <StripePaymentForm
            formData={formData}
            onChange={updateFormData}
            onNext={handleNext}
            onBack={handleBack}
          />
        );
      
      case 'review':
        return (
          <ReviewStep
            data={formData}
            onSubmit={handleSubmit}
            onBack={handleBack}
            loading={loading}
            error={error}
          />
        );
      
      default:
        return null;
    }
  };

  if (success) {
    return (
      <div className="registration-success">
        <div className="success-content">
          <div className="success-icon">✅</div>
          <h1>Registration Successful!</h1>
          
          <div className="success-details">
            <p>Your Sonicus instance is being prepared...</p>
            
            <div className="deployment-status">
              <h3>🚀 We're currently:</h3>
              <ul>
                <li>Setting up your dedicated container</li>
                <li>Configuring your database</li>
                <li>Preparing your sound library</li>
                <li>Setting up your admin dashboard</li>
              </ul>
            </div>

            <div className="next-steps">
              <h3>📧 What's Next?</h3>
              <p>
                You'll receive an email at <strong>{formData.primary_contact_email}</strong> 
                in approximately 5-10 minutes with:
              </p>
              <ul>
                <li>Your login credentials</li>
                <li>Direct access to {formData.domain}.sonicus.eu</li>
                <li>Getting started guide</li>
              </ul>
            </div>

            <div className="registration-info">
              <h4>Your Details:</h4>
              <p><strong>Organization:</strong> {registrationResult?.name}</p>
              <p><strong>Subdomain:</strong> {registrationResult?.domain}.sonicus.eu</p>
              <p><strong>Subscription:</strong> {registrationResult?.subscription_tier || 'Starter'} (Trial)</p>
            </div>
          </div>

          <div className="success-actions">
            <button 
              onClick={() => window.location.href = '/'}
              className="btn btn-primary"
            >
              Return to Homepage
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="business-registration">
      <div className="registration-container">
        {/* Progress Indicator */}
        <div className="progress-steps">
          {steps.map(step => (
            <div 
              key={step.id}
              className={`step ${currentStep === step.id ? 'active' : ''} ${currentStep > step.id ? 'completed' : ''}`}
            >
              <div className="step-number">{step.id}</div>
              <div className="step-title">{step.title}</div>
            </div>
          ))}
        </div>

        {/* Step Content */}
        <div className="step-content">
          {renderStep()}
        </div>
      </div>
    </div>
  );
};

// Review Step Component
const ReviewStep = ({ data, onSubmit, onBack, loading, error }) => {
  return (
    <div className="review-step">
      <h2>Review Your Registration</h2>
      
      <div className="review-sections">
        <div className="review-section">
          <h3>Company Information</h3>
          <div className="review-grid">
            <div><strong>Name:</strong> {data.name}</div>
            <div><strong>Email:</strong> {data.primary_contact_email}</div>
            <div><strong>Phone:</strong> {data.phone || 'Not provided'}</div>
            <div><strong>Industry:</strong> {data.industry || 'Not specified'}</div>
          </div>
        </div>

        <div className="review-section">
          <h3>Subdomain</h3>
          <div className="subdomain-preview">
            <strong>{data.domain}.sonicus.eu</strong>
          </div>
        </div>

        <div className="review-section">
          <h3>Subscription</h3>
          <div><strong>Plan:</strong> Starter (14-day free trial)</div>
          <div><strong>Price:</strong> €29/month after trial</div>
        </div>

        <div className="review-section">
          <h3>Legal Agreements</h3>
          <div className="legal-checkboxes">
            <label>
              <input
                type="checkbox"
                checked={data.terms_accepted}
                onChange={(e) => data.onChange?.({ terms_accepted: e.target.checked })}
              />
              I accept the Terms of Service
            </label>
            <label>
              <input
                type="checkbox"
                checked={data.privacy_accepted}
                onChange={(e) => data.onChange?.({ privacy_accepted: e.target.checked })}
              />
              I accept the Privacy Policy
            </label>
          </div>
        </div>
      </div>

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      <div className="step-actions">
        <button
          type="button"
          onClick={onBack}
          className="btn btn-secondary"
          disabled={loading}
        >
          Back
        </button>
        <button
          type="button"
          onClick={onSubmit}
          className="btn btn-primary"
          disabled={loading || !data.terms_accepted}
        >
          {loading ? 'Creating Organization...' : 'Complete Registration'}
        </button>
      </div>
    </div>
  );
};

export default BusinessRegistration;
