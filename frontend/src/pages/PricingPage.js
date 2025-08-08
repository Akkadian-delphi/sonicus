import React from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../hooks/useAuth";
import "../styles/PricingPage.css";

function PricingPage() {
  const { t } = useTranslation();
  const { isAuthenticated } = useAuth();

  const handleSubscribe = (tierName) => {
    // TODO: Implement subscription logic
    // For now, just show an alert
    alert(t('pricing.redirectingToSubscription', { plan: tierName }));
  };

  return (
    <div className="pricing-page">
      <div className="pricing-container">
        <header className="pricing-header">
          <div className="pricing-hero">
            <h1 className="pricing-title">{t('pricing.title')}</h1>
            <p className="pricing-subtitle">{t('pricing.subtitle')}</p>
            <div className="pricing-benefits">
              <span className="benefit">🎧 {t('homepage.features.professional.title')}</span>
              <span className="benefit">🔬 {t('homepage.features.scientifically.title')}</span>
              <span className="benefit">🌿 {t('homepage.features.naturalHealing.title')}</span>
              <span className="benefit">📱 {t('homepage.features.accessible.title')}</span>
            </div>
          </div>
        </header>

        <section className="subscription-section">
          <h2 className="section-title">{t('pricing.chooseYourPlan')}</h2>
          <div className="subscription-tiers">
            {/* Starter Tier */}
            <div className="tier-card">
              <h3>{t('homepage.subscriptionTiers.starter.name')}</h3>
              <div className="price">
                <span className="amount">{t('homepage.subscriptionTiers.starter.price')}</span>
              </div>
              <ul className="features-list">
                <li>{t('homepage.subscriptionTiers.starter.features.sessions')}</li>
                <li>{t('homepage.subscriptionTiers.starter.features.timeLimit')}</li>
                <li>{t('homepage.subscriptionTiers.starter.features.content')}</li>
                <li>{t('homepage.subscriptionTiers.starter.features.analytics')}</li>
              </ul>
              <button 
                className="tier-cta tier-cta-free"
                onClick={() => handleSubscribe('starter')}
              >
                {isAuthenticated ? t('pricing.currentPlan') : t('pricing.getStarted')}
              </button>
            </div>

            {/* Premium Tier */}
            <div className="tier-card featured" data-most-popular={t('pricing.mostPopular')}>
              <h3>{t('homepage.subscriptionTiers.premium.name')}</h3>
              <div className="price">
                <span className="amount">{t('homepage.subscriptionTiers.premium.price')}</span>
              </div>
              <ul className="features-list">
                <li>{t('homepage.subscriptionTiers.premium.features.sessions')}</li>
                <li>{t('homepage.subscriptionTiers.premium.features.timeLimit')}</li>
                <li>{t('homepage.subscriptionTiers.premium.features.content')}</li>
                <li>{t('homepage.subscriptionTiers.premium.features.analytics')}</li>
                <li>{t('homepage.subscriptionTiers.premium.features.tracking')}</li>
              </ul>
              <button 
                className="tier-cta tier-cta-premium"
                onClick={() => handleSubscribe('premium')}
              >
                {t('pricing.upgradeToPremium')}
              </button>
            </div>

            {/* Pro Tier */}
            <div className="tier-card">
              <h3>{t('homepage.subscriptionTiers.pro.name')}</h3>
              <div className="price">
                <span className="amount">{t('homepage.subscriptionTiers.pro.price')}</span>
              </div>
              <ul className="features-list">
                <li>{t('homepage.subscriptionTiers.pro.features.sessions')}</li>
                <li>{t('homepage.subscriptionTiers.pro.features.timeLimit')}</li>
                <li>{t('homepage.subscriptionTiers.pro.features.content')}</li>
                <li>{t('homepage.subscriptionTiers.pro.features.insights')}</li>
                <li>{t('homepage.subscriptionTiers.pro.features.support')}</li>
              </ul>
              <button 
                className="tier-cta tier-cta-pro"
                onClick={() => handleSubscribe('pro')}
              >
                {t('pricing.upgradeToPro')}
              </button>
            </div>
          </div>
        </section>

        <section className="pricing-faq">
          <h2 className="section-title">{t('pricing.faq.title')}</h2>
          <div className="faq-grid">
            <div className="faq-item">
              <h4>{t('pricing.faq.billing.question')}</h4>
              <p>{t('pricing.faq.billing.answer')}</p>
            </div>
            <div className="faq-item">
              <h4>{t('pricing.faq.cancel.question')}</h4>
              <p>{t('pricing.faq.cancel.answer')}</p>
            </div>
            <div className="faq-item">
              <h4>{t('pricing.faq.trial.question')}</h4>
              <p>{t('pricing.faq.trial.answer')}</p>
            </div>
            <div className="faq-item">
              <h4>{t('pricing.faq.support.question')}</h4>
              <p>{t('pricing.faq.support.answer')}</p>
            </div>
          </div>
        </section>

        <section className="pricing-guarantee">
          <div className="guarantee-card">
            <div className="guarantee-icon">🛡️</div>
            <h3>{t('pricing.guarantee.title')}</h3>
            <p>{t('pricing.guarantee.description')}</p>
            <div className="guarantee-features">
              <span>✨ {t('pricing.guarantee.noCommitment')}</span>
              <span>💳 {t('pricing.guarantee.securePayments')}</span>
              <span>🔒 {t('pricing.guarantee.dataProtection')}</span>
            </div>
          </div>
        </section>

        {!isAuthenticated && (
          <section className="pricing-cta">
            <h2>{t('pricing.readyToStart')}</h2>
            <p>{t('pricing.joinThousands')}</p>
            <div className="cta-buttons">
              <Link to="/register" className="btn btn-primary">{t('pricing.startFreeTrial')}</Link>
              <Link to="/login" className="btn btn-secondary">{t('pricing.signIn')}</Link>
            </div>
          </section>
        )}

        <footer className="pricing-footer">
          <p>{t('common.footer.version')}</p>
          <p>{t('common.footer.tagline')}</p>
        </footer>
      </div>
    </div>
  );
}

export default PricingPage;
