import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { useTenant } from '../context/TenantContext';
import { useAuth } from '../hooks/useAuth';
import axios from '../utils/axios';
import './OrganizationDashboard.css';

const OrganizationDashboard = () => {
  const { t } = useTranslation();
  const { organization, isB2B2CMode, getOrganizationBranding, hasFeature, getOrganizationLimits } = useTenant();
  const { user, hasRole } = useAuth();
  
  const [dashboardData, setDashboardData] = useState({
    users: { total: 0, active: 0, new_this_month: 0 },
    usage: { total_sessions: 0, total_listen_time: 0, avg_session_length: 0 },
    sounds: { total_packages: 0, most_popular: [] },
    wellness: { survey_responses: 0, avg_wellness_score: 0 }
  });
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const branding = getOrganizationBranding();
  const limits = getOrganizationLimits();

  useEffect(() => {
    if (!isB2B2CMode() || !organization) {
      setError(t('dashboard.error.noOrganization'));
      setLoading(false);
      return;
    }

    fetchDashboardData();
  }, [organization, isB2B2CMode]);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      // This endpoint should be created in the backend
      const response = await axios.get('/api/v1/organizations/me/dashboard');
      setDashboardData(response.data);
      setError(null);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      setError(t('dashboard.error.fetchFailed'));
    } finally {
      setLoading(false);
    }
  };

  if (!isB2B2CMode()) {
    return (
      <div className="organization-dashboard">
        <div className="container">
          <div className="error-state">
            <h2>{t('dashboard.error.b2cMode')}</h2>
            <p>{t('dashboard.error.b2cModeDesc')}</p>
          </div>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="organization-dashboard">
        <div className="container">
          <div className="loading-state">
            <div className="spinner"></div>
            <p>{t('common.loading')}</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="organization-dashboard">
        <div className="container">
          <div className="error-state">
            <h2>{t('dashboard.error.title')}</h2>
            <p>{error}</p>
            <button onClick={fetchDashboardData} className="btn btn-primary">
              {t('common.retry')}
            </button>
          </div>
        </div>
      </div>
    );
  }

  const usagePercentage = limits.maxUsers > 0 ? (dashboardData.users.total / limits.maxUsers) * 100 : 0;
  const isNearLimit = usagePercentage > 80;

  return (
    <div 
      className="organization-dashboard" 
      style={{ '--primary-color': branding.primaryColor, '--secondary-color': branding.secondaryColor }}
    >
      <div className="container">
        {/* Header */}
        <div className="dashboard-header">
          <div className="organization-info">
            {branding.logo && (
              <img src={branding.logo} alt={organization.name} className="organization-logo" />
            )}
            <div>
              <h1>{branding.companyName}</h1>
              <p className="organization-details">
                {organization.subscription_tier} • {organization.subscription_status}
                {organization.trial_end_date && (
                  <span className="trial-badge">
                    {t('dashboard.trialEnds')}: {new Date(organization.trial_end_date).toLocaleDateString()}
                  </span>
                )}
              </p>
            </div>
          </div>
          
          <div className="header-actions">
            <button className="btn btn-outline">
              {t('dashboard.settings')}
            </button>
            {hasRole('admin') && (
              <button className="btn btn-primary">
                {t('dashboard.manageUsers')}
              </button>
            )}
          </div>
        </div>

        {/* Quick Stats */}
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon">👥</div>
            <div className="stat-content">
              <h3>{dashboardData.users.total}</h3>
              <p>{t('dashboard.stats.totalUsers')}</p>
              <div className="stat-progress">
                <div 
                  className="progress-bar" 
                  style={{ width: `${Math.min(usagePercentage, 100)}%` }}
                ></div>
              </div>
              <small>
                {dashboardData.users.total} / {limits.maxUsers} {t('dashboard.stats.usersLimit')}
                {isNearLimit && (
                  <span className="warning-text"> • {t('dashboard.stats.nearLimit')}</span>
                )}
              </small>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">🎯</div>
            <div className="stat-content">
              <h3>{dashboardData.users.active}</h3>
              <p>{t('dashboard.stats.activeUsers')}</p>
              <small>
                +{dashboardData.users.new_this_month} {t('dashboard.stats.newThisMonth')}
              </small>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">🎵</div>
            <div className="stat-content">
              <h3>{dashboardData.usage.total_sessions}</h3>
              <p>{t('dashboard.stats.totalSessions')}</p>
              <small>
                {Math.round(dashboardData.usage.avg_session_length)} {t('dashboard.stats.avgMinutes')}
              </small>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">⏱️</div>
            <div className="stat-content">
              <h3>{Math.round(dashboardData.usage.total_listen_time / 60)}h</h3>
              <p>{t('dashboard.stats.totalListenTime')}</p>
              <small>
                {t('dashboard.stats.thisMonth')}
              </small>
            </div>
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="dashboard-content">
          
          {/* Popular Sounds */}
          <div className="dashboard-section">
            <div className="section-header">
              <h2>{t('dashboard.sections.popularSounds')}</h2>
              <button className="btn btn-sm btn-outline">
                {t('dashboard.viewAll')}
              </button>
            </div>
            
            <div className="sounds-list">
              {dashboardData.sounds.most_popular.length > 0 ? (
                dashboardData.sounds.most_popular.slice(0, 5).map((sound, index) => (
                  <div key={index} className="sound-item">
                    <div className="sound-rank">{index + 1}</div>
                    <div className="sound-info">
                      <h4>{sound.name}</h4>
                      <p>{sound.category}</p>
                    </div>
                    <div className="sound-stats">
                      <span className="listens-count">{sound.listens} {t('dashboard.listens')}</span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="empty-state">
                  <p>{t('dashboard.noData.sounds')}</p>
                </div>
              )}
            </div>
          </div>

          {/* Wellness Metrics */}
          {hasFeature('analytics') && (
            <div className="dashboard-section">
              <div className="section-header">
                <h2>{t('dashboard.sections.wellnessMetrics')}</h2>
                <button className="btn btn-sm btn-outline">
                  {t('dashboard.detailedReport')}
                </button>
              </div>
              
              <div className="wellness-overview">
                <div className="wellness-stat">
                  <h3>{dashboardData.wellness.avg_wellness_score}/10</h3>
                  <p>{t('dashboard.wellness.avgScore')}</p>
                </div>
                
                <div className="wellness-stat">
                  <h3>{dashboardData.wellness.survey_responses}</h3>
                  <p>{t('dashboard.wellness.responses')}</p>
                </div>
              </div>
              
              {dashboardData.wellness.survey_responses === 0 && (
                <div className="wellness-cta">
                  <p>{t('dashboard.wellness.noResponsesCTA')}</p>
                  <button className="btn btn-primary">
                    {t('dashboard.wellness.sendSurvey')}
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Quick Actions */}
          <div className="dashboard-section">
            <div className="section-header">
              <h2>{t('dashboard.sections.quickActions')}</h2>
            </div>
            
            <div className="actions-grid">
              <button className="action-card">
                <div className="action-icon">📧</div>
                <div className="action-content">
                  <h4>{t('dashboard.actions.inviteUsers')}</h4>
                  <p>{t('dashboard.actions.inviteUsersDesc')}</p>
                </div>
              </button>
              
              <Link to="/organization/branding" className="action-card">
                <div className="action-icon">🎨</div>
                <div className="action-content">
                  <h4>{t('dashboard.actions.customizeBranding')}</h4>
                  <p>{t('dashboard.actions.customizeBrandingDesc')}</p>
                </div>
              </Link>
              
              <button className="action-card">
                <div className="action-icon">📊</div>
                <div className="action-content">
                  <h4>{t('dashboard.actions.exportData')}</h4>
                  <p>{t('dashboard.actions.exportDataDesc')}</p>
                </div>
              </button>
              
              {hasFeature('api_access') && (
                <button className="action-card">
                  <div className="action-icon">⚡</div>
                  <div className="action-content">
                    <h4>{t('dashboard.actions.apiAccess')}</h4>
                    <p>{t('dashboard.actions.apiAccessDesc')}</p>
                  </div>
                </button>
              )}
            </div>
          </div>

          {/* Subscription Info */}
          <div className="dashboard-section subscription-section">
            <div className="section-header">
              <h2>{t('dashboard.sections.subscription')}</h2>
              <button className="btn btn-sm btn-primary">
                {t('dashboard.upgrade')}
              </button>
            </div>
            
            <div className="subscription-info">
              <div className="plan-details">
                <h3>{organization.subscription_tier} {t('dashboard.plan')}</h3>
                <ul className="feature-list">
                  <li>{t('dashboard.features.users', { count: limits.maxUsers })}</li>
                  <li>{t('dashboard.features.soundLibraries', { count: limits.maxSoundLibraries })}</li>
                  {hasFeature('analytics') && <li>{t('dashboard.features.analytics')}</li>}
                  {hasFeature('custom_branding') && <li>{t('dashboard.features.customBranding')}</li>}
                  {hasFeature('api_access') && <li>{t('dashboard.features.apiAccess')}</li>}
                </ul>
              </div>
              
              {organization.subscription_status === 'trial' && (
                <div className="trial-warning">
                  <h4>{t('dashboard.trial.ending')}</h4>
                  <p>{t('dashboard.trial.endingDesc')}</p>
                  <button className="btn btn-primary">
                    {t('dashboard.trial.upgradeNow')}
                  </button>
                </div>
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};

export default OrganizationDashboard;
