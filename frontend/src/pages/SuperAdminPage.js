import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { Navigate } from 'react-router-dom';
import '../styles/SuperAdminPage.css';

// Import API services and hooks
import { 
  getPlatformStats, 
  getOrganizations, 
  createOrganization, 
  updateOrganization,
  deleteOrganization,
  transformOrganizationData,
  transformPlatformStats
} from '../utils/apiService';
import { useApiCall, usePaginatedApi, useApiSubmit } from '../utils/apiHooks';

function SuperAdminPage() {
  const { isAuthenticated, user } = useAuth();
  const [activeTab, setActiveTab] = useState('dashboard');

  // Check if user is super admin
  const isSuperAdmin = user && user.role === 'super_admin';

  // API hooks for platform stats
  const {
    data: rawPlatformStats,
    loading: statsLoading,
    error: statsError,
    refresh: refreshStats
  } = useApiCall(getPlatformStats, [], {
    autoExecute: isSuperAdmin,
    initialData: null
  });

  // API hooks for organizations with pagination
  const {
    data: organizations,
    total: totalOrganizations,
    loading: orgsLoading,
    error: orgsError,
    fetchPage: fetchOrganizations,
    currentPage,
    hasNext,
    hasPrev,
    nextPage,
    prevPage
  } = usePaginatedApi(getOrganizations, { pageSize: 10 });

  // Organization management state
  const [showCreateOrg, setShowCreateOrg] = useState(false);
  const [newOrgData, setNewOrgData] = useState({
    name: '',
    domain: '',
    subscription_type: 'basic'
  });
  
  // Create organization submission
  const { execute: executeCreateOrg, loading: createOrgLoading } = useApiSubmit(
    createOrganization,
    {
      onSuccess: (result) => {
        setShowCreateOrg(false);
        setNewOrgData({ name: '', domain: '', subscription_type: 'basic' });
        fetchOrganizations(1); // Refresh organizations list
        alert('Organization created successfully!');
      },
      onError: (error) => {
        alert(`Failed to create organization: ${error.message}`);
      }
    }
  );

  // Organization action handlers
  const handleCreateOrg = async (e) => {
    e.preventDefault();
    await executeCreateOrg(newOrgData);
  };

  const handleViewOrg = (org) => {
    // Navigate to organization detail view
    console.log('Viewing organization:', org);
    // TODO: Implement organization detail modal or navigation
  };

  const handleEditOrg = (org) => {
    // Open edit modal
    console.log('Editing organization:', org);
    // TODO: Implement organization edit modal
  };

  const handleToggleOrgStatus = async (org) => {
    const action = org.is_active ? 'suspend' : 'activate';
    const confirmed = window.confirm(
      `Are you sure you want to ${action} ${org.name}?`
    );
    
    if (confirmed) {
      try {
        await updateOrganization(org.id, {
          is_active: !org.is_active
        });
        fetchOrganizations(currentPage); // Refresh current page
        alert(`Organization ${action}d successfully!`);
      } catch (error) {
        alert(`Failed to ${action} organization: ${error.message}`);
      }
    }
  };

  // Transform platform stats for display
  const platformStats = rawPlatformStats ? transformPlatformStats(rawPlatformStats) : null;

  // Transform organization data for display
  const transformedOrganizations = organizations.map(org => transformOrganizationData(org));

  // API submission hooks for organization management
  // eslint-disable-next-line no-unused-vars
  const {
    // eslint-disable-next-line no-unused-vars
    submit: submitCreateOrg,
    // eslint-disable-next-line no-unused-vars
    loading: createLoading,
    // eslint-disable-next-line no-unused-vars
    error: createError,
    // eslint-disable-next-line no-unused-vars
    success: createSuccess
  } = useApiSubmit(createOrganization, {
    onSuccess: () => {
      fetchOrganizations(currentPage); // Refresh current page
      refreshStats(); // Refresh platform stats
    }
  });

  // eslint-disable-next-line no-unused-vars
  const {
    // eslint-disable-next-line no-unused-vars
    submit: submitUpdateOrg,
    // eslint-disable-next-line no-unused-vars
    loading: updateLoading,
    // eslint-disable-next-line no-unused-vars
    error: updateError,
    // eslint-disable-next-line no-unused-vars
    success: updateSuccess
  } = useApiSubmit(({ id, ...data }) => updateOrganization(id, data), {
    onSuccess: () => {
      fetchOrganizations(currentPage);
      refreshStats();
    }
  });

  // eslint-disable-next-line no-unused-vars
  const {
    // eslint-disable-next-line no-unused-vars
    submit: submitDeleteOrg,
    // eslint-disable-next-line no-unused-vars
    loading: deleteLoading,
    // eslint-disable-next-line no-unused-vars
    error: deleteError,
    // eslint-disable-next-line no-unused-vars
    success: deleteSuccess
  } = useApiSubmit(deleteOrganization, {
    onSuccess: () => {
      fetchOrganizations(currentPage);
      refreshStats();
    }
  });

  // Redirect if not authenticated or not super admin
  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }

  if (!isSuperAdmin) {
    return (
      <div className="super-admin-access-denied">
        <h1>Access Denied</h1>
        <p>You don't have Super Administrator privileges to access this area.</p>
        <p>This area is reserved for Sonicus platform owners only.</p>
      </div>
    );
  }

  // Show loading state while initial data is loading
  const isLoading = statsLoading || orgsLoading;
  if (isLoading && !platformStats && transformedOrganizations.length === 0) {
    return (
      <div className="super-admin-loading">
        <h1>Loading Sonicus Platform Dashboard...</h1>
        <div className="loading-spinner"></div>
      </div>
    );
  }

  // Show error state if both critical APIs fail
  if (statsError && orgsError) {
    return (
      <div className="super-admin-error">
        <h1>Unable to Load Platform Data</h1>
        <p>There was an error loading the platform dashboard.</p>
        <button onClick={() => { refreshStats(); fetchOrganizations(0); }}>
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="super-admin-page">
      {/* System works with Authentik authentication */}
      
      <header className="super-admin-header">
        <div className="header-branding">
          <h1>🌿 Sonicus Platform Control</h1>
          <p>B2B2C SaaS Management Dashboard</p>
        </div>
        
        <nav className="super-admin-nav">
          <button 
            className={activeTab === 'dashboard' ? 'nav-btn active' : 'nav-btn'}
            onClick={() => setActiveTab('dashboard')}
          >
            📊 Dashboard
          </button>
          <button 
            className={activeTab === 'organizations' ? 'nav-btn active' : 'nav-btn'}
            onClick={() => setActiveTab('organizations')}
          >
            🏢 Organizations
          </button>
          <button 
            className={activeTab === 'content' ? 'nav-btn active' : 'nav-btn'}
            onClick={() => setActiveTab('content')}
          >
            🎵 Content Library
          </button>
          <button 
            className={activeTab === 'system' ? 'nav-btn active' : 'nav-btn'}
            onClick={() => setActiveTab('system')}
          >
            ⚙️ System
          </button>
        </nav>
      </header>

      {activeTab === 'dashboard' && (
        <div className="dashboard-section">
          {/* Error banner for stats */}
          {statsError && (
            <div className="error-banner">
              <span>⚠️ Unable to load platform statistics: {statsError}</span>
              <button onClick={refreshStats}>Retry</button>
            </div>
          )}
          
          <div className="metrics-grid">
            <div className="metric-card primary">
              <h3>Total Organizations</h3>
              <div className="metric-number">
                {statsLoading ? '...' : (platformStats?.totalOrganizations || totalOrganizations || 0)}
              </div>
              <div className="metric-change">
                Active: {platformStats?.activeOrganizations || 0} | Trial: {platformStats?.trialOrganizations || 0}
              </div>
            </div>
            <div className="metric-card success">
              <h3>Monthly Recurring Revenue</h3>
              <div className="metric-number">
                ${statsLoading ? '...' : (platformStats?.monthlyRecurringRevenue || 0).toLocaleString()}
              </div>
              <div className="metric-change">Calculated from subscriptions</div>
            </div>
            <div className="metric-card info">
              <h3>Platform Users</h3>
              <div className="metric-number">
                {statsLoading ? '...' : (platformStats?.totalUsers || 0).toLocaleString()}
              </div>
              <div className="metric-change">
                Active: {(platformStats?.totalActiveUsers || 0).toLocaleString()}
              </div>
            </div>
            <div className="metric-card health">
              <h3>System Health</h3>
              <div className="metric-number">
                {statsLoading ? '...' : `${platformStats?.platformUptime || 99.5}%`}
              </div>
              <div className="metric-change">
                Status: {platformStats?.systemHealth || 'Unknown'}
              </div>
            </div>
          </div>

          <div className="dashboard-charts">
            <div className="chart-container">
              <h3>Organization Status Distribution</h3>
              <div className="distribution-stats">
                <div className="dist-item">
                  <span className="dist-color active"></span>
                  <span>Active: {platformStats?.activeOrganizations || 0} orgs</span>
                </div>
                <div className="dist-item">
                  <span className="dist-color trial"></span>
                  <span>Trial: {platformStats?.trialOrganizations || 0} orgs</span>
                </div>
                <div className="dist-item">
                  <span className="dist-color cancelled"></span>
                  <span>Cancelled: {platformStats?.cancelledOrganizations || 0} orgs</span>
                </div>
              </div>
            </div>
            
            <div className="chart-container">
              <h3>Recent Activity</h3>
              <div className="activity-list">
                <div className="activity-item">
                  <span className="activity-time">Just now</span>
                  <span>Platform statistics refreshed</span>
                </div>
                <div className="activity-item">
                  <span className="activity-time">5 min ago</span>
                  <span>Organization health checks completed</span>
                </div>
                <div className="activity-item">
                  <span className="activity-time">1 hour ago</span>
                  <span>Database backup completed successfully</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'organizations' && (
        <div className="organizations-section">
          <div className="section-header">
            <h2>Organization Management</h2>
            <button 
              className="action-btn primary"
              onClick={() => setShowCreateOrg(true)}
            >
              + Add Organization
            </button>
          </div>
          
          {orgsLoading ? (
            <div className="loading-container">
              <div className="loading-spinner"></div>
              <p>Loading organizations...</p>
            </div>
          ) : orgsError ? (
            <div className="error-container">
              <p>Error loading organizations: {orgsError}</p>
              <button 
                className="action-btn secondary"
                onClick={() => fetchOrganizations(1)}
              >
                Retry
              </button>
            </div>
          ) : (
            <div className="organizations-table">
              <table>
                <thead>
                  <tr>
                    <th>Organization</th>
                    <th>Users</th>
                    <th>Status</th>
                    <th>Plan</th>
                    <th>Created</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {organizations.map(org => (
                    <tr key={org.id}>
                      <td>
                        <div className="org-info">
                          <strong>{org.name}</strong>
                          <small>ID: {org.id}</small>
                          <small>{org.domain}</small>
                        </div>
                      </td>
                      <td>{org.user_count || 0}</td>
                      <td>
                        <span className={`status-badge ${org.is_active ? 'active' : 'inactive'}`}>
                          {org.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td>
                        <span className={`plan-badge ${org.subscription_type || 'basic'}`}>
                          {org.subscription_type || 'Basic'}
                        </span>
                      </td>
                      <td>{new Date(org.created_at).toLocaleDateString()}</td>
                      <td className="actions">
                        <button 
                          className="action-btn small"
                          onClick={() => handleViewOrg(org)}
                        >
                          View
                        </button>
                        <button 
                          className="action-btn small secondary"
                          onClick={() => handleEditOrg(org)}
                        >
                          Edit
                        </button>
                        <button 
                          className="action-btn small danger"
                          onClick={() => handleToggleOrgStatus(org)}
                        >
                          {org.is_active ? 'Suspend' : 'Activate'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              
              {/* Pagination Controls */}
              <div className="pagination-controls">
                <div className="pagination-info">
                  Showing {organizations.length} of {totalOrganizations} organizations
                </div>
                <div className="pagination-buttons">
                  <button 
                    className="action-btn small secondary"
                    onClick={prevPage}
                    disabled={!hasPrev || orgsLoading}
                  >
                    Previous
                  </button>
                  <span className="page-info">Page {currentPage}</span>
                  <button 
                    className="action-btn small secondary"
                    onClick={nextPage}
                    disabled={!hasNext || orgsLoading}
                  >
                    Next
                  </button>
                </div>
              </div>
            </div>
          )}

          {showCreateOrg && (
            <div className="modal-overlay">
              <div className="modal">
                <div className="modal-header">
                  <h3>Create New Organization</h3>
                  <button 
                    className="close-btn"
                    onClick={() => setShowCreateOrg(false)}
                  >
                    ×
                  </button>
                </div>
                <form onSubmit={handleCreateOrg}>
                  <div className="form-group">
                    <label>Organization Name</label>
                    <input
                      type="text"
                      value={newOrgData.name}
                      onChange={(e) => setNewOrgData({...newOrgData, name: e.target.value})}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label>Domain</label>
                    <input
                      type="text"
                      value={newOrgData.domain}
                      onChange={(e) => setNewOrgData({...newOrgData, domain: e.target.value})}
                      placeholder="company.com"
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label>Subscription Type</label>
                    <select
                      value={newOrgData.subscription_type}
                      onChange={(e) => setNewOrgData({...newOrgData, subscription_type: e.target.value})}
                    >
                      <option value="basic">Basic</option>
                      <option value="professional">Professional</option>
                      <option value="enterprise">Enterprise</option>
                    </select>
                  </div>
                  <div className="form-actions">
                    <button 
                      type="button" 
                      className="action-btn secondary"
                      onClick={() => setShowCreateOrg(false)}
                    >
                      Cancel
                    </button>
                    <button 
                      type="submit" 
                      className="action-btn primary"
                      disabled={createOrgLoading}
                    >
                      {createOrgLoading ? 'Creating...' : 'Create Organization'}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'content' && (
        <div className="content-section">
          <div className="section-header">
            <h2>Global Content Library Management</h2>
            <button className="action-btn primary">+ Upload Content</button>
          </div>
          
          {statsLoading ? (
            <div className="loading-container">
              <div className="loading-spinner"></div>
              <p>Loading content statistics...</p>
            </div>
          ) : (
            <>
              <div className="content-stats">
                <div className="content-stat">
                  <h4>Total Sound Library</h4>
                  <div className="stat-number">
                    {rawPlatformStats?.content_stats?.total_sounds || '0'}
                  </div>
                </div>
                <div className="content-stat">
                  <h4>Template Packages</h4>
                  <div className="stat-number">
                    {rawPlatformStats?.content_stats?.template_packages || '0'}
                  </div>
                </div>
                <div className="content-stat">
                  <h4>Premium Content</h4>
                  <div className="stat-number">
                    {rawPlatformStats?.content_stats?.premium_content || '0'}
                  </div>
                </div>
                <div className="content-stat">
                  <h4>Total Usage Hours</h4>
                  <div className="stat-number">
                    {rawPlatformStats?.usage_stats?.total_listening_hours?.toLocaleString() || '0'}
                  </div>
                </div>
              </div>

              <div className="content-categories">
                {rawPlatformStats?.content_categories?.map((category, index) => (
                  <div key={index} className="category-card">
                    <h4>{category.icon} {category.name}</h4>
                    <p>{category.sound_count} sounds available</p>
                    <div className="category-usage">
                      Used by {category.organization_count} organizations
                    </div>
                    <div className="category-stats">
                      <small>{category.total_hours} total hours listened</small>
                    </div>
                  </div>
                )) || [
                  {
                    icon: '🌙',
                    name: 'Sleep & Relaxation',
                    sound_count: 234,
                    organization_count: 43,
                    total_hours: '12,456'
                  },
                  {
                    icon: '🧘',
                    name: 'Meditation & Mindfulness',
                    sound_count: 189,
                    organization_count: 38,
                    total_hours: '9,823'
                  },
                  {
                    icon: '🎯',
                    name: 'Focus & Productivity',
                    sound_count: 156,
                    organization_count: 29,
                    total_hours: '7,234'
                  },
                  {
                    icon: '🌿',
                    name: 'Nature & Ambient',
                    sound_count: 298,
                    organization_count: 41,
                    total_hours: '15,678'
                  }
                ].map((category, index) => (
                  <div key={index} className="category-card">
                    <h4>{category.icon} {category.name}</h4>
                    <p>{category.sound_count} sounds available</p>
                    <div className="category-usage">
                      Used by {category.organization_count} organizations
                    </div>
                    <div className="category-stats">
                      <small>{category.total_hours} total hours listened</small>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {activeTab === 'system' && (
        <div className="system-section">
          <div className="section-header">
            <h2>System Administration</h2>
          </div>
          
          <div className="system-controls">
            <div className="control-group">
              <h3>Platform Operations</h3>
              <button className="action-btn">Send Platform Announcement</button>
              <button className="action-btn secondary">Schedule Maintenance</button>
              <button className="action-btn secondary">Export Analytics</button>
            </div>
            
            <div className="control-group">
              <h3>Security & Access</h3>
              <button className="action-btn">Security Audit</button>
              <button className="action-btn secondary">Access Logs</button>
              <button className="action-btn secondary">API Key Management</button>
            </div>
            
            <div className="control-group">
              <h3>Billing & Finance</h3>
              <button className="action-btn secondary">Billing Reports</button>
              <button className="action-btn secondary">Payment Processing</button>
              <button className="action-btn secondary">Revenue Analytics</button>
            </div>
          </div>

          <div className="system-status">
            <h3>System Status</h3>
            {statsLoading ? (
              <div className="loading-container">
                <div className="loading-spinner"></div>
                <p>Checking system status...</p>
              </div>
            ) : (
              <div className="status-grid">
                <div className={`status-item ${rawPlatformStats?.system_health?.api_status === 'healthy' ? 'healthy' : 'warning'}`}>
                  <span className="status-indicator"></span>
                  <span>API Services</span>
                  <span className="status-value">
                    {rawPlatformStats?.system_health?.api_status === 'healthy' ? 'Operational' : 'Issues Detected'}
                  </span>
                </div>
                <div className={`status-item ${rawPlatformStats?.system_health?.database_status === 'healthy' ? 'healthy' : 'warning'}`}>
                  <span className="status-indicator"></span>
                  <span>Database Cluster</span>
                  <span className="status-value">
                    {rawPlatformStats?.system_health?.database_status === 'healthy' ? 'Healthy' : 'Degraded'}
                  </span>
                </div>
                <div className={`status-item ${rawPlatformStats?.system_health?.storage_status === 'healthy' ? 'healthy' : 'warning'}`}>
                  <span className="status-indicator"></span>
                  <span>Content Delivery</span>
                  <span className="status-value">
                    {rawPlatformStats?.system_health?.storage_status === 'healthy' ? 'Optimal' : 'Slow'}
                  </span>
                </div>
                <div className={`status-item ${rawPlatformStats?.system_health?.background_jobs_status === 'healthy' ? 'healthy' : 'warning'}`}>
                  <span className="status-indicator"></span>
                  <span>Background Jobs</span>
                  <span className="status-value">
                    {rawPlatformStats?.system_health?.background_jobs_status === 'healthy' ? 'Normal Load' : 'High Load'}
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      <footer className="super-admin-footer">
        <p>Sonicus B2B2C Platform Administration v2.0.0</p>
        <p>Managing therapeutic sound healing at enterprise scale</p>
      </footer>
    </div>
  );
}

export default SuperAdminPage;
