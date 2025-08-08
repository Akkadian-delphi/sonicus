import React, { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../hooks/useAuth';
import '../styles/AvatarMenu.css';

function AvatarMenu() {
  const { t } = useTranslation();
  const { user, logout } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef(null);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = async () => {
    setIsOpen(false);
    await logout();
  };

  const toggleMenu = () => {
    setIsOpen(!isOpen);
  };

  // Generate initials from user name or email
  const getInitials = () => {
    const name = user?.name || user?.preferred_username || user?.email || 'U';
    if (name.includes(' ')) {
      const nameParts = name.split(' ');
      return (nameParts[0][0] + nameParts[1][0]).toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  };

  // Generate a consistent color based on user name
  const getAvatarColor = () => {
    const name = user?.name || user?.preferred_username || user?.email || 'User';
    let hash = 0;
    for (let i = 0; i < name.length; i++) {
      hash = name.charCodeAt(i) + ((hash << 5) - hash);
    }
    
    // Generate a pleasant color from the hash
    const colors = [
      '#10b981', '#60a5fa', '#f59e0b', '#ef4444', '#8b5cf6',
      '#06b6d4', '#f97316', '#84cc16', '#ec4899', '#6366f1'
    ];
    
    return colors[Math.abs(hash) % colors.length];
  };

  return (
    <div className="avatar-menu" ref={menuRef}>
      <div 
        className="avatar-button" 
        onClick={toggleMenu}
        style={{ backgroundColor: getAvatarColor() }}
      >
        {user?.avatar_url ? (
          <img src={user.avatar_url} alt="User Avatar" className="avatar-image" />
        ) : (
          <span className="avatar-initials">{getInitials()}</span>
        )}
        <div className="avatar-status-indicator"></div>
      </div>

      {isOpen && (
        <div className="avatar-dropdown">
          <div className="dropdown-header">
            <div className="user-info">
              <div className="user-name">
                {user?.name || user?.preferred_username || t('common.user')}
              </div>
              <div className="user-email">{user?.email}</div>
              {user?.role && (
                <div className="user-role">
                  <span className="role-badge">{user.role}</span>
                </div>
              )}
            </div>
          </div>

          <div className="dropdown-divider"></div>

          <div className="dropdown-menu">
            <Link 
              to="/profile" 
              className="dropdown-item"
              onClick={() => setIsOpen(false)}
            >
              <svg className="dropdown-icon" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
              </svg>
              {t('navbar.profile')}
            </Link>

            <Link 
              to="/sounds" 
              className="dropdown-item"
              onClick={() => setIsOpen(false)}
            >
              <svg className="dropdown-icon" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.707.707L4.586 13H2a1 1 0 01-1-1V8a1 1 0 011-1h2.586l3.707-3.707a1 1 0 011.09-.217zM15.657 6.343a1 1 0 011.414 0A9.972 9.972 0 0119 12a9.972 9.972 0 01-1.929 5.657 1 1 0 11-1.414-1.414A7.971 7.971 0 0017 12a7.971 7.971 0 00-1.343-4.243 1 1 0 010-1.414z" clipRule="evenodd" />
                <path fillRule="evenodd" d="M13.828 8.172a1 1 0 011.414 0A5.983 5.983 0 0117 12a5.983 5.983 0 01-1.758 3.828 1 1 0 11-1.414-1.414A3.987 3.987 0 0015 12a3.987 3.987 0 00-1.172-2.828 1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
              {t('navbar.sounds')}
            </Link>

            <Link 
              to="/dashboard" 
              className="dropdown-item"
              onClick={() => setIsOpen(false)}
            >
              <svg className="dropdown-icon" viewBox="0 0 20 20" fill="currentColor">
                <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z" />
              </svg>
              {t('common.dashboard', 'Dashboard')}
            </Link>

            {user?.role === 'super_admin' && (
              <Link 
                to="/admin" 
                className="dropdown-item admin-item"
                onClick={() => setIsOpen(false)}
              >
                <svg className="dropdown-icon" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
                </svg>
                {t('navbar.admin')}
              </Link>
            )}

            <div className="dropdown-divider"></div>

            <div className="dropdown-item settings-item">
              <svg className="dropdown-icon" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
              </svg>
              {t('common.settings', 'Settings')}
            </div>

            <div className="dropdown-item help-item">
              <svg className="dropdown-icon" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
              </svg>
              {t('common.help', 'Help & Support')}
            </div>

            <div className="dropdown-divider"></div>

            <button 
              onClick={handleLogout} 
              className="dropdown-item logout-item"
            >
              <svg className="dropdown-icon" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M3 3a1 1 0 00-1 1v12a1 1 0 102 0V4a1 1 0 00-1-1zm10.293 9.293a1 1 0 001.414 1.414l3-3a1 1 0 000-1.414l-3-3a1 1 0 10-1.414 1.414L14.586 9H7a1 1 0 100 2h7.586l-1.293 1.293z" clipRule="evenodd" />
              </svg>
              {t('navbar.signOut')}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default AvatarMenu;
