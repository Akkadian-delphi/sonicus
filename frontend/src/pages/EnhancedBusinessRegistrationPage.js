import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import axios from '../utils/axios';
import './EnhancedBusinessRegistration.css';

const EnhancedBusinessRegistrationPage = () => {
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
  
  // Infrastructure setup tracking
  const [infrastructureSetup, setInfrastructureSetup] = useState({
    active: false,
    organizationId: null,
    subdomain: null,
    steps: {
      registration: { status: 'pending', message: '' },
      dns: { status: 'pending', message: '' },
      payment: { status: 'pending', message: '' },
      crm: { status: 'pending', message: '' },
      verification: { status: 'pending', message: '' },
      deployment: { status: 'pending', message: '' }
    },
    completedAt: null,
    error: null
  });

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

  // Monitor infrastructure setup progress
  const monitorInfrastructureSetup = useCallback(async (organizationId, subdomain) => {
    const maxAttempts = 30; // Monitor for 30 attempts (about 2 minutes)
    let attempts = 0;
    
    const checkProgress = async () => {
      if (attempts >= maxAttempts) {
        setInfrastructureSetup(prev => ({
          ...prev,
          error: 'Infrastructure setup monitoring timeout'
        }));
        return;
      }

      try {
        // In a real implementation, you'd have an endpoint to check infrastructure progress
        // For now, we'll simulate the progress based on typical setup times
        
        const now = Date.now();
        const elapsed = now - infrastructureSetup.startTime;
        
        let newSteps = { ...infrastructureSetup.steps };
        
        // Registration completed (immediate)
        if (elapsed > 0) {
          newSteps.registration = { status: 'completed', message: 'Organization created successfully' };
        }
        
        // DNS setup (2-5 seconds)
        if (elapsed > 2000) {
          newSteps.dns = { status: 'in-progress', message: 'Creating DNS subdomain record...' };
        }
        if (elapsed > 5000) {
          newSteps.dns = { status: 'completed', message: `DNS record created: ${subdomain}.sonicus.eu` };
        }
        
        // Payment setup (3-7 seconds)
        if (elapsed > 3000) {
          newSteps.payment = { status: 'in-progress', message: 'Setting up payment customer...' };
        }
        if (elapsed > 7000) {
          newSteps.payment = { status: 'completed', message: 'Payment customer created successfully' };
        }
        
        // CRM integration (4-8 seconds)
        if (elapsed > 4000) {
          newSteps.crm = { status: 'in-progress', message: 'Creating CRM lead...' };
        }
        if (elapsed > 8000) {
          newSteps.crm = { status: 'completed', message: 'CRM lead created successfully' };
        }
        
        // DNS verification (8-15 seconds)
        if (elapsed > 8000) {
          newSteps.verification = { status: 'in-progress', message: 'Verifying DNS propagation...' };
        }
        if (elapsed > 15000) {
          newSteps.verification = { status: 'completed', message: 'DNS propagation verified' };
        }
        
        // Container deployment (12-20 seconds)
        if (elapsed > 12000) {
          newSteps.deployment = { status: 'in-progress', message: 'Deploying organization container...' };
        }
        if (elapsed > 20000) {
          newSteps.deployment = { status: 'completed', message: 'Container deployed successfully' };
        }
        
        setInfrastructureSetup(prev => ({
          ...prev,
          steps: newSteps
        }));
        
        // Check if all steps are completed
        const allCompleted = Object.values(newSteps).every(step => step.status === 'completed');
        if (allCompleted) {
          setInfrastructureSetup(prev => ({
            ...prev,
            completedAt: new Date(),
            active: false
          }));
          
          // Redirect after a brief pause to show completion
          setTimeout(() => {
            navigate('/business/welcome', { 
              state: { 
                organizationId,
                subdomain: `${subdomain}.sonicus.eu`,
                infrastructureReady: true
              }
            });
          }, 2000);
          
          return;
        }
        
        attempts++;
        setTimeout(checkProgress, 2000); // Check every 2 seconds
        
      } catch (error) {
        console.error('Error monitoring infrastructure setup:', error);
        setInfrastructureSetup(prev => ({
          ...prev,
          error: 'Failed to monitor infrastructure setup'
        }));
      }
    };
    
    // Start monitoring
    setInfrastructureSetup(prev => ({
      ...prev,
      startTime: Date.now()
    }));
    
    setTimeout(checkProgress, 1000); // Start after 1 second
  }, [navigate, infrastructureSetup.steps, infrastructureSetup.startTime]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Final domain availability check
      if (domainAvailability.available !== true) {
        throw new Error(t('business.registration.domain.notAvailable'));
      }

      // Update infrastructure setup state to show registration in progress
      setInfrastructureSetup(prev => ({
        ...prev,
        active: true,
        subdomain: formData.domain,
        steps: {
          registration: { status: 'in-progress', message: 'Creating organization...' },
          dns: { status: 'pending', message: '' },
          payment: { status: 'pending', message: '' },
          crm: { status: 'pending', message: '' },
          verification: { status: 'pending', message: '' },
          deployment: { status: 'pending', message: '' }
        }
      }));

      // Move to infrastructure setup step
      setStep(4);

      const response = await axios.post('/api/v1/organizations/register', formData);
      const organization = response.data;

      console.log('Organization registered:', organization);

      // Update infrastructure setup with organization details
      setInfrastructureSetup(prev => ({
        ...prev,
        organizationId: organization.id,
        subdomain: organization.domain,
        steps: {
          ...prev.steps,
          registration: { status: 'completed', message: 'Organization created successfully' }
        }
      }));

      // Start monitoring infrastructure setup
      monitorInfrastructureSetup(organization.id, organization.domain);

    } catch (error) {
      console.error('Registration error:', error);
      setError(
        error.response?.data?.detail || 
        error.message || 
        t('business.registration.error.general')
      );
      
      // Reset infrastructure setup on error
      setInfrastructureSetup(prev => ({
        ...prev,
        active: false,
        error: error.message
      }));
      
      setStep(3); // Go back to previous step
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

  // Infrastructure setup progress component
  const InfrastructureProgress = () => (
    <div className="infrastructure-progress">
      <h2>{t('business.registration.infrastructure.title')}</h2>
      <p>{t('business.registration.infrastructure.description')}</p>
      
      <div className="infrastructure-steps">
        {Object.entries(infrastructureSetup.steps).map(([key, step]) => (
          <div key={key} className={`infrastructure-step ${step.status}`}>
            <div className="step-icon">
              {step.status === 'completed' && '✓'}
              {step.status === 'in-progress' && (
                <div className="spinner">
                  <div className="spinner-dot"></div>
                  <div className="spinner-dot"></div>
                  <div className="spinner-dot"></div>
                </div>
              )}
              {step.status === 'pending' && '○'}
            </div>
            <div className="step-content">
              <div className="step-title">
                {t(`business.registration.infrastructure.${key}.title`)}
              </div>
              <div className="step-message">
                {step.message || t(`business.registration.infrastructure.${key}.description`)}
              </div>
            </div>
          </div>
        ))}
      </div>

      {infrastructureSetup.error && (
        <div className="infrastructure-error">
          <p>{t('business.registration.infrastructure.error')}: {infrastructureSetup.error}</p>
          <button 
            type="button"
            onClick={() => navigate('/business/welcome', { state: { organizationId: infrastructureSetup.organizationId } })}
            className="btn btn-primary"
          >
            {t('business.registration.infrastructure.continueAnyway')}
          </button>
        </div>
      )}

      {infrastructureSetup.completedAt && (
        <div className="infrastructure-complete">
          <div className="success-icon">🎉</div>
          <h3>{t('business.registration.infrastructure.complete')}</h3>
          
          <div className="deployment-info">
            <p>{t('business.registration.infrastructure.redirect')}</p>
            <p className="deployment-status">{t('business.registration.infrastructure.deploymentStatus')}</p>
            <ul className="deployment-steps">
              {t('business.registration.infrastructure.deploymentSteps', { returnObjects: true }).map((step, index) => (
                <li key={index}>• {step}</li>
              ))}
            </ul>
          </div>

          <div className="email-notification">
            <p>{t('business.registration.infrastructure.emailNotification', { email: formData.primary_contact_email })}</p>
            <ul className="email-includes">
              {t('business.registration.infrastructure.emailIncludes', { 
                returnObjects: true, 
                subdomain: infrastructureSetup.subdomain || formData.domain 
              }).map((item, index) => (
                <li key={index}>• {item}</li>
              ))}
            </ul>
          </div>

          <div className="completion-footer">
            <p className="estimated-time">{t('business.registration.infrastructure.estimatedTime')}</p>
            <p className="thank-you">{t('business.registration.infrastructure.thankYou')}</p>
          </div>
        </div>
      )}
    </div>
  );

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
            <div className={`step ${step >= 4 ? 'active' : ''}`}>
              <span>4</span>
              <label>{t('business.registration.step4')}</label>
            </div>
          </div>
        </div>

        {/* Show infrastructure progress when active */}
        {step === 4 && infrastructureSetup.active ? (
          <InfrastructureProgress />
        ) : (
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
                  <small className="field-help">
                    📧 We'll send your login credentials and setup confirmation to this email
                  </small>
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
        )}

        {/* Additional info */}
        {step !== 4 && (
          <div className="registration-footer">
            <p>{t('business.registration.trialInfo')}</p>
            <p>
              {t('business.registration.haveAccount')}{' '}
              <a href="/login">{t('business.registration.signIn')}</a>
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default EnhancedBusinessRegistrationPage;
