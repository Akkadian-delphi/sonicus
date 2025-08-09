import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import './BusinessWelcome.css';

const BusinessWelcomePage = () => {
  const { t } = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();
  
  const [organization, setOrganization] = useState(null);
  const [subdomain, setSubdomain] = useState('');

  useEffect(() => {
    // Get organization data from navigation state
    if (location.state?.organization) {
      setOrganization(location.state.organization);
      setSubdomain(location.state.subdomain);
    } else {
      // Redirect to registration if no organization data
      navigate('/business/register');
    }
  }, [location.state, navigate]);

  const nextSteps = [
    {
      title: t('business.welcome.steps.accessPortal'),
      description: t('business.welcome.steps.accessPortalDesc'),
      action: () => {
        window.location.href = `https://${subdomain}`;
      },
      actionText: t('business.welcome.steps.visitPortal'),
      primary: true
    },
    {
      title: t('business.welcome.steps.inviteTeam'),
      description: t('business.welcome.steps.inviteTeamDesc'),
      action: () => {
        // Navigate to team invitation page
        navigate('/business/invite-team');
      },
      actionText: t('business.welcome.steps.inviteMembers')
    },
    {
      title: t('business.welcome.steps.customizeBranding'),
      description: t('business.welcome.steps.customizeBrandingDesc'),
      action: () => {
        navigate('/business/settings/branding');
      },
      actionText: t('business.welcome.steps.customizeNow')
    },
    {
      title: t('business.welcome.steps.configureSounds'),
      description: t('business.welcome.steps.configureSoundsDesc'),
      action: () => {
        navigate('/business/sound-packages');
      },
      actionText: t('business.welcome.steps.browseSounds')
    }
  ];

  if (!organization) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>{t('common.loading')}</p>
      </div>
    );
  }

  return (
    <div className="business-welcome">
      <div className="container">
        {/* Success Header */}
        <div className="welcome-header">
          <div className="success-icon">
            <svg viewBox="0 0 52 52" className="checkmark">
              <circle className="checkmark__circle" cx="26" cy="26" r="25" fill="none"/>
              <path className="checkmark__check" fill="none" d="m14.1,27.2l7.1,7.2 16.7-16.8"/>
            </svg>
          </div>
          
          <h1>{t('business.welcome.title')}</h1>
          <h2>{organization.display_name || organization.name}</h2>
          
          <div className="organization-info">
            <div className="info-card">
              <strong>{t('business.welcome.yourSubdomain')}:</strong>
              <div className="subdomain-display">
                <a href={`https://${subdomain}`} target="_blank" rel="noopener noreferrer">
                  {subdomain}
                </a>
              </div>
            </div>
            
            <div className="info-card">
              <strong>{t('business.welcome.subscriptionTier')}:</strong>
              <span className="tier-badge">{organization.subscription_tier}</span>
            </div>
            
            <div className="info-card">
              <strong>{t('business.welcome.trialEnds')}:</strong>
              <span>{new Date(organization.trial_end_date).toLocaleDateString()}</span>
            </div>
          </div>
        </div>

        {/* Trial Information */}
        <div className="trial-info">
          <h3>{t('business.welcome.trialTitle')}</h3>
          <p>{t('business.welcome.trialDescription')}</p>
          <ul>
            <li>{t('business.welcome.trialFeatures.users', { count: organization.max_users })}</li>
            <li>{t('business.welcome.trialFeatures.soundLibraries', { count: organization.max_sound_libraries })}</li>
            <li>{t('business.welcome.trialFeatures.analytics')}</li>
            <li>{t('business.welcome.trialFeatures.support')}</li>
          </ul>
        </div>

        {/* Next Steps */}
        <div className="next-steps">
          <h3>{t('business.welcome.nextStepsTitle')}</h3>
          <p>{t('business.welcome.nextStepsDesc')}</p>
          
          <div className="steps-grid">
            {nextSteps.map((step, index) => (
              <div key={index} className={`step-card ${step.primary ? 'primary' : ''}`}>
                <div className="step-number">{index + 1}</div>
                <div className="step-content">
                  <h4>{step.title}</h4>
                  <p>{step.description}</p>
                  <button 
                    onClick={step.action} 
                    className={`btn ${step.primary ? 'btn-primary' : 'btn-secondary'}`}
                  >
                    {step.actionText}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Resources */}
        <div className="resources-section">
          <h3>{t('business.welcome.resourcesTitle')}</h3>
          <div className="resources-grid">
            <a href="/docs/getting-started" className="resource-card">
              <div className="resource-icon">📚</div>
              <h4>{t('business.welcome.resources.gettingStarted')}</h4>
              <p>{t('business.welcome.resources.gettingStartedDesc')}</p>
            </a>
            
            <a href="/docs/api" className="resource-card">
              <div className="resource-icon">⚡</div>
              <h4>{t('business.welcome.resources.apiDocs')}</h4>
              <p>{t('business.welcome.resources.apiDocsDesc')}</p>
            </a>
            
            <a href="/support" className="resource-card">
              <div className="resource-icon">💬</div>
              <h4>{t('business.welcome.resources.support')}</h4>
              <p>{t('business.welcome.resources.supportDesc')}</p>
            </a>
            
            <a href="/community" className="resource-card">
              <div className="resource-icon">👥</div>
              <h4>{t('business.welcome.resources.community')}</h4>
              <p>{t('business.welcome.resources.communityDesc')}</p>
            </a>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="welcome-footer">
          <p>{t('business.welcome.needHelp')}</p>
          <div className="footer-actions">
            <a href="mailto:support@sonicus.com" className="btn btn-outline">
              {t('business.welcome.contactSupport')}
            </a>
            <button 
              onClick={() => window.location.href = `https://${subdomain}`}
              className="btn btn-primary"
            >
              {t('business.welcome.goToPortal')}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BusinessWelcomePage;
