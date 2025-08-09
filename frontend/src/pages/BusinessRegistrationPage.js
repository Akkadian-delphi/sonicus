import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import axios from '../utils/axios';
import './BusinessRegistration.css';

const BusinessRegistrationPage = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  
  const [formData, setFormData] = useState({
    name: '',
    display_name: '',
    domain: '',
    primary_contact_email: '',
    phone: '',
    industry: '',
    company_size: '',
    address_line1: '',
    address_line2: '',
    city: '',
    state: '',
    country: '',
    postal_code: ''
  });

  const [domainAvailability, setDomainAvailability] = useState({
    available: null,
    checking: false,
    message: '',
    suggestions: []
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [step, setStep] = useState(1);

  // Industry options
  const industryOptions = [
    'Technology', 'Healthcare', 'Finance', 'Education', 'Retail',
    'Manufacturing', 'Consulting', 'Real Estate', 'Non-profit', 'Other'
  ];

  // Company size options
  const companySizeOptions = [
    '1-10', '11-50', '51-200', '201-1000', '1000+'
  ];

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));

    // Auto-generate display name if not manually changed
    if (name === 'name' && !formData.display_name) {
      setFormData(prev => ({ ...prev, display_name: value }));
    }

    // Auto-generate domain suggestion if not manually changed
    if (name === 'name' && !formData.domain) {
      const domainSuggestion = value.toLowerCase()
        .replace(/[^a-z0-9]/g, '')
        .substring(0, 20);
      if (domainSuggestion) {
        setFormData(prev => ({ ...prev, domain: domainSuggestion }));
        // Don't auto-check availability as user is still typing
      }
    }
  };

  const checkDomainAvailability = async (domain) => {
    if (!domain || domain.length < 3) {
      setDomainAvailability({
        available: false,
        checking: false,
        message: t('business.registration.domain.tooShort'),
        suggestions: []
      });
      return;
    }

    setDomainAvailability(prev => ({ ...prev, checking: true }));

    try {
      const response = await axios.get(`/api/v1/organizations/domain-availability/${domain}`);
      const result = response.data;

      setDomainAvailability({
        available: result.available,
        checking: false,
        message: result.message,
        suggestions: result.suggested_alternatives || []
      });

    } catch (error) {
      setDomainAvailability({
        available: false,
        checking: false,
        message: t('business.registration.domain.checkError'),
        suggestions: []
      });
    }
  };

  const handleDomainBlur = () => {
    if (formData.domain) {
      checkDomainAvailability(formData.domain);
    }
  };

  const selectSuggestedDomain = (domain) => {
    setFormData(prev => ({ ...prev, domain }));
    checkDomainAvailability(domain);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Final domain availability check
      if (domainAvailability.available !== true) {
        throw new Error(t('business.registration.domain.notAvailable'));
      }

      const response = await axios.post('/api/v1/organizations/register', formData);
      const organization = response.data;

      // Registration successful
      console.log('Organization registered:', organization);

      // Redirect to success page or organization dashboard
      navigate('/business/welcome', { 
        state: { 
          organization,
          subdomain: `${organization.domain}.sonicus.com`
        }
      });

    } catch (error) {
      console.error('Registration error:', error);
      setError(
        error.response?.data?.detail || 
        error.message || 
        t('business.registration.error.general')
      );
    } finally {
      setLoading(false);
    }
  };

  const nextStep = () => {
    if (step === 1) {
      // Validate required fields for step 1
      if (!formData.name || !formData.domain || !formData.primary_contact_email) {
        setError(t('business.registration.error.requiredFields'));
        return;
      }
      if (domainAvailability.available !== true) {
        setError(t('business.registration.error.domainNotAvailable'));
        return;
      }
    }
    setError(null);
    setStep(step + 1);
  };

  const prevStep = () => {
    setError(null);
    setStep(step - 1);
  };

  return (
    <div className="business-registration">
      <div className="container">
        <div className="registration-header">
          <h1>{t('business.registration.title')}</h1>
          <p>{t('business.registration.subtitle')}</p>
          
          {/* Progress indicator */}
          <div className="progress-steps">
            <div className={`step ${step >= 1 ? 'active' : ''}`}>
              <span>1</span>
              <label>{t('business.registration.step1')}</label>
            </div>
            <div className={`step ${step >= 2 ? 'active' : ''}`}>
              <span>2</span>
              <label>{t('business.registration.step2')}</label>
            </div>
            <div className={`step ${step >= 3 ? 'active' : ''}`}>
              <span>3</span>
              <label>{t('business.registration.step3')}</label>
            </div>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="registration-form">
          {/* Step 1: Basic Information */}
          {step === 1 && (
            <div className="step-content">
              <h2>{t('business.registration.basicInfo')}</h2>
              
              <div className="form-group">
                <label htmlFor="name" className="required">
                  {t('business.registration.companyName')}
                </label>
                <input
                  type="text"
                  id="name"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  required
                  placeholder={t('business.registration.companyNamePlaceholder')}
                />
              </div>

              <div className="form-group">
                <label htmlFor="display_name">
                  {t('business.registration.displayName')}
                </label>
                <input
                  type="text"
                  id="display_name"
                  name="display_name"
                  value={formData.display_name}
                  onChange={handleInputChange}
                  placeholder={t('business.registration.displayNamePlaceholder')}
                />
                <small>{t('business.registration.displayNameHelp')}</small>
              </div>

              <div className="form-group">
                <label htmlFor="domain" className="required">
                  {t('business.registration.subdomain')}
                </label>
                <div className="domain-input-group">
                  <input
                    type="text"
                    id="domain"
                    name="domain"
                    value={formData.domain}
                    onChange={handleInputChange}
                    onBlur={handleDomainBlur}
                    required
                    placeholder="your-company"
                    pattern="[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]"
                  />
                  <span className="domain-suffix">.sonicus.com</span>
                </div>
                
                {/* Domain availability feedback */}
                {domainAvailability.checking && (
                  <div className="domain-feedback checking">
                    {t('business.registration.domain.checking')}
                  </div>
                )}
                
                {!domainAvailability.checking && domainAvailability.available === true && (
                  <div className="domain-feedback available">
                    ✓ {domainAvailability.message}
                  </div>
                )}
                
                {!domainAvailability.checking && domainAvailability.available === false && (
                  <div className="domain-feedback unavailable">
                    ✗ {domainAvailability.message}
                    {domainAvailability.suggestions.length > 0 && (
                      <div className="domain-suggestions">
                        <p>{t('business.registration.domain.suggestions')}:</p>
                        <div className="suggestions-list">
                          {domainAvailability.suggestions.map((suggestion, index) => (
                            <button
                              key={index}
                              type="button"
                              className="suggestion-button"
                              onClick={() => selectSuggestedDomain(suggestion)}
                            >
                              {suggestion}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>

              <div className="form-group">
                <label htmlFor="primary_contact_email" className="required">
                  {t('business.registration.primaryEmail')}
                </label>
                <input
                  type="email"
                  id="primary_contact_email"
                  name="primary_contact_email"
                  value={formData.primary_contact_email}
                  onChange={handleInputChange}
                  required
                  placeholder="admin@your-company.com"
                />
              </div>

              <div className="form-group">
                <label htmlFor="phone">
                  {t('business.registration.phone')}
                </label>
                <input
                  type="tel"
                  id="phone"
                  name="phone"
                  value={formData.phone}
                  onChange={handleInputChange}
                  placeholder="+1 (555) 123-4567"
                />
              </div>
            </div>
          )}

          {/* Step 2: Business Details */}
          {step === 2 && (
            <div className="step-content">
              <h2>{t('business.registration.businessDetails')}</h2>
              
              <div className="form-group">
                <label htmlFor="industry">
                  {t('business.registration.industry')}
                </label>
                <select
                  id="industry"
                  name="industry"
                  value={formData.industry}
                  onChange={handleInputChange}
                >
                  <option value="">{t('business.registration.selectIndustry')}</option>
                  {industryOptions.map(industry => (
                    <option key={industry} value={industry}>
                      {t(`business.industries.${industry.toLowerCase()}`, industry)}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="company_size">
                  {t('business.registration.companySize')}
                </label>
                <select
                  id="company_size"
                  name="company_size"
                  value={formData.company_size}
                  onChange={handleInputChange}
                >
                  <option value="">{t('business.registration.selectCompanySize')}</option>
                  {companySizeOptions.map(size => (
                    <option key={size} value={size}>
                      {t(`business.companySize.${size}`, size)} {t('business.registration.employees')}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}

          {/* Step 3: Address (Optional) */}
          {step === 3 && (
            <div className="step-content">
              <h2>{t('business.registration.addressInfo')}</h2>
              <p className="step-description">{t('business.registration.addressOptional')}</p>
              
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="address_line1">
                    {t('business.registration.addressLine1')}
                  </label>
                  <input
                    type="text"
                    id="address_line1"
                    name="address_line1"
                    value={formData.address_line1}
                    onChange={handleInputChange}
                    placeholder="123 Business St"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="address_line2">
                    {t('business.registration.addressLine2')}
                  </label>
                  <input
                    type="text"
                    id="address_line2"
                    name="address_line2"
                    value={formData.address_line2}
                    onChange={handleInputChange}
                    placeholder="Suite 100"
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="city">
                    {t('business.registration.city')}
                  </label>
                  <input
                    type="text"
                    id="city"
                    name="city"
                    value={formData.city}
                    onChange={handleInputChange}
                    placeholder="New York"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="state">
                    {t('business.registration.state')}
                  </label>
                  <input
                    type="text"
                    id="state"
                    name="state"
                    value={formData.state}
                    onChange={handleInputChange}
                    placeholder="NY"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="postal_code">
                    {t('business.registration.postalCode')}
                  </label>
                  <input
                    type="text"
                    id="postal_code"
                    name="postal_code"
                    value={formData.postal_code}
                    onChange={handleInputChange}
                    placeholder="10001"
                  />
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="country">
                  {t('business.registration.country')}
                </label>
                <input
                  type="text"
                  id="country"
                  name="country"
                  value={formData.country}
                  onChange={handleInputChange}
                  placeholder="United States"
                />
              </div>
            </div>
          )}

          {/* Error message */}
          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          {/* Navigation buttons */}
          <div className="form-navigation">
            {step > 1 && (
              <button
                type="button"
                onClick={prevStep}
                className="btn btn-secondary"
                disabled={loading}
              >
                {t('business.registration.previous')}
              </button>
            )}

            {step < 3 ? (
              <button
                type="button"
                onClick={nextStep}
                className="btn btn-primary"
                disabled={loading || (step === 1 && domainAvailability.available !== true)}
              >
                {t('business.registration.next')}
              </button>
            ) : (
              <button
                type="submit"
                className="btn btn-success"
                disabled={loading}
              >
                {loading ? t('business.registration.creating') : t('business.registration.createOrganization')}
              </button>
            )}
          </div>
        </form>

        {/* Additional info */}
        <div className="registration-footer">
          <p>{t('business.registration.trialInfo')}</p>
          <p>
            {t('business.registration.haveAccount')}{' '}
            <a href="/login">{t('business.registration.signIn')}</a>
          </p>
        </div>
      </div>
    </div>
  );
};

export default BusinessRegistrationPage;
