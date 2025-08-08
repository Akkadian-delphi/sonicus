import React from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../hooks/useAuth";
import LanguageSwitcher from "./LanguageSwitcher";
import AvatarMenu from "./AvatarMenu";
import "../styles/Navbar.css";

function Navbar() {
  const { t } = useTranslation();
  const { isAuthenticated, loading } = useAuth();

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
              <LanguageSwitcher />
              <AvatarMenu />
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
