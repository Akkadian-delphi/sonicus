import React from "react";
import { useTranslation } from "react-i18next";
import { useAuth } from "../hooks/useAuth";
import "../styles/SubscriptionModal.css";

function SubscriptionModal({ isOpen, onClose }) {
  const { t } = useTranslation();
  const { isAuthenticated } = useAuth();

  const handleSubscribe = (tierName) => {
    // TODO: Implement subscription logic
    console.log(`Subscribe to ${tierName} plan`);
    onClose();
  };

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="subscription-modal-overlay" onClick={handleOverlayClick}>
      <div className="subscription-modal">
        <div className="modal-header">
          <h2 className="modal-title">{t('pricing.chooseYourPlan')}</h2>
          <button className="modal-close" onClick={onClose}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>

        <div className="modal-content">
          <div className="modal-subscription-tiers">
            {/* Starter Tier */}
            <div className="modal-tier-card">
              <h3>{t('homepage.subscriptionTiers.starter.name')}</h3>
              <div className="modal-price">
                <span className="modal-amount">{t('homepage.subscriptionTiers.starter.price')}</span>
              </div>
              <ul className="modal-features-list">
                <li>{t('homepage.subscriptionTiers.starter.features.sessions')}</li>
                <li>{t('homepage.subscriptionTiers.starter.features.timeLimit')}</li>
                <li>{t('homepage.subscriptionTiers.starter.features.content')}</li>
                <li>{t('homepage.subscriptionTiers.starter.features.analytics')}</li>
              </ul>
              <button 
                className="modal-tier-cta modal-tier-cta-free"
                onClick={() => handleSubscribe('starter')}
              >
                {isAuthenticated ? t('pricing.currentPlan') : t('pricing.getStarted')}
              </button>
            </div>

            {/* Premium Tier */}
            <div className="modal-tier-card modal-featured">
              <div className="modal-popular-badge">⭐ {t('pricing.mostPopular')}</div>
              <h3>{t('homepage.subscriptionTiers.premium.name')}</h3>
              <div className="modal-price">
                <span className="modal-amount">{t('homepage.subscriptionTiers.premium.price')}</span>
              </div>
              <ul className="modal-features-list">
                <li>{t('homepage.subscriptionTiers.premium.features.sessions')}</li>
                <li>{t('homepage.subscriptionTiers.premium.features.timeLimit')}</li>
                <li>{t('homepage.subscriptionTiers.premium.features.content')}</li>
                <li>{t('homepage.subscriptionTiers.premium.features.analytics')}</li>
                <li>{t('homepage.subscriptionTiers.premium.features.tracking')}</li>
              </ul>
              <button 
                className="modal-tier-cta modal-tier-cta-premium"
                onClick={() => handleSubscribe('premium')}
              >
                {t('pricing.upgradeToPremium')}
              </button>
            </div>

            {/* Pro Tier */}
            <div className="modal-tier-card">
              <h3>{t('homepage.subscriptionTiers.pro.name')}</h3>
              <div className="modal-price">
                <span className="modal-amount">{t('homepage.subscriptionTiers.pro.price')}</span>
              </div>
              <ul className="modal-features-list">
                <li>{t('homepage.subscriptionTiers.pro.features.sessions')}</li>
                <li>{t('homepage.subscriptionTiers.pro.features.timeLimit')}</li>
                <li>{t('homepage.subscriptionTiers.pro.features.content')}</li>
                <li>{t('homepage.subscriptionTiers.pro.features.insights')}</li>
                <li>{t('homepage.subscriptionTiers.pro.features.support')}</li>
              </ul>
              <button 
                className="modal-tier-cta modal-tier-cta-pro"
                onClick={() => handleSubscribe('pro')}
              >
                {t('pricing.upgradeToPro')}
              </button>
            </div>
          </div>

          <div className="modal-footer">
            <div className="modal-guarantee">
              <span className="guarantee-icon">🛡️</span>
              <span>{t('pricing.guarantee.noCommitment')} • {t('pricing.guarantee.securePayments')}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SubscriptionModal;
