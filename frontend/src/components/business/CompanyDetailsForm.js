/**
 * Company Details Form Component
 * Collects basic company information for organization registration
 */

import React, { useState, useEffect } from 'react';
import './CompanyDetailsForm.css';

const CompanyDetailsForm = ({ data, onChange, onNext }) => {
  const [errors, setErrors] = useState({});
  const [touched, setTouched] = useState({});

  const handleInputChange = (field, value) => {
    onChange({ [field]: value });
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: null }));
    }
  };

  const handleBlur = (field) => {
    setTouched(prev => ({ ...prev, [field]: true }));
    validateField(field);
  };

  const validateField = (field) => {
    const value = data[field];
    let error = null;

    switch (field) {
      case 'name':
        if (!value || value.trim().length < 2) {
          error = 'Company name must be at least 2 characters';
        }
        break;
        
      case 'primary_contact_email':
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!value) {
          error = 'Email is required';
        } else if (!emailRegex.test(value)) {
          error = 'Please enter a valid email address';
        }
        break;
        
      case 'phone':
        if (value && value.length > 0) {
          const phoneRegex = /^[\+]?[0-9\s\-\(\)]{7,20}$/;
          if (!phoneRegex.test(value)) {
            error = 'Please enter a valid phone number';
          }
        }
        break;
        
      default:
        break;
    }

    if (error) {
      setErrors(prev => ({ ...prev, [field]: error }));
    }
    return !error;
  };

  const validateForm = () => {
    const fieldsToValidate = ['name', 'primary_contact_email'];
    let isValid = true;

    fieldsToValidate.forEach(field => {
      if (!validateField(field)) {
        isValid = false;
      }
    });

    return isValid;
  };

  const handleNext = () => {
    // Mark all required fields as touched
    const requiredFields = ['name', 'primary_contact_email'];
    const newTouched = {};
    requiredFields.forEach(field => {
      newTouched[field] = true;
    });
    setTouched(prev => ({ ...prev, ...newTouched }));

    if (validateForm()) {
      onNext();
    }
  };

  const companySizeOptions = [
    { value: '', label: 'Select company size' },
    { value: '1-10', label: '1-10 employees' },
    { value: '11-50', label: '11-50 employees' },
    { value: '51-200', label: '51-200 employees' },
    { value: '201-1000', label: '201-1000 employees' },
    { value: '1000+', label: '1000+ employees' }
  ];

  const industryOptions = [
    { value: '', label: 'Select industry' },
    { value: 'healthcare', label: 'Healthcare & Wellness' },
    { value: 'education', label: 'Education' },
    { value: 'corporate', label: 'Corporate & Business' },
    { value: 'hospitality', label: 'Hospitality & Tourism' },
    { value: 'retail', label: 'Retail & E-commerce' },
    { value: 'fitness', label: 'Fitness & Sports' },
    { value: 'spa', label: 'Spa & Beauty' },
    { value: 'therapy', label: 'Therapy & Counseling' },
    { value: 'meditation', label: 'Meditation & Mindfulness' },
    { value: 'other', label: 'Other' }
  ];

  return (
    <div className="company-details-form">
      <div className="step-header">
        <h2>Company Information</h2>
        <p>Tell us about your organization to get started with Sonicus</p>
      </div>

      <form onSubmit={(e) => { e.preventDefault(); handleNext(); }}>
        {/* Basic Information */}
        <div className="form-section">
          <h3>Basic Information</h3>
          
          <div className="form-group">
            <label htmlFor="name" className="required">
              Company Name
            </label>
            <input
              id="name"
              type="text"
              value={data.name || ''}
              onChange={(e) => handleInputChange('name', e.target.value)}
              onBlur={() => handleBlur('name')}
              placeholder="Enter your company name"
              className={errors.name && touched.name ? 'error' : ''}
            />
            {errors.name && touched.name && (
              <div className="error-message">{errors.name}</div>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="display_name">
              Display Name (Optional)
            </label>
            <input
              id="display_name"
              type="text"
              value={data.display_name || ''}
              onChange={(e) => handleInputChange('display_name', e.target.value)}
              placeholder="Public name for your organization (defaults to company name)"
            />
            <small className="form-help">
              This is how your organization will appear to your customers
            </small>
          </div>

          <div className="form-group">
            <label htmlFor="primary_contact_email" className="required">
              Primary Contact Email
            </label>
            <input
              id="primary_contact_email"
              type="email"
              value={data.primary_contact_email || ''}
              onChange={(e) => handleInputChange('primary_contact_email', e.target.value)}
              onBlur={() => handleBlur('primary_contact_email')}
              placeholder="admin@yourcompany.com"
              className={errors.primary_contact_email && touched.primary_contact_email ? 'error' : ''}
            />
            {errors.primary_contact_email && touched.primary_contact_email && (
              <div className="error-message">{errors.primary_contact_email}</div>
            )}
            <small className="form-help">
              This will be your admin login email and where we'll send setup instructions
            </small>
          </div>

          <div className="form-group">
            <label htmlFor="phone">
              Phone Number (Optional)
            </label>
            <input
              id="phone"
              type="tel"
              value={data.phone || ''}
              onChange={(e) => handleInputChange('phone', e.target.value)}
              onBlur={() => handleBlur('phone')}
              placeholder="+1 (555) 123-4567"
              className={errors.phone && touched.phone ? 'error' : ''}
            />
            {errors.phone && touched.phone && (
              <div className="error-message">{errors.phone}</div>
            )}
          </div>
        </div>

        {/* Business Details */}
        <div className="form-section">
          <h3>Business Details</h3>
          
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="industry">
                Industry
              </label>
              <select
                id="industry"
                value={data.industry || ''}
                onChange={(e) => handleInputChange('industry', e.target.value)}
              >
                {industryOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="company_size">
                Company Size
              </label>
              <select
                id="company_size"
                value={data.company_size || ''}
                onChange={(e) => handleInputChange('company_size', e.target.value)}
              >
                {companySizeOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Address Information */}
        <div className="form-section">
          <h3>Address Information (Optional)</h3>
          
          <div className="form-group">
            <label htmlFor="address_line1">
              Address Line 1
            </label>
            <input
              id="address_line1"
              type="text"
              value={data.address_line1 || ''}
              onChange={(e) => handleInputChange('address_line1', e.target.value)}
              placeholder="Street address"
            />
          </div>

          <div className="form-group">
            <label htmlFor="address_line2">
              Address Line 2
            </label>
            <input
              id="address_line2"
              type="text"
              value={data.address_line2 || ''}
              onChange={(e) => handleInputChange('address_line2', e.target.value)}
              placeholder="Apartment, suite, etc."
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="city">
                City
              </label>
              <input
                id="city"
                type="text"
                value={data.city || ''}
                onChange={(e) => handleInputChange('city', e.target.value)}
                placeholder="City"
              />
            </div>

            <div className="form-group">
              <label htmlFor="state">
                State/Province
              </label>
              <input
                id="state"
                type="text"
                value={data.state || ''}
                onChange={(e) => handleInputChange('state', e.target.value)}
                placeholder="State or Province"
              />
            </div>

            <div className="form-group">
              <label htmlFor="postal_code">
                Postal Code
              </label>
              <input
                id="postal_code"
                type="text"
                value={data.postal_code || ''}
                onChange={(e) => handleInputChange('postal_code', e.target.value)}
                placeholder="12345"
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="country">
              Country
            </label>
            <input
              id="country"
              type="text"
              value={data.country || ''}
              onChange={(e) => handleInputChange('country', e.target.value)}
              placeholder="Country"
            />
          </div>
        </div>

        {/* Step Actions */}
        <div className="step-actions">
          <button
            type="submit"
            className="btn btn-primary"
          >
            Continue to Subdomain Setup
          </button>
        </div>
      </form>
    </div>
  );
};

export default CompanyDetailsForm;
