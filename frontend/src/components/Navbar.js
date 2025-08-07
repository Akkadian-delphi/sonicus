import React from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../hooks/useAuth";
import LanguageSwitcher from "./LanguageSwitcher";
import "../styles/Navbar.css";

function Navbar() {
  const { t } = useTranslation();
  const { user, logout, isAuthenticated, loading } = useAuth();

  const handleLogout = async () => {
    await logout();
  };

  // Don't render anything while loading
  if (loading) {
    return null;
  }

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/" className="navbar-logo">
          <img 
            src="/logo-colorida.png" 
            alt="Sonicus - Therapeutic Sound Healing"
            className="logo-image"
          />
        </Link>
        
        <div className="navbar-auth">
          {isAuthenticated ? (
            <>
              <Link to="/sounds" className="navbar-link">
                {t('navbar.sounds')}
              </Link>
              <Link to="/profile" className="navbar-link">
                {t('navbar.profile')}
              </Link>
              {user?.role === 'super_admin' && (
                <Link to="/admin" className="navbar-link admin-link">
                  {t('navbar.admin')}
                </Link>
              )}
              <span className="user-info">
                {t('navbar.welcome', { name: user.email || user.preferred_username || 'User' })}
                {user.role && ` (${user.role})`}
              </span>
              <button onClick={handleLogout} className="auth-button logout-btn">
                {t('navbar.signOut')}
              </button>
              <LanguageSwitcher />
            </>
          ) : (
            <>
              <Link to="/login" className="auth-button login-btn">
                {t('navbar.signIn')}
              </Link>
              <Link to="/register" className="auth-button register-btn">
                {t('navbar.getStarted')}
              </Link>
              <LanguageSwitcher />
            </>
          )}
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
