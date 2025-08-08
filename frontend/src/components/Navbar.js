import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../hooks/useAuth";
import LanguageSwitcher from "./LanguageSwitcher";
import AvatarMenu from "./AvatarMenu";
import SubscriptionModal from "./SubscriptionModal";
import "../styles/Navbar.css";

function Navbar() {
  const { t } = useTranslation();
  const { isAuthenticated, loading } = useAuth();
  const [isSubscriptionModalOpen, setIsSubscriptionModalOpen] = useState(false);

  // Don't render anything while loading
  if (loading) {
    return null;
  }

  return (
    <>
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
                <Link to="/pricing" className="navbar-link pricing-link">
                  {t('navbar.pricing')}
                </Link>
                <button 
                  className="upgrade-btn"
                  onClick={() => setIsSubscriptionModalOpen(true)}
                  title={t('navbar.upgradePlan')}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 2L15.09 8.26L22 9L17 14L18.18 21L12 17.77L5.82 21L7 14L2 9L8.91 8.26L12 2Z"/>
                  </svg>
                  {t('navbar.upgrade')}
                </button>
                <LanguageSwitcher />
                <AvatarMenu />
              </>
            ) : (
              <>
                <Link to="/pricing" className="navbar-link pricing-link">
                  {t('navbar.pricing')}
                </Link>
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

      <SubscriptionModal 
        isOpen={isSubscriptionModalOpen} 
        onClose={() => setIsSubscriptionModalOpen(false)} 
      />
    </>
  );
}

export default Navbar;
