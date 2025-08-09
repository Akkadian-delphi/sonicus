import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useTenant } from '../context/TenantContext';
import { useAuth } from '../hooks/useAuth';
import axios from '../utils/axios';
import './UserManagement.css';

const UserManagement = () => {
  const { t } = useTranslation();
  const { organization, isB2B2CMode, getOrganizationLimits } = useTenant();
  const { user, hasRole } = useAuth();
  
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteData, setInviteData] = useState({ email: '', role: 'user' });
  const [searchTerm, setSearchTerm] = useState('');
  const [filterRole, setFilterRole] = useState('all');
  const [sortBy, setSortBy] = useState('name');
  
  const limits = getOrganizationLimits();

  useEffect(() => {
    if (!isB2B2CMode() || !organization) {
      setError(t('userManagement.error.noOrganization'));
      setLoading(false);
      return;
    }

    if (!hasRole('admin')) {
      setError(t('userManagement.error.noPermission'));
      setLoading(false);
      return;
    }

    fetchUsers();
  }, [organization, isB2B2CMode]);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      // This endpoint should return users within the organization context
      const response = await axios.get('/api/v1/organizations/me/users');
      setUsers(response.data);
      setError(null);
    } catch (error) {
      console.error('Error fetching users:', error);
      setError(t('userManagement.error.fetchFailed'));
    } finally {
      setLoading(false);
    }
  };

  const handleInviteUser = async (e) => {
    e.preventDefault();
    
    try {
      // Check user limit
      if (users.length >= limits.maxUsers) {
        setError(t('userManagement.error.userLimitReached', { limit: limits.maxUsers }));
        return;
      }

      const response = await axios.post('/api/v1/organizations/me/users/invite', inviteData);
      
      // Reset form and close modal
      setInviteData({ email: '', role: 'user' });
      setShowInviteModal(false);
      
      // Refresh users list
      await fetchUsers();
      
      // Show success message (you might want to use a toast notification)
      alert(t('userManagement.invite.success'));
      
    } catch (error) {
      console.error('Error inviting user:', error);
      setError(error.response?.data?.detail || t('userManagement.invite.error'));
    }
  };

  const handleRemoveUser = async (userId) => {
    if (!window.confirm(t('userManagement.confirmRemove'))) {
      return;
    }

    try {
      await axios.delete(`/api/v1/organizations/me/users/${userId}`);
      await fetchUsers(); // Refresh the list
    } catch (error) {
      console.error('Error removing user:', error);
      setError(error.response?.data?.detail || t('userManagement.remove.error'));
    }
  };

  const handleUpdateUserRole = async (userId, newRole) => {
    try {
      await axios.patch(`/api/v1/organizations/me/users/${userId}`, { role: newRole });
      await fetchUsers(); // Refresh the list
    } catch (error) {
      console.error('Error updating user role:', error);
      setError(error.response?.data?.detail || t('userManagement.updateRole.error'));
    }
  };

  // Filter and sort users
  const filteredUsers = users
    .filter(user => {
      const matchesSearch = user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           user.name?.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesRole = filterRole === 'all' || user.role === filterRole;
      return matchesSearch && matchesRole;
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return (a.name || a.email).localeCompare(b.name || b.email);
        case 'role':
          return a.role.localeCompare(b.role);
        case 'created_at':
          return new Date(b.created_at) - new Date(a.created_at);
        default:
          return 0;
      }
    });

  const getRoleColor = (role) => {
    switch (role) {
      case 'admin': return '#dc3545';
      case 'manager': return '#fd7e14';
      case 'user': return '#28a745';
      default: return '#6c757d';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return '#28a745';
      case 'invited': return '#ffc107';
      case 'inactive': return '#6c757d';
      default: return '#6c757d';
    }
  };

  if (!isB2B2CMode()) {
    return (
      <div className="user-management">
        <div className="container">
          <div className="error-state">
            <h2>{t('userManagement.error.b2cMode')}</h2>
            <p>{t('userManagement.error.b2cModeDesc')}</p>
          </div>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="user-management">
        <div className="container">
          <div className="loading-state">
            <div className="spinner"></div>
            <p>{t('common.loading')}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="user-management">
      <div className="container">
        {/* Header */}
        <div className="management-header">
          <div className="header-content">
            <h1>{t('userManagement.title')}</h1>
            <p className="subtitle">
              {t('userManagement.subtitle', { 
                current: users.length, 
                limit: limits.maxUsers,
                organization: organization.display_name || organization.name
              })}
            </p>
          </div>
          
          <div className="header-actions">
            <button 
              onClick={() => setShowInviteModal(true)}
              className="btn btn-primary"
              disabled={users.length >= limits.maxUsers}
            >
              {t('userManagement.inviteUser')}
            </button>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="error-message">
            {error}
            <button onClick={() => setError(null)} className="error-close">×</button>
          </div>
        )}

        {/* Filters and Search */}
        <div className="filters-section">
          <div className="search-box">
            <input
              type="text"
              placeholder={t('userManagement.searchPlaceholder')}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input"
            />
          </div>
          
          <div className="filter-controls">
            <select
              value={filterRole}
              onChange={(e) => setFilterRole(e.target.value)}
              className="filter-select"
            >
              <option value="all">{t('userManagement.filters.allRoles')}</option>
              <option value="admin">{t('userManagement.roles.admin')}</option>
              <option value="manager">{t('userManagement.roles.manager')}</option>
              <option value="user">{t('userManagement.roles.user')}</option>
            </select>
            
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="sort-select"
            >
              <option value="name">{t('userManagement.sort.name')}</option>
              <option value="role">{t('userManagement.sort.role')}</option>
              <option value="created_at">{t('userManagement.sort.dateAdded')}</option>
            </select>
          </div>
        </div>

        {/* Users List */}
        <div className="users-section">
          {filteredUsers.length > 0 ? (
            <div className="users-grid">
              {filteredUsers.map(userItem => (
                <div key={userItem.id} className="user-card">
                  <div className="user-avatar">
                    {userItem.avatar ? (
                      <img src={userItem.avatar} alt={userItem.name || userItem.email} />
                    ) : (
                      <div className="avatar-placeholder">
                        {(userItem.name || userItem.email).charAt(0).toUpperCase()}
                      </div>
                    )}
                  </div>
                  
                  <div className="user-info">
                    <h3>{userItem.name || userItem.email}</h3>
                    {userItem.name && (
                      <p className="user-email">{userItem.email}</p>
                    )}
                    
                    <div className="user-badges">
                      <span 
                        className="role-badge" 
                        style={{ backgroundColor: getRoleColor(userItem.role) }}
                      >
                        {t(`userManagement.roles.${userItem.role}`)}
                      </span>
                      
                      <span 
                        className="status-badge" 
                        style={{ backgroundColor: getStatusColor(userItem.status) }}
                      >
                        {t(`userManagement.status.${userItem.status}`)}
                      </span>
                    </div>
                    
                    <div className="user-meta">
                      <small>
                        {t('userManagement.joinedOn')}: {' '}
                        {new Date(userItem.created_at).toLocaleDateString()}
                      </small>
                      {userItem.last_active && (
                        <small>
                          {t('userManagement.lastActive')}: {' '}
                          {new Date(userItem.last_active).toLocaleDateString()}
                        </small>
                      )}
                    </div>
                  </div>
                  
                  <div className="user-actions">
                    {userItem.id !== user?.id && hasRole('admin') && (
                      <>
                        <select
                          value={userItem.role}
                          onChange={(e) => handleUpdateUserRole(userItem.id, e.target.value)}
                          className="role-select"
                        >
                          <option value="user">{t('userManagement.roles.user')}</option>
                          <option value="manager">{t('userManagement.roles.manager')}</option>
                          <option value="admin">{t('userManagement.roles.admin')}</option>
                        </select>
                        
                        <button
                          onClick={() => handleRemoveUser(userItem.id)}
                          className="btn btn-danger btn-sm"
                        >
                          {t('userManagement.removeUser')}
                        </button>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <div className="empty-icon">👥</div>
              <h3>{t('userManagement.noUsers')}</h3>
              <p>{t('userManagement.noUsersDesc')}</p>
              <button 
                onClick={() => setShowInviteModal(true)}
                className="btn btn-primary"
              >
                {t('userManagement.inviteFirstUser')}
              </button>
            </div>
          )}
        </div>

        {/* Invite Modal */}
        {showInviteModal && (
          <div className="modal-overlay" onClick={() => setShowInviteModal(false)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h2>{t('userManagement.invite.title')}</h2>
                <button 
                  onClick={() => setShowInviteModal(false)}
                  className="modal-close"
                >
                  ×
                </button>
              </div>
              
              <form onSubmit={handleInviteUser} className="invite-form">
                <div className="form-group">
                  <label htmlFor="email">
                    {t('userManagement.invite.email')}
                  </label>
                  <input
                    type="email"
                    id="email"
                    value={inviteData.email}
                    onChange={(e) => setInviteData(prev => ({ ...prev, email: e.target.value }))}
                    required
                    placeholder="user@company.com"
                  />
                </div>
                
                <div className="form-group">
                  <label htmlFor="role">
                    {t('userManagement.invite.role')}
                  </label>
                  <select
                    id="role"
                    value={inviteData.role}
                    onChange={(e) => setInviteData(prev => ({ ...prev, role: e.target.value }))}
                  >
                    <option value="user">{t('userManagement.roles.user')}</option>
                    <option value="manager">{t('userManagement.roles.manager')}</option>
                    <option value="admin">{t('userManagement.roles.admin')}</option>
                  </select>
                </div>
                
                <div className="role-descriptions">
                  <h4>{t('userManagement.invite.roleDescriptions')}</h4>
                  <ul>
                    <li><strong>{t('userManagement.roles.user')}:</strong> {t('userManagement.roleDesc.user')}</li>
                    <li><strong>{t('userManagement.roles.manager')}:</strong> {t('userManagement.roleDesc.manager')}</li>
                    <li><strong>{t('userManagement.roles.admin')}:</strong> {t('userManagement.roleDesc.admin')}</li>
                  </ul>
                </div>
                
                <div className="modal-actions">
                  <button 
                    type="button" 
                    onClick={() => setShowInviteModal(false)}
                    className="btn btn-secondary"
                  >
                    {t('common.cancel')}
                  </button>
                  <button type="submit" className="btn btn-primary">
                    {t('userManagement.invite.send')}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default UserManagement;
