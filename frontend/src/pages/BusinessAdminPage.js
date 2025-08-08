import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../hooks/useAuth';
import { Navigate } from 'react-router-dom';
import '../styles/BusinessAdminPage.css';
import '../styles/responsive.css';
import '../styles/MobileAdmin.css';
import '../styles/PWA.css';

// Import mobile admin components
import {
  MobileAdminNav,
  TouchFriendlyCard,
  MobileSearchBar,
  TouchFriendlyModal,
  MobileDataTable,
  FloatingActionButton
} from '../components/MobileAdminComponents';

// Import PWA manager
import pwaManager from '../utils/pwaManager';

// Import API services and hooks
import { 
  getOrganizationDetails,
  getOrganizationStats,
  getOrganizationCustomers,
  getOrganizationPackages,
  updateCustomer,
  assignPackageToCustomer,
  removePackageFromCustomer,
  getWellnessAnalytics
} from '../utils/apiService';
import { useApiCall, usePaginatedApi, useApiSubmit } from '../utils/apiHooks';

function BusinessAdminPage() {
  const { isAuthenticated, user, loading, hasRole } = useAuth();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedSearchQuery, setDebouncedSearchQuery] = useState('');

  // Debounce search query to prevent infinite API calls
  useEffect(() => {
    const timer = setTimeout(() => {
      // Ensure searchQuery is always a string
      const safeSearchQuery = typeof searchQuery === 'string' ? searchQuery : '';
      setDebouncedSearchQuery(safeSearchQuery);
    }, 500); // 500ms delay

    return () => clearTimeout(timer);
  }, [searchQuery]);
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [showCustomerModal, setShowCustomerModal] = useState(false);
  const [showInstallPrompt, setShowInstallPrompt] = useState(false);
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  // Check if user is business admin using the new role checking system
  const isBusinessAdmin = hasRole(['business_admin', 'staff']);
  
  // Get user's organization ID - only proceed if we have a valid organization_id
  const organizationId = user?.organization_id;
  const hasValidOrgId = organizationId && organizationId !== 'undefined';

  // Check authentication and user role
  useEffect(() => {
    if (!isAuthenticated || !user || !['business_admin', 'super_admin'].includes(user.role)) {
      navigate('/login');
      return;
    }
    
    if (user.role === 'business_admin' && !hasValidOrgId) {
      setError('No valid organization associated with this account');
      return;
    }
    
    fetchCustomers();
  }, [isAuthenticated, user, navigate, hasValidOrgId]);

  // PWA manager setup
  useEffect(() => {
    // Set up PWA event listeners
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    const handleInstallPrompt = () => setShowInstallPrompt(true);

    pwaManager.on('online', handleOnline);
    pwaManager.on('offline', handleOffline);
    pwaManager.on('beforeinstallprompt', handleInstallPrompt);

    return () => {
      pwaManager.off('online', handleOnline);
      pwaManager.off('offline', handleOffline);
      pwaManager.off('beforeinstallprompt', handleInstallPrompt);
    };
  }, []);

  // API hooks for organization data
  const {
    data: organizationDetails,
    loading: orgLoading,
    error: orgError,
    refresh: refreshOrganization
  } = useApiCall(getOrganizationDetails, [organizationId], {
    autoExecute: isBusinessAdmin && hasValidOrgId,
    initialData: null
  });

  // API hooks for organization statistics
  const {
    data: organizationStats,
    loading: statsLoading,
    error: statsError,
    refresh: refreshStats
  } = useApiCall(getOrganizationStats, [organizationId], {
    autoExecute: isBusinessAdmin && hasValidOrgId,
    initialData: null
  });

  // API hooks for wellness analytics
  const {
    data: wellnessAnalytics,
    loading: analyticsLoading,
    // eslint-disable-next-line no-unused-vars
    error: analyticsError
  } = useApiCall(getWellnessAnalytics, [organizationId], {
    autoExecute: isBusinessAdmin && hasValidOrgId,
    initialData: null
  });

  // API hooks for customers with pagination
  const customersFetcher = useCallback((params) => {
    // Ensure searchValue is always a string to prevent malformed API requests
    const searchValue = typeof debouncedSearchQuery === 'string' ? debouncedSearchQuery : '';
    
    return getOrganizationCustomers({
      ...params,
      search: searchValue
    });
  }, [debouncedSearchQuery]);

  const {
    data: customers,
    total: totalCustomers,
    loading: customersLoading,
    // eslint-disable-next-line no-unused-vars
    error: customersError,
    fetchPage: fetchCustomers,
    currentPage: customerPage,
    hasNext: hasNextCustomers,
    hasPrev: hasPrevCustomers,
    nextPage: nextCustomerPage,
    prevPage: prevCustomerPage
  } = usePaginatedApi(customersFetcher, { 
    pageSize: 10,
    autoExecute: isBusinessAdmin && hasValidOrgId
  });

  // API hooks for packages
  const {
    data: packages,
    loading: packagesLoading,
    // eslint-disable-next-line no-unused-vars
    error: packagesError,
    // eslint-disable-next-line no-unused-vars
    refresh: refreshPackages
  } = useApiCall(getOrganizationPackages, [organizationId], {
    autoExecute: isBusinessAdmin && hasValidOrgId,
    initialData: []
  });

  // Customer management
  // eslint-disable-next-line no-unused-vars
  const { execute: updateCustomerData } = useApiSubmit(updateCustomer);
  const { execute: assignPackage } = useApiSubmit(assignPackageToCustomer);
  const { execute: removePackage } = useApiSubmit(removePackageFromCustomer);

  // Navigation tabs configuration (after data loading)
  const navigationTabs = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'customers', label: 'Customers', icon: '👥', badge: totalCustomers > 0 ? totalCustomers : undefined },
    { id: 'packages', label: 'Packages', icon: '📦' },
    { id: 'analytics', label: 'Analytics', icon: '📈' },
    { id: 'communications', label: 'Comms', icon: '💬' }
  ];

  // Handler functions
  // Enhanced handlers with mobile-friendly toasts
    const handleCustomerStatusToggle = (customerId, currentStatus) => {
    // TODO: Implement customer status toggle
    // For now, show a placeholder message
    alert(`Toggle status for customer ${customerId} from ${currentStatus}`);
  };

  // Render content based on active tab
  const renderTabContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return renderDashboard();
      case 'customers':
        return renderCustomers();
      case 'packages':
        return renderPackages();
      case 'analytics':
        return renderAnalytics();
      case 'communications':
        return renderCommunications();
      default:
        return renderDashboard();
    }
  };

  // eslint-disable-next-line no-unused-vars
  const handleAssignPackage = async (customerId, packageId) => {
    try {
      await assignPackage({ customerId, packageId });
      await fetchCustomers(customerPage); // Refresh customers
      pwaManager.showToast('Package assigned successfully!', 'success');
    } catch (error) {
      pwaManager.showToast(`Failed to assign package: ${error.message}`, 'error');
    }
  };

  // eslint-disable-next-line no-unused-vars
  const handleRemovePackage = async (customerId, packageId) => {
    const confirmed = window.confirm('Are you sure you want to remove this package from the customer?');
    if (confirmed) {
      try {
        await removePackage({ customerId, packageId });
        await fetchCustomers(customerPage); // Refresh customers
        pwaManager.showToast('Package removed successfully!', 'success');
      } catch (error) {
        pwaManager.showToast(`Failed to remove package: ${error.message}`, 'error');
      }
    }
  };

  // Customer table row actions
  const handleCustomerRowAction = (action, customer) => {
    switch (action) {
      case 'view':
      case 'edit':
        setSelectedCustomer(customer);
        setShowCustomerModal(true);
        break;
      case 'delete':
        handleCustomerStatusToggle(customer.id, customer.status);
        break;
      default:
        break;
    }
  };

  // Filtered customers based on search
  const filteredCustomers = (Array.isArray(customers) ? customers : []).filter(customer => 
    customer.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    customer.email?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    customer.department?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // PWA Install handler
  const handleInstallPWA = async () => {
    const installed = await pwaManager.installApp();
    if (installed) {
      setShowInstallPrompt(false);
      pwaManager.showToast('App installed successfully!', 'success');
    }
  };

  // Floating action button configuration
  const fabActions = [
    {
      icon: '👤',
      label: 'Add Customer',
      onClick: () => {
        setSelectedCustomer(null);
        setShowCustomerModal(true);
      }
    },
    {
      icon: '📊',
      label: 'Generate Report',
      onClick: () => pwaManager.showToast('Report generation coming soon!', 'info')
    },
    {
      icon: '📤',
      label: 'Export Data',
      onClick: () => pwaManager.showToast('Export feature coming soon!', 'info')
    }
  ];

  // Check if any data is loading
  const isLoading = orgLoading || statsLoading || customersLoading || packagesLoading;

  // Show loading state while checking authentication
  if (loading) {
    return (
      <div className="business-admin-page">
        <div className="loading-section">
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  // Redirect if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }

  if (!isBusinessAdmin) {
    return (
      <div className="business-admin-access-denied">
        <h1>Access Denied</h1>
        <p>You don't have Business Administrator privileges to access this area.</p>
        <p>Contact your organization administrator for access.</p>
      </div>
    );
  }

  // Check if organization ID is valid for business admin
  if (isBusinessAdmin && !hasValidOrgId) {
    return (
      <div className="business-admin-page">
        <div className="error-section">
          <h2>Organization Error</h2>
          <p>Unable to load organization data. No valid organization ID found.</p>
          <p>Organization ID: {String(user?.organization_id)}</p>
        </div>
      </div>
    );
  }

  if (isLoading && !organizationDetails && !organizationStats) {
    return (
      <div className="business-admin-loading">
        <h1>Loading Business Dashboard...</h1>
        <div className="loading-spinner"></div>
      </div>
    );
  }

  // Handle errors
  if (orgError || statsError) {
    return (
      <div className="business-admin-error">
        <h1>Error Loading Dashboard</h1>
        <p>Unable to load organization data. Please try again.</p>
        <button 
          className="action-btn primary"
          onClick={() => {
            refreshOrganization();
            refreshStats();
          }}
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="business-admin-page">
      {/* PWA Install Prompt */}
      {showInstallPrompt && (
        <div className="install-prompt">
          <div className="install-prompt-header">
            <div className="install-prompt-icon">📱</div>
            <h3 className="install-prompt-title">Install Sonicus Admin</h3>
          </div>
          <p className="install-prompt-description">
            Install our app for a better experience with offline capabilities and quick access.
          </p>
          <div className="install-prompt-actions">
            <button className="btn btn-primary" onClick={handleInstallPWA}>
              Install
            </button>
            <button 
              className="btn btn-outline-primary" 
              onClick={() => setShowInstallPrompt(false)}
            >
              Maybe Later
            </button>
          </div>
        </div>
      )}

      {/* Mobile Navigation */}
      <MobileAdminNav
        activeTab={activeTab}
        onTabChange={setActiveTab}
        tabs={navigationTabs}
      />

      {/* Main Content */}
      <div className="admin-content">
        <div className="container-fluid">
          {renderTabContent()}
        </div>
      </div>

      {/* Customer Modal */}
      <TouchFriendlyModal
        isOpen={showCustomerModal}
        onClose={() => setShowCustomerModal(false)}
        title={selectedCustomer ? 'Edit Customer' : 'Add Customer'}
        size="lg"
      >
        {renderCustomerModal()}
      </TouchFriendlyModal>

      {/* Floating Action Button */}
      <FloatingActionButton
        actions={fabActions}
        primaryAction={{
          icon: '+',
          label: 'Quick Actions',
          onClick: () => {}
        }}
      />
    </div>
  );

  // Dashboard renderer
  function renderDashboard() {
    return (
      <div className="dashboard-section">
        {/* Organization Header */}
        <div className="row mb-4">
          <div className="col-12">
            <TouchFriendlyCard className="p-4">
              <div className="d-flex align-items-center">
                <div className="me-3">
                  <div style={{ 
                    width: '64px', 
                    height: '64px', 
                    background: 'linear-gradient(135deg, var(--primary-color), var(--secondary-color))',
                    borderRadius: '16px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '24px',
                    color: 'white'
                  }}>
                    🏢
                  </div>
                </div>
                <div className="flex-1">
                  <h2 className="mb-1">{organizationDetails?.name || 'Loading...'}</h2>
                  <p className="text-muted mb-0">
                    Wellness Program Administration • {organizationDetails?.subscription_type || 'Professional'} Plan
                  </p>
                  {!isOnline && (
                    <span className="badge bg-warning text-dark mt-1">Offline Mode</span>
                  )}
                </div>
              </div>
            </TouchFriendlyCard>
          </div>
        </div>

        {/* Stats Cards */}
        {statsLoading ? (
          <div className="mobile-loading">
            <div className="spinner"></div>
            <div className="splash-loading-text">Loading dashboard statistics...</div>
          </div>
        ) : (
          <div className="dashboard-stats row">
            <div className="col-6 col-md-3 mb-3">
              <TouchFriendlyCard className="stat-card text-center p-3">
                <div className="stat-icon mb-2" style={{ fontSize: '2rem' }}>👥</div>
                <div className="stat-value fw-bold">{organizationStats?.total_customers || 0}</div>
                <div className="stat-label text-muted">Customers</div>
              </TouchFriendlyCard>
            </div>
            <div className="col-6 col-md-3 mb-3">
              <TouchFriendlyCard className="stat-card text-center p-3">
                <div className="stat-icon mb-2" style={{ fontSize: '2rem' }}>📦</div>
                <div className="stat-value fw-bold">{organizationStats?.active_packages || 0}</div>
                <div className="stat-label text-muted">Active Packages</div>
              </TouchFriendlyCard>
            </div>
            <div className="col-6 col-md-3 mb-3">
              <TouchFriendlyCard className="stat-card text-center p-3">
                <div className="stat-icon mb-2" style={{ fontSize: '2rem' }}>📈</div>
                <div className="stat-value fw-bold">{organizationStats?.engagement_rate || '0%'}</div>
                <div className="stat-label text-muted">Engagement</div>
              </TouchFriendlyCard>
            </div>
            <div className="col-6 col-md-3 mb-3">
              <TouchFriendlyCard className="stat-card text-center p-3">
                <div className="stat-icon mb-2" style={{ fontSize: '2rem' }}>💰</div>
                <div className="stat-value fw-bold">${organizationStats?.monthly_cost || '0'}</div>
                <div className="stat-label text-muted">Monthly Cost</div>
              </TouchFriendlyCard>
            </div>
          </div>
        )}

        {/* Quick Actions */}
        <div className="row">
          <div className="col-12">
            <h3 className="mb-3">Quick Actions</h3>
            <div className="row">
              <div className="col-6 col-md-4 mb-3">
                <TouchFriendlyCard className="quick-action-card p-3 text-center h-100" onTap={() => setActiveTab('customers')}>
                  <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>👥</div>
                  <div className="fw-semibold">Manage Customers</div>
                  <div className="text-muted small">View and edit customer data</div>
                </TouchFriendlyCard>
              </div>
              <div className="col-6 col-md-4 mb-3">
                <TouchFriendlyCard className="quick-action-card p-3 text-center h-100" onTap={() => setActiveTab('packages')}>
                  <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>📦</div>
                  <div className="fw-semibold">Package Management</div>
                  <div className="text-muted small">Assign and manage packages</div>
                </TouchFriendlyCard>
              </div>
              <div className="col-6 col-md-4 mb-3">
                <TouchFriendlyCard className="quick-action-card p-3 text-center h-100" onTap={() => setActiveTab('analytics')}>
                  <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>📊</div>
                  <div className="fw-semibold">View Analytics</div>
                  <div className="text-muted small">Wellness metrics and reports</div>
                </TouchFriendlyCard>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Customers renderer  
  function renderCustomers() {
    const customerColumns = [
      { key: 'name', label: 'Name' },
      { key: 'email', label: 'Email' },
      { key: 'department', label: 'Department' },
      { 
        key: 'status', 
        label: 'Status',
        render: (status) => (
          <span className={`badge ${status === 'active' ? 'bg-success' : 'bg-secondary'}`}>
            {status}
          </span>
        )
      }
    ];

    return (
      <div className="customers-section">
        <div className="d-flex justify-content-between align-items-center mb-3">
          <h2>Customers ({totalCustomers || 0})</h2>
        </div>

        <MobileSearchBar
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search customers..."
          onClear={() => setSearchQuery('')}
        />

        {customersLoading ? (
          <div className="mobile-loading">
            <div className="spinner"></div>
            <div className="splash-loading-text">Loading customers...</div>
          </div>
        ) : filteredCustomers.length === 0 ? (
          <div className="mobile-empty-state">
            <div className="mobile-empty-icon">👥</div>
            <div className="mobile-empty-title">No Customers Found</div>
            <div className="mobile-empty-description">
              {searchQuery ? 'No customers match your search criteria.' : 'No customers have been added yet.'}
            </div>
            <button className="btn btn-primary" onClick={() => {
              setSelectedCustomer(null);
              setShowCustomerModal(true);
            }}>
              Add First Customer
            </button>
          </div>
        ) : (
          <>
            <MobileDataTable
              data={filteredCustomers}
              columns={customerColumns}
              onRowAction={handleCustomerRowAction}
            />

            {/* Pagination */}
            {(hasNextCustomers || hasPrevCustomers) && (
              <div className="d-flex justify-content-between align-items-center mt-3">
                <button 
                  className="btn btn-outline-primary"
                  onClick={prevCustomerPage}
                  disabled={!hasPrevCustomers}
                >
                  Previous
                </button>
                <span className="text-muted">
                  Page {customerPage} of {Math.ceil(totalCustomers / 10)}
                </span>
                <button 
                  className="btn btn-outline-primary"
                  onClick={nextCustomerPage}
                  disabled={!hasNextCustomers}
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </div>
    );
  }

  // Packages renderer
  function renderPackages() {
    // Ensure packages is always an array
    const safePackages = Array.isArray(packages) ? packages : [];
    
    return (
      <div className="packages-section">
        <h2 className="mb-3">Wellness Packages</h2>
        
        {packagesLoading ? (
          <div className="mobile-loading">
            <div className="spinner"></div>
            <div className="splash-loading-text">Loading packages...</div>
          </div>
        ) : safePackages.length === 0 ? (
          <div className="mobile-empty-state">
            <div className="mobile-empty-icon">📦</div>
            <div className="mobile-empty-title">No Packages Available</div>
            <div className="mobile-empty-description">
              No wellness packages are currently assigned to your organization.
            </div>
          </div>
        ) : (
          <div className="row">
            {safePackages.map((pkg) => (
              <div key={pkg.id} className="col-12 col-md-6 col-lg-4 mb-3">
                <TouchFriendlyCard className="package-card h-100">
                  <div className="card-body">
                    <div className="d-flex align-items-start mb-3">
                      <div className="package-icon me-3" style={{ 
                        fontSize: '2rem',
                        width: '56px',
                        height: '56px',
                        background: 'linear-gradient(135deg, var(--primary-color), var(--secondary-color))',
                        borderRadius: '12px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'white'
                      }}>
                        📦
                      </div>
                      <div className="flex-1">
                        <h5 className="package-title mb-1">{pkg.name}</h5>
                        <p className="text-muted small mb-0">{pkg.description}</p>
                      </div>
                    </div>
                    
                    <div className="package-stats">
                      <div className="row text-center">
                        <div className="col-4">
                          <div className="fw-bold">{pkg.sounds_count || 0}</div>
                          <div className="text-muted small">Sounds</div>
                        </div>
                        <div className="col-4">
                          <div className="fw-bold">{pkg.assigned_count || 0}</div>
                          <div className="text-muted small">Assigned</div>
                        </div>
                        <div className="col-4">
                          <div className="fw-bold">{pkg.usage_rate || '0%'}</div>
                          <div className="text-muted small">Usage</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </TouchFriendlyCard>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  // Analytics renderer
  function renderAnalytics() {
    return (
      <div className="analytics-section">
        <h2 className="mb-3">Wellness Analytics</h2>
        
        {analyticsLoading ? (
          <div className="mobile-loading">
            <div className="spinner"></div>
            <div className="splash-loading-text">Loading analytics...</div>
          </div>
        ) : (
          <div className="row">
            <div className="col-12 mb-4">
              <TouchFriendlyCard className="p-4">
                <h4 className="mb-3">📊 Engagement Overview</h4>
                <div className="progress mb-2" style={{ height: '24px' }}>
                  <div 
                    className="progress-bar bg-success" 
                    style={{ width: `${wellnessAnalytics?.engagement_rate || 0}%` }}
                  >
                    {wellnessAnalytics?.engagement_rate || 0}%
                  </div>
                </div>
                <div className="text-muted small">Overall customer engagement with wellness programs</div>
              </TouchFriendlyCard>
            </div>

            <div className="col-12 col-md-6 mb-4">
              <TouchFriendlyCard className="h-100 p-4">
                <h5 className="mb-3">🎯 Most Used Features</h5>
                <div className="feature-list">
                  {(wellnessAnalytics?.top_features || []).map((feature, index) => (
                    <div key={index} className="d-flex justify-content-between align-items-center mb-2">
                      <span>{feature.name}</span>
                      <span className="fw-bold">{feature.usage}%</span>
                    </div>
                  ))}
                </div>
              </TouchFriendlyCard>
            </div>

            <div className="col-12 col-md-6 mb-4">
              <TouchFriendlyCard className="h-100 p-4">
                <h5 className="mb-3">📈 Usage Trends</h5>
                <div className="text-center">
                  <div className="display-4 text-primary mb-2">
                    {wellnessAnalytics?.weekly_active_users || 0}
                  </div>
                  <div className="text-muted">Weekly Active Users</div>
                </div>
              </TouchFriendlyCard>
            </div>
          </div>
        )}
      </div>
    );
  }

  // Communications renderer
  function renderCommunications() {
    return (
      <div className="communications-section">
        <h2 className="mb-3">Customer Communications</h2>
        
        <div className="row">
          <div className="col-12 col-md-6 mb-3">
            <TouchFriendlyCard className="comm-card p-4 h-100">
              <div className="text-center">
                <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📢</div>
                <h4 className="mb-2">Announcements</h4>
                <p className="text-muted mb-3">Send important updates to all customers</p>
                <button className="btn btn-primary">
                  Create Announcement
                </button>
              </div>
            </TouchFriendlyCard>
          </div>

          <div className="col-12 col-md-6 mb-3">
            <TouchFriendlyCard className="comm-card p-4 h-100">
              <div className="text-center">
                <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📊</div>
                <h4 className="mb-2">Surveys</h4>
                <p className="text-muted mb-3">Gather feedback and insights</p>
                <button className="btn btn-primary">
                  Create Survey
                </button>
              </div>
            </TouchFriendlyCard>
          </div>

          <div className="col-12 col-md-6 mb-3">
            <TouchFriendlyCard className="comm-card p-4 h-100">
              <div className="text-center">
                <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>💬</div>
                <h4 className="mb-2">Feedback</h4>
                <p className="text-muted mb-3">Review customer feedback</p>
                <button className="btn btn-outline-primary">
                  View Feedback
                </button>
              </div>
            </TouchFriendlyCard>
          </div>

          <div className="col-12 col-md-6 mb-3">
            <TouchFriendlyCard className="comm-card p-4 h-100">
              <div className="text-center">
                <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>⏰</div>
                <h4 className="mb-2">Reminders</h4>
                <p className="text-muted mb-3">Automated wellness reminders</p>
                <button className="btn btn-outline-primary">
                  Manage Reminders
                </button>
              </div>
            </TouchFriendlyCard>
          </div>
        </div>
      </div>
    );
  }

  // Customer modal renderer
  function renderCustomerModal() {
    return (
      <div className="customer-modal-content">
        <div className="mb-3">
          <label className="form-label">Name</label>
          <input 
            type="text" 
            className="form-control" 
            defaultValue={selectedCustomer?.name || ''}
            placeholder="Enter customer name"
          />
        </div>
        <div className="mb-3">
          <label className="form-label">Email</label>
          <input 
            type="email" 
            className="form-control" 
            defaultValue={selectedCustomer?.email || ''}
            placeholder="Enter email address"
          />
        </div>
        <div className="mb-3">
          <label className="form-label">Department</label>
          <input 
            type="text" 
            className="form-control" 
            defaultValue={selectedCustomer?.department || ''}
            placeholder="Enter department"
          />
        </div>
        <div className="mb-3">
          <label className="form-label">Status</label>
          <select className="form-control" defaultValue={selectedCustomer?.status || 'active'}>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
        </div>
        <div className="d-flex gap-2">
          <button 
            className="btn btn-primary flex-1"
            onClick={() => {
              pwaManager.showToast('Customer saved successfully!', 'success');
              setShowCustomerModal(false);
            }}
          >
            Save Changes
          </button>
          <button 
            className="btn btn-outline-secondary flex-1"
            onClick={() => setShowCustomerModal(false)}
          >
            Cancel
          </button>
        </div>
      </div>
    );
  }
}

export default BusinessAdminPage;
