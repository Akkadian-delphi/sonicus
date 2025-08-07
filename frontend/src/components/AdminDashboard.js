import React, { useState, useEffect, useCallback, useRef } from 'react';
import axios from '../utils/axios';
import './AdminDashboard.css';

const AdminDashboard = () => {
  // Dashboard data states - updated to use new API structure
  const [dashboardData, setDashboardData] = useState({
    platformStats: null,
    revenueAnalytics: null,
    growthTrends: null,
    systemHealth: null,
    systemAlerts: null
  });
  
  // Legacy states for backward compatibility
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [sounds, setSounds] = useState([]);
  
  const [selectedTab, setSelectedTab] = useState('dashboard');
  const [loading, setLoading] = useState({
    dashboard: false,
    users: false,
    sounds: false,
    refreshing: false
  });
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  // Real-time features
  const [wsConnected, setWsConnected] = useState(false);
  // eslint-disable-next-line no-unused-vars
  const [userActivity, setUserActivity] = useState([]);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [timeRange, setTimeRange] = useState('30d');
  const wsRef = useRef(null);
  const refreshTimerRef = useRef(null);

  // Pagination states
  // eslint-disable-next-line no-unused-vars
  const [userPage, setUserPage] = useState(0);
  const [userFilter, setUserFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  // Handle real-time data updates from WebSocket
  const handleRealTimeUpdate = useCallback((data) => {
    const { type, data: payload } = data;
    
    switch (type) {
      case 'dashboard_update':
        if (payload.platform_stats) {
          setDashboardData(prev => ({
            ...prev,
            platformStats: payload.platform_stats
          }));
          // Update legacy stats for backward compatibility
          setStats({
            total_users: payload.platform_stats.total_users,
            trial_users: payload.platform_stats.active_users * 0.3, // Mock
            paid_subscribers: payload.platform_stats.active_users * 0.7, // Mock
            expired_users: payload.platform_stats.total_users - payload.platform_stats.active_users,
            total_sounds: payload.platform_stats.total_sounds,
            new_users_this_month: payload.platform_stats.total_users * 0.1, // Mock
            revenue_this_month: payload.platform_stats.monthly_revenue,
            user_engagement: payload.platform_stats.user_engagement || 0,
            system_health: payload.platform_stats.system_health || 100
          });
        }
        break;
      case 'user_activity':
        if (payload.user_data) {
          setUserActivity(prev => [payload.user_data, ...prev.slice(0, 49)]);
        }
        break;
      case 'error_alert':
        console.error('Dashboard Error Alert:', payload);
        break;
      default:
        console.log('Unknown WebSocket message type:', type);
    }
  }, []);

  // Initialize WebSocket connection for real-time updates
  const initializeWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('authToken');
      const wsUrl = `ws://localhost:18100/ws/admin/dashboard?token=${token}`;
      
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onopen = () => {
        console.log('Admin Dashboard WebSocket connected');
        setWsConnected(true);
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleRealTimeUpdate(data);
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      wsRef.current.onclose = () => {
        console.log('Admin Dashboard WebSocket disconnected');
        setWsConnected(false);
        // Attempt to reconnect after 5 seconds
        setTimeout(initializeWebSocket, 5000);
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setWsConnected(false);
      };
    } catch (err) {
      console.error('Failed to initialize WebSocket:', err);
      setWsConnected(false);
    }
  }, [handleRealTimeUpdate]);

  // Load dashboard data using new comprehensive API
  const loadDashboardData = useCallback(async () => {
    try {
      setLoading(prev => ({ ...prev, dashboard: true }));
      
      // Load new dashboard metrics
      const [statsRes, revenueRes, growthRes, healthRes, alertsRes] = await Promise.allSettled([
        axios.get('/super-admin/dashboard/stats', { params: { time_range: timeRange } }),
        axios.get('/super-admin/dashboard/revenue', { params: { time_range: timeRange } }),
        axios.get('/super-admin/dashboard/growth', { params: { time_range: timeRange } }),
        axios.get('/super-admin/dashboard/health'),
        axios.get('/super-admin/dashboard/alerts', { params: { severity: 'high,critical' } })
      ]);

      // Update dashboard data
      if (statsRes.status === 'fulfilled') {
        setDashboardData(prev => ({ ...prev, platformStats: statsRes.value.data }));
        
        // Convert to legacy format for backward compatibility
        const platformData = statsRes.value.data;
        setStats({
          total_users: platformData.total_users,
          trial_users: Math.floor(platformData.active_users * 0.3),
          paid_subscribers: Math.floor(platformData.active_users * 0.7),
          expired_users: platformData.total_users - platformData.active_users,
          total_sounds: platformData.total_sounds,
          new_users_this_month: Math.floor(platformData.total_users * 0.1),
          revenue_this_month: platformData.monthly_revenue,
          conversion_rate: platformData.conversion_rate
        });
      }

      if (revenueRes.status === 'fulfilled') {
        setDashboardData(prev => ({ ...prev, revenueAnalytics: revenueRes.value.data }));
      }

      if (growthRes.status === 'fulfilled') {
        setDashboardData(prev => ({ ...prev, growthTrends: growthRes.value.data }));
      }

      if (healthRes.status === 'fulfilled') {
        setDashboardData(prev => ({ ...prev, systemHealth: healthRes.value.data }));
      }

      if (alertsRes.status === 'fulfilled') {
        setDashboardData(prev => ({ ...prev, systemAlerts: alertsRes.value.data }));
      }

      setError(null);
      setLastUpdated(new Date());
    } catch (err) {
      setError('Failed to load dashboard data');
      console.error('Dashboard error:', err);
    } finally {
      setLoading(prev => ({ ...prev, dashboard: false }));
    }
  }, [timeRange]);

  // Load legacy data (users and sounds) 
  const loadLegacyData = async () => {
    try {
      setLoading(prev => ({ ...prev, users: true, sounds: true }));
      
      const [usersRes, soundsRes] = await Promise.all([
        axios.get('/admin/users?limit=50'),
        axios.get('/admin/sounds?limit=50')
      ]);

      setUsers(usersRes.data);
      setSounds(soundsRes.data);
    } catch (err) {
      console.error('Failed to load legacy data:', err);
    } finally {
      setLoading(prev => ({ ...prev, users: false, sounds: false }));
    }
  };

  // Manual refresh function
  const handleManualRefresh = async () => {
    setLoading(prev => ({ ...prev, refreshing: true }));
    try {
      // Trigger server-side refresh
      await axios.post('/super-admin/dashboard/manage/refresh');
      
      // Reload data
      await loadDashboardData();
      await loadLegacyData();
    } catch (err) {
      console.error('Manual refresh failed:', err);
      setError('Failed to refresh data');
    } finally {
      setLoading(prev => ({ ...prev, refreshing: false }));
    }
  };

  // Setup auto-refresh timer
  useEffect(() => {
    if (autoRefresh) {
      refreshTimerRef.current = setInterval(() => {
        loadDashboardData();
      }, 30000); // Refresh every 30 seconds

      return () => {
        if (refreshTimerRef.current) {
          clearInterval(refreshTimerRef.current);
        }
      };
    }
  }, [autoRefresh, loadDashboardData]);

  // Initial data load and WebSocket setup
  useEffect(() => {
    loadDashboardData();
    loadLegacyData();
    initializeWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (refreshTimerRef.current) {
        clearInterval(refreshTimerRef.current);
      }
    };
  }, [loadDashboardData, initializeWebSocket]);

  // Reload data when time range changes
  useEffect(() => {
    loadDashboardData();
  }, [timeRange, loadDashboardData]);

  const extendUserTrial = async (userId, days) => {
    try {
      await axios.post(`/admin/users/${userId}/extend-trial?days=${days}`);
      alert(`Trial extended by ${days} days`);
      loadDashboardData(); // Refresh data
      loadLegacyData();
    } catch (err) {
      alert('Failed to extend trial');
      console.error('Extend trial error:', err);
    }
  };

  const activateUserSubscription = async (userId) => {
    try {
      await axios.post(`/admin/users/${userId}/activate-subscription`);
      alert('Subscription activated');
      loadDashboardData(); // Refresh data
      loadLegacyData();
    } catch (err) {
      alert('Failed to activate subscription');
      console.error('Activate subscription error:', err);
    }
  };

  const deleteSound = async (soundId) => {
    if (!window.confirm('Are you sure you want to delete this sound?')) {
      return;
    }

    try {
      await axios.delete(`/admin/sounds/${soundId}`);
      alert('Sound deleted successfully');
      loadDashboardData(); // Refresh data
      loadLegacyData();
    } catch (err) {
      alert('Failed to delete sound');
      console.error('Delete sound error:', err);
    }
  };

  // Utility functions
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
  };

  const formatNumber = (num) => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num?.toString() || '0';
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount || 0);
  };

  const getStatusBadge = (status) => {
    const statusClass = {
      trial: 'status-trial',
      active: 'status-active',
      expired: 'status-expired',
      cancelled: 'status-cancelled'
    };

    return (
      <span className={`status-badge ${statusClass[status] || 'status-default'}`}>
        {status.toUpperCase()}
      </span>
    );
  };

  // Loading and error states
  if (loading.dashboard && !stats) {
    return (
      <div className="admin-loading">
        <div className="loading-spinner">
          <div className="spinner"></div>
        </div>
        <p>Loading admin dashboard...</p>
      </div>
    );
  }

  if (error && !stats) {
    return (
      <div className="admin-error">
        <div className="error-message">
          <span className="error-icon">⚠️</span>
          Error: {error}
          <button onClick={() => window.location.reload()} className="retry-button">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="admin-dashboard">
      {/* Enhanced Header with Real-time Controls */}
      <div className="admin-header">
        <div className="header-left">
          <h1>Admin Control Panel</h1>
          <div className="connection-status">
            <span className={`status-indicator ${wsConnected ? 'connected' : 'disconnected'}`}>
              {wsConnected ? '🟢 Live' : '🔴 Offline'}
            </span>
            {lastUpdated && (
              <span className="last-updated">
                Last updated: {lastUpdated.toLocaleTimeString()}
              </span>
            )}
          </div>
        </div>

        <div className="header-controls">
          {/* Time Range Selector */}
          <select 
            value={timeRange} 
            onChange={(e) => setTimeRange(e.target.value)}
            className="time-range-selector"
          >
            <option value="1d">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="90d">Last 90 Days</option>
          </select>

          {/* Auto Refresh Toggle */}
          <label className="auto-refresh-toggle">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
            />
            Auto Refresh
          </label>

          {/* Manual Refresh Button */}
          <button 
            onClick={handleManualRefresh}
            disabled={loading.refreshing}
            className="refresh-button"
          >
            {loading.refreshing ? (
              <div className="button-spinner">
                <div className="spinner"></div>
              </div>
            ) : (
              '🔄 Refresh'
            )}
          </button>
        </div>
      </div>

      {/* Enhanced Navigation Tabs */}
      <div className="admin-tabs">
        <button 
          className={selectedTab === 'dashboard' ? 'active' : ''}
          onClick={() => setSelectedTab('dashboard')}
        >
          Overview
        </button>
        <button 
          className={selectedTab === 'analytics' ? 'active' : ''}
          onClick={() => setSelectedTab('analytics')}
        >
          Analytics
        </button>
        <button 
          className={selectedTab === 'users' ? 'active' : ''}
          onClick={() => setSelectedTab('users')}
        >
          Users
        </button>
        <button 
          className={selectedTab === 'sounds' ? 'active' : ''}
          onClick={() => setSelectedTab('sounds')}
        >
          Sounds
        </button>
        <button 
          className={selectedTab === 'system' ? 'active' : ''}
          onClick={() => setSelectedTab('system')}
        >
          System Health
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="error-banner">
          <span className="error-icon">⚠️</span>
          {error}
          <button onClick={() => setError(null)} className="dismiss-error">×</button>
        </div>
      )}

      {/* Dashboard Content */}
      <div className="dashboard-content">
        {selectedTab === 'dashboard' && (
          <div className="dashboard-overview">
            {loading.dashboard ? (
              <div className="loading-section">
                <div className="spinner"></div>
                <p>Loading dashboard data...</p>
              </div>
            ) : stats && (
              <div className="stats-grid">
                <div className="stat-card enhanced">
                  <h3>Total Users</h3>
                  <div className="stat-number">{formatNumber(stats.total_users)}</div>
                  <div className="stat-change positive">
                    +{dashboardData.platformStats?.user_growth_rate?.toFixed(1) || '0'}%
                  </div>
                  <div className="stat-details">
                    Active: {formatNumber(dashboardData.platformStats?.active_users || 0)}
                  </div>
                </div>

                <div className="stat-card enhanced">
                  <h3>Revenue (30d)</h3>
                  <div className="stat-number">{formatCurrency(stats.revenue_this_month)}</div>
                  <div className="stat-change positive">
                    +{dashboardData.platformStats?.revenue_growth_rate?.toFixed(1) || '0'}%
                  </div>
                  <div className="stat-details">
                    MRR: {formatCurrency(dashboardData.revenueAnalytics?.mrr || 0)}
                  </div>
                </div>

                <div className="stat-card enhanced">
                  <h3>Organizations</h3>
                  <div className="stat-number">{formatNumber(dashboardData.platformStats?.total_organizations || 0)}</div>
                  <div className="stat-change positive">
                    +{dashboardData.platformStats?.org_growth_rate?.toFixed(1) || '0'}%
                  </div>
                  <div className="stat-details">Growth trending upward</div>
                </div>

                <div className="stat-card enhanced">
                  <h3>Active Sessions</h3>
                  <div className="stat-number">{formatNumber(dashboardData.platformStats?.active_sessions || 0)}</div>
                  <div className="stat-details">Currently online</div>
                </div>

                <div className="stat-card enhanced">
                  <h3>Content Plays</h3>
                  <div className="stat-number">{formatNumber(dashboardData.platformStats?.content_plays || 0)}</div>
                  <div className="stat-details">This {timeRange}</div>
                </div>

                <div className="stat-card enhanced">
                  <h3>Conversion Rate</h3>
                  <div className="stat-number">{stats.conversion_rate}%</div>
                  <div className="stat-details">Trial to paid</div>
                </div>

                <div className="stat-card enhanced">
                  <h3>Total Sounds</h3>
                  <div className="stat-number">{formatNumber(stats.total_sounds)}</div>
                  <div className="stat-details">In library</div>
                </div>

                <div className="stat-card enhanced">
                  <h3>System Health</h3>
                  <div className="stat-number health-score">
                    {dashboardData.systemHealth?.overall_health_score?.toFixed(1) || '0'}%
                  </div>
                  <div className={`stat-details ${dashboardData.systemHealth?.overall_health_score >= 90 ? 'healthy' : 'warning'}`}>
                    {dashboardData.systemHealth?.overall_health_score >= 90 ? 'Excellent' : 'Needs attention'}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {selectedTab === 'analytics' && (
          <div className="analytics-tab">
            <div className="analytics-sections">
              {/* Revenue Analytics */}
              {dashboardData.revenueAnalytics && (
                <div className="analytics-section">
                  <h2>Revenue Analytics</h2>
                  <div className="revenue-cards">
                    <div className="revenue-card">
                      <h3>Monthly Recurring Revenue</h3>
                      <div className="revenue-amount">{formatCurrency(dashboardData.revenueAnalytics.mrr)}</div>
                      <div className="revenue-change positive">
                        +{dashboardData.revenueAnalytics.mrr_growth_rate?.toFixed(1)}%
                      </div>
                    </div>
                    <div className="revenue-card">
                      <h3>Average Revenue Per User</h3>
                      <div className="revenue-amount">{formatCurrency(dashboardData.revenueAnalytics.arpu)}</div>
                      <div className="revenue-sub">Per month</div>
                    </div>
                    <div className="revenue-card">
                      <h3>Customer Lifetime Value</h3>
                      <div className="revenue-amount">{formatCurrency(dashboardData.revenueAnalytics.clv)}</div>
                      <div className="revenue-sub">Average CLV</div>
                    </div>
                  </div>
                </div>
              )}

              {/* Growth Trends */}
              {dashboardData.growthTrends && (
                <div className="analytics-section">
                  <h2>Growth Trends</h2>
                  <div className="growth-cards">
                    <div className="growth-card">
                      <h3>New Users</h3>
                      <div className="growth-number">{formatNumber(dashboardData.growthTrends.new_users)}</div>
                      <div className="growth-period">This {timeRange}</div>
                    </div>
                    <div className="growth-card">
                      <h3>Retention Rate</h3>
                      <div className="growth-number">{dashboardData.growthTrends.retention_rate?.toFixed(1)}%</div>
                      <div className="growth-period">30-day retention</div>
                    </div>
                  </div>
                  
                  {dashboardData.growthTrends.key_insights && (
                    <div className="insights-section">
                      <h3>Key Insights</h3>
                      <ul className="insights-list">
                        {dashboardData.growthTrends.key_insights.map((insight, index) => (
                          <li key={index} className="insight-item">
                            <span className="insight-icon">💡</span>
                            {insight}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {selectedTab === 'system' && (
          <div className="system-tab">
            {dashboardData.systemHealth && (
              <div className="system-health">
                <h2>System Health</h2>
                <div className="health-overview">
                  <div className="health-score-card">
                    <h3>Overall Health Score</h3>
                    <div className={`health-percentage ${dashboardData.systemHealth.overall_health_score >= 90 ? 'excellent' : 'warning'}`}>
                      {dashboardData.systemHealth.overall_health_score?.toFixed(1)}%
                    </div>
                    <div className="health-status">
                      {dashboardData.systemHealth.overall_health_score >= 90 ? 'Excellent' : 'Needs Attention'}
                    </div>
                  </div>
                </div>

                {dashboardData.systemHealth.components && (
                  <div className="health-components">
                    {Object.entries(dashboardData.systemHealth.components).map(([component, health]) => (
                      <div key={component} className="component-card">
                        <div className="component-name">{component.replace('_', ' ').toUpperCase()}</div>
                        <div className={`component-status ${health.status}`}>
                          {health.status}
                        </div>
                        <div className="component-metrics">
                          {health.response_time && (
                            <span>Response: {health.response_time}ms</span>
                          )}
                          {health.uptime && (
                            <span>Uptime: {health.uptime?.toFixed(1)}%</span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {dashboardData.systemAlerts && dashboardData.systemAlerts.alerts && (
              <div className="system-alerts">
                <h2>System Alerts</h2>
                <div className="alerts-summary">
                  <div className="alert-count critical">
                    <span className="count">{dashboardData.systemAlerts.critical_count || 0}</span>
                    <span className="label">Critical</span>
                  </div>
                  <div className="alert-count high">
                    <span className="count">{dashboardData.systemAlerts.high_count || 0}</span>
                    <span className="label">High</span>
                  </div>
                </div>

                <div className="alerts-list">
                  {dashboardData.systemAlerts.alerts.slice(0, 5).map((alert, index) => (
                    <div key={index} className={`alert-item ${alert.severity}`}>
                      <div className="alert-header">
                        <span className={`alert-severity ${alert.severity}`}>
                          {alert.severity.toUpperCase()}
                        </span>
                        <span className="alert-time">
                          {new Date(alert.timestamp).toLocaleString()}
                        </span>
                      </div>
                      <div className="alert-message">{alert.message}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {selectedTab === 'users' && (
          <div className="users-management">
            <div className="users-filters">
              <input
                type="text"
                placeholder="Search by email..."
                value={userFilter}
                onChange={(e) => setUserFilter(e.target.value)}
                className="search-input"
              />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="status-filter"
              >
                <option value="">All Statuses</option>
                <option value="trial">Trial</option>
                <option value="active">Active</option>
                <option value="expired">Expired</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>

            {loading.users ? (
              <div className="loading-section">
                <div className="spinner"></div>
                <p>Loading users...</p>
              </div>
            ) : (
              <div className="users-table">
                <table>
                  <thead>
                    <tr>
                      <th>Email</th>
                      <th>Status</th>
                      <th>Created</th>
                      <th>Trial End</th>
                      <th>Last Login</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users
                      .filter(user => 
                        user.email.toLowerCase().includes(userFilter.toLowerCase()) &&
                        (statusFilter === '' || user.subscription_status === statusFilter)
                      )
                      .map(user => (
                        <tr key={user.id}>
                          <td>{user.email}</td>
                          <td>{getStatusBadge(user.subscription_status)}</td>
                          <td>{formatDate(user.created_at)}</td>
                          <td>{formatDate(user.trial_end_date)}</td>
                          <td>{formatDate(user.last_login)}</td>
                          <td className="user-actions">
                            <button 
                              onClick={() => extendUserTrial(user.id, 7)}
                              className="btn-extend"
                              title="Extend trial by 7 days"
                            >
                              +7d
                            </button>
                            <button 
                              onClick={() => activateUserSubscription(user.id)}
                              className="btn-activate"
                              title="Activate subscription"
                            >
                              Activate
                            </button>
                          </td>
                        </tr>
                      ))
                    }
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {selectedTab === 'sounds' && (
          <div className="sounds-management">
            <div className="sounds-header">
              <h2>Sound Library Management</h2>
              <button className="btn-add-sound">Add New Sound</button>
            </div>

            {loading.sounds ? (
              <div className="loading-section">
                <div className="spinner"></div>
                <p>Loading sounds...</p>
              </div>
            ) : (
              <div className="sounds-grid">
                {sounds.map(sound => (
                  <div key={sound.id} className="sound-card">
                    <div className="sound-thumbnail">
                      {sound.thumbnail_url ? (
                        <img src={sound.thumbnail_url} alt={sound.title} />
                      ) : (
                        <div className="no-thumbnail">No Image</div>
                      )}
                    </div>
                    <div className="sound-info">
                      <h3>{sound.title}</h3>
                      <p className="sound-category">{sound.category}</p>
                      <p className="sound-duration">{sound.duration}s</p>
                      <p className="sound-description">{sound.description}</p>
                      <div className="sound-badges">
                        {sound.is_premium && <span className="premium-badge">Premium</span>}
                      </div>
                    </div>
                    <div className="sound-actions">
                      <button className="btn-edit">Edit</button>
                      <button 
                        className="btn-delete"
                        onClick={() => deleteSound(sound.id)}
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminDashboard;
