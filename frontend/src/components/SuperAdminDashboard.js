import React, { useState, useEffect, useCallback, useRef } from 'react';
import axios from '../utils/axios';
import './SuperAdminDashboard.css';

const SuperAdminDashboard = () => {
  // Dashboard data states
  const [platformStats, setPlatformStats] = useState(null);
  const [revenueAnalytics, setRevenueAnalytics] = useState(null);
  const [growthTrends, setGrowthTrends] = useState(null);
  const [systemHealth, setSystemHealth] = useState(null);
  const [systemAlerts, setSystemAlerts] = useState(null);

  // UI states
  const [selectedTab, setSelectedTab] = useState('overview');
  const [loading, setLoading] = useState({
    platform: false,
    revenue: false,
    growth: false,
    health: false,
    alerts: false,
    refreshing: false
  });
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  // Time range and filters
  const [timeRange, setTimeRange] = useState('30d');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(30000); // 30 seconds

  // WebSocket and real-time updates
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef(null);
  const refreshTimerRef = useRef(null);

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
        console.log('Dashboard WebSocket connected');
        setWsConnected(true);
        setError(null);
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
        console.log('Dashboard WebSocket disconnected');
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
  }, []);

  // Handle real-time data updates from WebSocket
  const handleRealTimeUpdate = useCallback((data) => {
    const { type, payload } = data;
    
    switch (type) {
      case 'platform_stats':
        setPlatformStats(payload);
        break;
      case 'revenue_analytics':
        setRevenueAnalytics(payload);
        break;
      case 'growth_trends':
        setGrowthTrends(payload);
        break;
      case 'system_health':
        setSystemHealth(payload);
        break;
      case 'system_alerts':
        setSystemAlerts(payload);
        break;
      case 'full_refresh':
        loadAllDashboardData();
        break;
      default:
        console.log('Unknown real-time update type:', type);
    }
    
    setLastUpdated(new Date());
  }, []);

  // Load platform statistics
  const loadPlatformStats = async (showLoading = true) => {
    try {
      if (showLoading) {
        setLoading(prev => ({ ...prev, platform: true }));
      }

      const response = await axios.get('/super-admin/dashboard/stats', {
        params: { time_range: timeRange }
      });

      setPlatformStats(response.data);
      setError(null);
    } catch (err) {
      console.error('Failed to load platform stats:', err);
      setError(prev => ({ ...prev, platform: 'Failed to load platform statistics' }));
    } finally {
      if (showLoading) {
        setLoading(prev => ({ ...prev, platform: false }));
      }
    }
  };

  // Load revenue analytics
  const loadRevenueAnalytics = async (showLoading = true) => {
    try {
      if (showLoading) {
        setLoading(prev => ({ ...prev, revenue: true }));
      }

      const response = await axios.get('/super-admin/dashboard/revenue', {
        params: { 
          time_range: timeRange,
          breakdown: 'monthly'
        }
      });

      setRevenueAnalytics(response.data);
    } catch (err) {
      console.error('Failed to load revenue analytics:', err);
      setError(prev => ({ ...prev, revenue: 'Failed to load revenue data' }));
    } finally {
      if (showLoading) {
        setLoading(prev => ({ ...prev, revenue: false }));
      }
    }
  };

  // Load growth trends
  const loadGrowthTrends = async (showLoading = true) => {
    try {
      if (showLoading) {
        setLoading(prev => ({ ...prev, growth: true }));
      }

      const response = await axios.get('/super-admin/dashboard/growth', {
        params: { time_range: timeRange }
      });

      setGrowthTrends(response.data);
    } catch (err) {
      console.error('Failed to load growth trends:', err);
      setError(prev => ({ ...prev, growth: 'Failed to load growth data' }));
    } finally {
      if (showLoading) {
        setLoading(prev => ({ ...prev, growth: false }));
      }
    }
  };

  // Load system health
  const loadSystemHealth = async (showLoading = true) => {
    try {
      if (showLoading) {
        setLoading(prev => ({ ...prev, health: true }));
      }

      const response = await axios.get('/super-admin/dashboard/health');
      setSystemHealth(response.data);
    } catch (err) {
      console.error('Failed to load system health:', err);
      setError(prev => ({ ...prev, health: 'Failed to load system health' }));
    } finally {
      if (showLoading) {
        setLoading(prev => ({ ...prev, health: false }));
      }
    }
  };

  // Load system alerts
  const loadSystemAlerts = async (showLoading = true) => {
    try {
      if (showLoading) {
        setLoading(prev => ({ ...prev, alerts: true }));
      }

      const response = await axios.get('/super-admin/dashboard/alerts', {
        params: { severity: 'high,critical' }
      });

      setSystemAlerts(response.data);
    } catch (err) {
      console.error('Failed to load system alerts:', err);
      setError(prev => ({ ...prev, alerts: 'Failed to load alerts' }));
    } finally {
      if (showLoading) {
        setLoading(prev => ({ ...prev, alerts: false }));
      }
    }
  };

  // Load all dashboard data
  const loadAllDashboardData = useCallback(async (showLoading = true) => {
    const loadPromises = [
      loadPlatformStats(showLoading),
      loadRevenueAnalytics(showLoading),
      loadGrowthTrends(showLoading),
      loadSystemHealth(showLoading),
      loadSystemAlerts(showLoading)
    ];

    await Promise.allSettled(loadPromises);
    setLastUpdated(new Date());
  }, [timeRange]);

  // Manual refresh function
  const handleManualRefresh = async () => {
    setLoading(prev => ({ ...prev, refreshing: true }));
    await loadAllDashboardData(false);
    setLoading(prev => ({ ...prev, refreshing: false }));
  };

  // Handle time range change
  const handleTimeRangeChange = (newRange) => {
    setTimeRange(newRange);
    // Data will be reloaded by useEffect watching timeRange
  };

  // Setup auto-refresh timer
  useEffect(() => {
    if (autoRefresh && refreshInterval > 0) {
      refreshTimerRef.current = setInterval(() => {
        loadAllDashboardData(false);
      }, refreshInterval);

      return () => {
        if (refreshTimerRef.current) {
          clearInterval(refreshTimerRef.current);
        }
      };
    }
  }, [autoRefresh, refreshInterval, loadAllDashboardData]);

  // Initial data load and WebSocket setup
  useEffect(() => {
    loadAllDashboardData();
    initializeWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (refreshTimerRef.current) {
        clearInterval(refreshTimerRef.current);
      }
    };
  }, []);

  // Reload data when time range changes
  useEffect(() => {
    loadAllDashboardData();
  }, [timeRange]);

  // Format numbers for display
  const formatNumber = (num) => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num?.toString() || '0';
  };

  // Format currency
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount || 0);
  };

  // Format percentage
  const formatPercentage = (value) => {
    return `${(value || 0).toFixed(1)}%`;
  };

  // Get loading indicator
  const getLoadingSpinner = () => (
    <div className="loading-spinner">
      <div className="spinner"></div>
    </div>
  );

  // Get error message
  const getErrorMessage = (errorMsg) => (
    <div className="error-message">
      <span className="error-icon">⚠️</span>
      {errorMsg}
    </div>
  );

  return (
    <div className="super-admin-dashboard">
      {/* Header */}
      <div className="dashboard-header">
        <div className="header-left">
          <h1>Super Admin Dashboard</h1>
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
            onChange={(e) => handleTimeRangeChange(e.target.value)}
            className="time-range-selector"
          >
            <option value="1d">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="90d">Last 90 Days</option>
            <option value="1y">Last Year</option>
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
            {loading.refreshing ? getLoadingSpinner() : '🔄 Refresh'}
          </button>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="dashboard-tabs">
        <button 
          className={selectedTab === 'overview' ? 'active' : ''}
          onClick={() => setSelectedTab('overview')}
        >
          Overview
        </button>
        <button 
          className={selectedTab === 'revenue' ? 'active' : ''}
          onClick={() => setSelectedTab('revenue')}
        >
          Revenue
        </button>
        <button 
          className={selectedTab === 'growth' ? 'active' : ''}
          onClick={() => setSelectedTab('growth')}
        >
          Growth
        </button>
        <button 
          className={selectedTab === 'health' ? 'active' : ''}
          onClick={() => setSelectedTab('health')}
        >
          System Health
        </button>
        <button 
          className={selectedTab === 'alerts' ? 'active' : ''}
          onClick={() => setSelectedTab('alerts')}
        >
          Alerts
        </button>
      </div>

      {/* Dashboard Content */}
      <div className="dashboard-content">
        {selectedTab === 'overview' && (
          <div className="overview-tab">
            {loading.platform ? getLoadingSpinner() : error?.platform ? getErrorMessage(error.platform) : platformStats && (
              <div className="stats-grid">
                <div className="stat-card">
                  <h3>Total Users</h3>
                  <div className="stat-number">{formatNumber(platformStats.total_users)}</div>
                  <div className="stat-change positive">
                    +{formatPercentage(platformStats.user_growth_rate)}
                  </div>
                </div>

                <div className="stat-card">
                  <h3>Organizations</h3>
                  <div className="stat-number">{formatNumber(platformStats.total_organizations)}</div>
                  <div className="stat-change positive">
                    +{formatPercentage(platformStats.org_growth_rate)}
                  </div>
                </div>

                <div className="stat-card">
                  <h3>Monthly Revenue</h3>
                  <div className="stat-number">{formatCurrency(platformStats.monthly_revenue)}</div>
                  <div className="stat-change positive">
                    +{formatPercentage(platformStats.revenue_growth_rate)}
                  </div>
                </div>

                <div className="stat-card">
                  <h3>Active Sessions</h3>
                  <div className="stat-number">{formatNumber(platformStats.active_sessions)}</div>
                  <div className="stat-sub">Currently online</div>
                </div>

                <div className="stat-card">
                  <h3>Content Plays</h3>
                  <div className="stat-number">{formatNumber(platformStats.content_plays)}</div>
                  <div className="stat-sub">This {timeRange}</div>
                </div>

                <div className="stat-card">
                  <h3>Conversion Rate</h3>
                  <div className="stat-number">{formatPercentage(platformStats.conversion_rate)}</div>
                  <div className="stat-sub">Trial to paid</div>
                </div>
              </div>
            )}
          </div>
        )}

        {selectedTab === 'revenue' && (
          <div className="revenue-tab">
            {loading.revenue ? getLoadingSpinner() : error?.revenue ? getErrorMessage(error.revenue) : revenueAnalytics && (
              <div className="revenue-analytics">
                <div className="revenue-summary">
                  <div className="revenue-card">
                    <h3>Monthly Recurring Revenue</h3>
                    <div className="revenue-amount">{formatCurrency(revenueAnalytics.mrr)}</div>
                    <div className="revenue-change positive">
                      +{formatPercentage(revenueAnalytics.mrr_growth_rate)}
                    </div>
                  </div>

                  <div className="revenue-card">
                    <h3>Annual Recurring Revenue</h3>
                    <div className="revenue-amount">{formatCurrency(revenueAnalytics.arr)}</div>
                    <div className="revenue-change positive">
                      +{formatPercentage(revenueAnalytics.arr_growth_rate)}
                    </div>
                  </div>

                  <div className="revenue-card">
                    <h3>Average Revenue Per User</h3>
                    <div className="revenue-amount">{formatCurrency(revenueAnalytics.arpu)}</div>
                    <div className="revenue-sub">Per month</div>
                  </div>

                  <div className="revenue-card">
                    <h3>Customer Lifetime Value</h3>
                    <div className="revenue-amount">{formatCurrency(revenueAnalytics.clv)}</div>
                    <div className="revenue-sub">Average CLV</div>
                  </div>
                </div>

                {/* Revenue Chart Placeholder */}
                <div className="revenue-chart">
                  <h3>Revenue Trends</h3>
                  <div className="chart-placeholder">
                    📈 Revenue trend chart would go here
                    {/* Integration point for chart library like Chart.js or D3 */}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {selectedTab === 'growth' && (
          <div className="growth-tab">
            {loading.growth ? getLoadingSpinner() : error?.growth ? getErrorMessage(error.growth) : growthTrends && (
              <div className="growth-analytics">
                <div className="growth-summary">
                  <div className="growth-card">
                    <h3>User Growth</h3>
                    <div className="growth-number">{formatNumber(growthTrends.new_users)}</div>
                    <div className="growth-period">New this {timeRange}</div>
                  </div>

                  <div className="growth-card">
                    <h3>Organization Growth</h3>
                    <div className="growth-number">{formatNumber(growthTrends.new_organizations)}</div>
                    <div className="growth-period">New this {timeRange}</div>
                  </div>

                  <div className="growth-card">
                    <h3>Retention Rate</h3>
                    <div className="growth-number">{formatPercentage(growthTrends.retention_rate)}</div>
                    <div className="growth-period">30-day retention</div>
                  </div>

                  <div className="growth-card">
                    <h3>Churn Rate</h3>
                    <div className="growth-number">{formatPercentage(growthTrends.churn_rate)}</div>
                    <div className="growth-period">Monthly churn</div>
                  </div>
                </div>

                {/* Growth Insights */}
                {growthTrends.key_insights && (
                  <div className="growth-insights">
                    <h3>Key Growth Insights</h3>
                    <ul className="insights-list">
                      {growthTrends.key_insights.map((insight, index) => (
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
        )}

        {selectedTab === 'health' && (
          <div className="health-tab">
            {loading.health ? getLoadingSpinner() : error?.health ? getErrorMessage(error.health) : systemHealth && (
              <div className="system-health">
                <div className="health-overview">
                  <div className="health-score">
                    <h3>Overall System Health</h3>
                    <div className={`health-percentage ${systemHealth.overall_health_score >= 90 ? 'excellent' : systemHealth.overall_health_score >= 70 ? 'good' : 'warning'}`}>
                      {formatPercentage(systemHealth.overall_health_score)}
                    </div>
                    <div className="health-status">
                      {systemHealth.overall_health_score >= 90 ? 'Excellent' : 
                       systemHealth.overall_health_score >= 70 ? 'Good' : 'Needs Attention'}
                    </div>
                  </div>
                </div>

                <div className="health-components">
                  {systemHealth.components && Object.entries(systemHealth.components).map(([component, health]) => (
                    <div key={component} className="component-health">
                      <div className="component-name">{component}</div>
                      <div className={`component-status ${health.status}`}>
                        {health.status}
                      </div>
                      <div className="component-metrics">
                        {health.response_time && (
                          <span>Response: {health.response_time}ms</span>
                        )}
                        {health.uptime && (
                          <span>Uptime: {formatPercentage(health.uptime)}</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {selectedTab === 'alerts' && (
          <div className="alerts-tab">
            {loading.alerts ? getLoadingSpinner() : error?.alerts ? getErrorMessage(error.alerts) : systemAlerts && (
              <div className="system-alerts">
                <div className="alerts-summary">
                  <div className="alert-count critical">
                    <span className="count">{systemAlerts.critical_count || 0}</span>
                    <span className="label">Critical</span>
                  </div>
                  <div className="alert-count high">
                    <span className="count">{systemAlerts.high_count || 0}</span>
                    <span className="label">High</span>
                  </div>
                  <div className="alert-count medium">
                    <span className="count">{systemAlerts.medium_count || 0}</span>
                    <span className="label">Medium</span>
                  </div>
                  <div className="alert-count low">
                    <span className="count">{systemAlerts.low_count || 0}</span>
                    <span className="label">Low</span>
                  </div>
                </div>

                <div className="alerts-list">
                  {systemAlerts.alerts && systemAlerts.alerts.map((alert, index) => (
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
                      {alert.affected_users && (
                        <div className="alert-impact">
                          Affected users: {alert.affected_users}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default SuperAdminDashboard;
