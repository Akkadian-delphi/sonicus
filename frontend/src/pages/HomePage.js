import React, { useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../hooks/useAuth";
import { getDashboardRoute } from "../utils/roleBasedRedirect";
import "../styles/HomePage.css";

function HomePage() {
  const { t } = useTranslation();
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    // If user is authenticated, redirect to their personal dashboard
    if (isAuthenticated && user) {
      const dashboardRoute = getDashboardRoute(user);
      navigate(dashboardRoute);
    }
  }, [isAuthenticated, user, navigate]);

  return (
    <div className="home-page">
      <div className="home-content">
        <div className="landing-page">
        
        {/* Show personalized content for authenticated users */}
        {isAuthenticated && user && (
          <div style={{
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            color: 'white',
            padding: '20px',
            borderRadius: '12px',
            marginBottom: '30px',
            textAlign: 'center'
          }}>
            <h2 style={{ margin: '0 0 10px 0' }}>{t('navbar.welcome', { name: user.email })}</h2>
            <div style={{ display: 'flex', gap: '15px', justifyContent: 'center', flexWrap: 'wrap', marginTop: '15px' }}>
              <Link 
                to="/profile" 
                className="btn" 
                style={{
                  background: 'rgba(255,255,255,0.2)',
                  color: 'white',
                  border: '1px solid rgba(255,255,255,0.3)',
                  textDecoration: 'none'
                }}
              >
                {t('homepage.cta.myDashboard')}
              </Link>
              <Link 
                to="/sounds" 
                className="btn" 
                style={{
                  background: 'rgba(255,255,255,0.2)',
                  color: 'white',
                  border: '1px solid rgba(255,255,255,0.3)',
                  textDecoration: 'none'
                }}
              >
                {t('homepage.cta.exploreSound')}
              </Link>
            </div>
          </div>
        )}
        
        <header className="hero-section">
          <div className="hero-logo">
            <img src="/logo-colorida.png" alt="Sonicus" className="hero-logo-image" />
          </div>
          <h1 className="hero-title">Sonicus</h1>
          <p className="hero-subtitle">{t('homepage.hero.title')}</p>
          <p className="hero-description">
            {t('homepage.hero.subtitle')}
          </p>
          <div className="hero-highlights">
            <span className="highlight">🎧 {t('homepage.features.professional.title')}</span>
            <span className="highlight">🔬 {t('homepage.features.scientifically.title')}</span>
            <span className="highlight">🌿 {t('homepage.features.naturalHealing.title')}</span>
            <span className="highlight">📱 {t('homepage.features.accessible.title')}</span>
          </div>
        </header>

          <section className="what-we-do-section">
            <h2>{t('homepage.whatWeDo.title')}</h2>
            <div className="description-block">
              <p className="main-description">
                <strong>{t('homepage.whatWeDo.description')}</strong>
              </p>
            </div>
            
            <div className="key-benefits">
              <h3>{t('homepage.whatWeDo.keyBenefits.title')}</h3>
              <ul className="benefits-list">
                <li><strong>{t('homepage.whatWeDo.keyBenefits.stressReduction.title')}</strong> {t('homepage.whatWeDo.keyBenefits.stressReduction.description')}</li>
                <li><strong>{t('homepage.whatWeDo.keyBenefits.betterSleep.title')}</strong> {t('homepage.whatWeDo.keyBenefits.betterSleep.description')}</li>
                <li><strong>{t('homepage.whatWeDo.keyBenefits.enhancedFocus.title')}</strong> {t('homepage.whatWeDo.keyBenefits.enhancedFocus.description')}</li>
                <li><strong>{t('homepage.whatWeDo.keyBenefits.emotionalBalance.title')}</strong> {t('homepage.whatWeDo.keyBenefits.emotionalBalance.description')}</li>
                <li><strong>{t('homepage.whatWeDo.keyBenefits.painManagement.title')}</strong> {t('homepage.whatWeDo.keyBenefits.painManagement.description')}</li>
                <li><strong>{t('homepage.whatWeDo.keyBenefits.meditationSupport.title')}</strong> {t('homepage.whatWeDo.keyBenefits.meditationSupport.description')}</li>
              </ul>
            </div>
          </section>

          <section className="features-section">
            <h2>{t('homepage.howItWorks.title')}</h2>
            <div className="features-grid">
              <div className="feature-card">
                <h3>{t('homepage.howItWorks.curatedLibrary.title')}</h3>
                <p>{t('homepage.howItWorks.curatedLibrary.description')}</p>
              </div>
              <div className="feature-card">
                <h3>{t('homepage.howItWorks.evidenceBased.title')}</h3>
                <p>{t('homepage.howItWorks.evidenceBased.description')}</p>
              </div>
              <div className="feature-card">
                <h3>{t('homepage.howItWorks.instantStreaming.title')}</h3>
                <p>{t('homepage.howItWorks.instantStreaming.description')}</p>
              </div>
              <div className="feature-card">
                <h3>{t('homepage.howItWorks.personalJourney.title')}</h3>
                <p>{t('homepage.howItWorks.personalJourney.description')}</p>
              </div>
              <div className="feature-card">
                <h3>{t('homepage.howItWorks.privateSecure.title')}</h3>
                <p>{t('homepage.howItWorks.privateSecure.description')}</p>
              </div>
              <div className="feature-card">
                <h3>{t('homepage.howItWorks.smartRecommendations.title')}</h3>
                <p>{t('homepage.howItWorks.smartRecommendations.description')}</p>
              </div>
            </div>
          </section>

                    <section className="features-section">
            <h2>{t('homepage.features.title')}</h2>
            <div className="features-grid">
              <div className="use-case">
                <h4>🌙 {t('homepage.features.useCases.sleep.title')}</h4>
                <p>{t('homepage.features.useCases.sleep.description')}</p>
              </div>
              <div className="use-case">
                <h4>😰 {t('homepage.features.useCases.stress.title')}</h4>
                <p>{t('homepage.features.useCases.stress.description')}</p>
              </div>
              <div className="use-case">
                <h4>🧘‍♀️ {t('homepage.features.useCases.meditation.title')}</h4>
                <p>{t('homepage.features.useCases.meditation.description')}</p>
              </div>
              <div className="use-case">
                <h4>💼 {t('homepage.features.useCases.workplace.title')}</h4>
                <p>{t('homepage.features.useCases.workplace.description')}</p>
              </div>
              <div className="use-case">
                <h4>🏥 {t('homepage.features.useCases.recovery.title')}</h4>
                <p>{t('homepage.features.useCases.recovery.description')}</p>
              </div>
              <div className="use-case">
                <h4>🎓 {t('homepage.features.useCases.study.title')}</h4>
                <p>{t('homepage.features.useCases.study.description')}</p>
              </div>
            </div>
          </section>

          <section className="cta-section">
            <h2>{t('homepage.cta.title')}</h2>
            <p className="cta-description">
              {isAuthenticated 
                ? t('homepage.cta.authenticatedDescription')
                : t('homepage.cta.guestDescription')
              }
            </p>
            
            {/* B2C Subscription Tiers */}
            {!isAuthenticated && (
              <div className="subscription-tiers">
                <div className="tier-card">
                  <h3>{t('homepage.subscriptionTiers.starter.name')}</h3>
                  <div className="price">{t('homepage.subscriptionTiers.starter.price')}</div>
                  <ul>
                    <li>{t('homepage.subscriptionTiers.starter.features.sessions')}</li>
                    <li>{t('homepage.subscriptionTiers.starter.features.timeLimit')}</li>
                    <li>{t('homepage.subscriptionTiers.starter.features.content')}</li>
                    <li>{t('homepage.subscriptionTiers.starter.features.analytics')}</li>
                  </ul>
                </div>
                <div className="tier-card featured">
                  <h3>{t('homepage.subscriptionTiers.premium.name')}</h3>
                  <div className="price">{t('homepage.subscriptionTiers.premium.price')}</div>
                  <ul>
                    <li>{t('homepage.subscriptionTiers.premium.features.sessions')}</li>
                    <li>{t('homepage.subscriptionTiers.premium.features.timeLimit')}</li>
                    <li>{t('homepage.subscriptionTiers.premium.features.content')}</li>
                    <li>{t('homepage.subscriptionTiers.premium.features.analytics')}</li>
                    <li>{t('homepage.subscriptionTiers.premium.features.tracking')}</li>
                  </ul>
                </div>
                <div className="tier-card">
                  <h3>{t('homepage.subscriptionTiers.pro.name')}</h3>
                  <div className="price">{t('homepage.subscriptionTiers.pro.price')}</div>
                  <ul>
                    <li>{t('homepage.subscriptionTiers.pro.features.sessions')}</li>
                    <li>{t('homepage.subscriptionTiers.pro.features.timeLimit')}</li>
                    <li>{t('homepage.subscriptionTiers.pro.features.content')}</li>
                    <li>{t('homepage.subscriptionTiers.pro.features.insights')}</li>
                    <li>{t('homepage.subscriptionTiers.pro.features.support')}</li>
                  </ul>
                </div>
              </div>
            )}

            <div className="cta-buttons">
              {isAuthenticated ? (
                <>
                  <Link to="/sounds" className="btn btn-primary">{t('homepage.cta.buttons.exploreSounds')}</Link>
                  <Link to="/profile" className="btn btn-secondary">{t('homepage.cta.buttons.dashboard')}</Link>
                </>
              ) : (
                <>
                  <Link to="/register" className="btn btn-primary">{t('homepage.cta.buttons.startTrial')}</Link>
                  <Link to="/login" className="btn btn-secondary">{t('homepage.cta.buttons.signIn')}</Link>
                </>
              )}
            </div>
          </section>

          <section className="info-section">
            <div className="info-card">
              <h3>{t('homepage.science.title')}</h3>
              <p>
                <strong>{t('homepage.science.intro')}</strong> {t('homepage.science.description')}
              </p>
              <div className="research-highlights">
                <span className="research-point">📊 {t('homepage.science.highlights.stressReduction')}</span>
                <span className="research-point">🧠 {t('homepage.science.highlights.neuroplasticity')}</span>
                <span className="research-point">💤 {t('homepage.science.highlights.sleep')}</span>
                <span className="research-point">🎯 {t('homepage.science.highlights.cognitive')}</span>
              </div>
            </div>
          </section>

          <footer className="app-info">
            <p className="version">{t('common.footer.version')}</p>
            <p className="tagline">{t('common.footer.tagline')}</p>
          </footer>
        </div>
      </div>
    </div>
  );
}

export default HomePage;
