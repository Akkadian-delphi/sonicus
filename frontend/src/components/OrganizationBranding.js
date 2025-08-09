import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useTenant } from '../context/TenantContext';
import axios from 'axios';
import './OrganizationBranding.css';

const OrganizationBranding = () => {
  const { t } = useTranslation();
  const { isB2B2CMode, organizationInfo, updateOrganizationBranding } = useTenant();
  
  const [branding, setBranding] = useState({
    colors: {
      primary: '#3B82F6',
      secondary: '#64748B',
      accent: '#10B981',
      background: '#FFFFFF',
      text: '#1F2937'
    },
    typography: {
      font_family: 'Inter, sans-serif',
      heading_font: 'Inter, sans-serif'
    },
    layout: {
      sidebar_style: 'default',
      theme_mode: 'light'
    },
    logo_url: null,
    custom_css: ''
  });
  
  const [presets, setPresets] = useState({});
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('colors');

  // Apply branding to preview in real-time
  useEffect(() => {
    const root = document.documentElement;
    
    // Apply CSS variables
    root.style.setProperty('--color-primary', branding.colors.primary);
    root.style.setProperty('--color-secondary', branding.colors.secondary);
    root.style.setProperty('--color-accent', branding.colors.accent);
    root.style.setProperty('--color-background', branding.colors.background);
    root.style.setProperty('--color-text', branding.colors.text);
    root.style.setProperty('--font-font-family', branding.typography.font_family);
    root.style.setProperty('--font-heading-font', branding.typography.heading_font);
    
    // Apply theme mode to body class
    document.body.classList.remove('theme-light', 'theme-dark', 'theme-auto');
    document.body.classList.add(`theme-${branding.layout.theme_mode}`);
    
    // Handle auto theme mode
    if (branding.layout.theme_mode === 'auto') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      const handleThemeChange = (e) => {
        document.body.classList.toggle('theme-dark-active', e.matches);
        document.body.classList.toggle('theme-light-active', !e.matches);
      };
      
      handleThemeChange(mediaQuery);
      mediaQuery.addEventListener('change', handleThemeChange);
      
      return () => mediaQuery.removeEventListener('change', handleThemeChange);
    }
  }, [branding]);

  const loadBranding = async () => {
    try {
      const response = await axios.get('/api/v1/organization/branding/');
      setBranding(response.data);
    } catch (error) {
      console.error('Failed to load branding:', error);
    }
  };

  const loadPresets = async () => {
    try {
      const response = await axios.get('/api/v1/organization/branding/presets');
      setPresets(response.data);
    } catch (error) {
      console.error('Failed to load presets:', error);
    }
  };

  const handleColorChange = (colorKey, value) => {
    setBranding(prev => ({
      ...prev,
      colors: {
        ...prev.colors,
        [colorKey]: value
      }
    }));
    generatePreview();
  };

  const handleTypographyChange = (key, value) => {
    setBranding(prev => ({
      ...prev,
      typography: {
        ...prev.typography,
        [key]: value
      }
    }));
    generatePreview();
  };

  const handleLayoutChange = (key, value) => {
    setBranding(prev => ({
      ...prev,
      layout: {
        ...prev.layout,
        [key]: value
      }
    }));
    generatePreview();
  };

  const handleCustomCSSChange = (value) => {
    setBranding(prev => ({
      ...prev,
      custom_css: value
    }));
    generatePreview();
  };

  const generatePreview = async () => {
    try {
      const response = await axios.post('/api/v1/organization/branding/preview', branding);
      setPreview(response.data);
    } catch (error) {
      console.error('Failed to generate preview:', error);
    }
  };

  const applyPreset = (presetKey) => {
    const preset = presets[presetKey];
    if (preset) {
      setBranding(prev => ({
        ...prev,
        colors: preset.colors,
        typography: preset.typography,
        layout: preset.layout || prev.layout
      }));
      generatePreview();
    }
  };

  const saveBranding = async () => {
    setLoading(true);
    try {
      const response = await axios.post('/api/v1/organization/branding/', branding);
      
      // Update the global branding context
      if (updateOrganizationBranding) {
        updateOrganizationBranding(response.data.data);
      }
      
      // Apply CSS variables immediately
      applyCSSVariables(branding.colors, branding.typography);
      
      alert(t('branding.save.success', 'Branding updated successfully!'));
    } catch (error) {
      console.error('Failed to save branding:', error);
      alert(t('branding.save.error', 'Failed to save branding changes.'));
    } finally {
      setLoading(false);
    }
  };

  const applyCSSVariables = (colors, typography) => {
    const root = document.documentElement;
    
    // Apply color variables
    Object.entries(colors).forEach(([key, value]) => {
      root.style.setProperty(`--color-${key.replace('_', '-')}`, value);
    });
    
    // Apply typography variables
    Object.entries(typography).forEach(([key, value]) => {
      root.style.setProperty(`--font-${key.replace('_', '-')}`, value);
    });
  };

  const resetToDefaults = () => {
    setBranding({
      colors: {
        primary: '#3B82F6',
        secondary: '#64748B',
        accent: '#10B981',
        background: '#FFFFFF',
        text: '#1F2937'
      },
      typography: {
        font_family: 'Inter, sans-serif',
        heading_font: 'Inter, sans-serif'
      },
      layout: {
        sidebar_style: 'default',
        theme_mode: 'light'
      },
      logo_url: null,
      custom_css: ''
    });
    generatePreview();
  };

  if (!isB2B2CMode) {
    return (
      <div className="branding-not-available">
        <h3>{t('branding.error.b2cMode', 'Organization Branding Not Available')}</h3>
        <p>{t('branding.error.b2cModeDesc', 'This feature is only available for business organizations.')}</p>
      </div>
    );
  }

  return (
    <div className="organization-branding">
      <div className="branding-header">
        <h2>{t('branding.title', 'Organization Branding')}</h2>
        <p className="branding-subtitle">
          {t('branding.subtitle', 'Customize your organization\'s appearance and branding')}
        </p>
      </div>

      <div className="branding-container">
        {/* Left Panel - Controls */}
        <div className="branding-controls">
          {/* Navigation Tabs */}
          <div className="branding-tabs">
            <button 
              className={`tab ${activeTab === 'colors' ? 'active' : ''}`}
              onClick={() => setActiveTab('colors')}
            >
              {t('branding.tabs.colors', 'Colors')}
            </button>
            <button 
              className={`tab ${activeTab === 'typography' ? 'active' : ''}`}
              onClick={() => setActiveTab('typography')}
            >
              {t('branding.tabs.typography', 'Typography')}
            </button>
            <button 
              className={`tab ${activeTab === 'presets' ? 'active' : ''}`}
              onClick={() => setActiveTab('presets')}
            >
              {t('branding.tabs.presets', 'Presets')}
            </button>
            <button 
              className={`tab ${activeTab === 'advanced' ? 'active' : ''}`}
              onClick={() => setActiveTab('advanced')}
            >
              {t('branding.tabs.advanced', 'Advanced')}
            </button>
          </div>

          {/* Tab Content */}
          <div className="tab-content">
            {/* Colors Tab */}
            {activeTab === 'colors' && (
              <div className="colors-section">
                <h3>{t('branding.colors.title', 'Brand Colors')}</h3>
                <div className="color-controls">
                  {Object.entries(branding.colors).map(([key, value]) => (
                    <div key={key} className="color-control">
                      <label>
                        {t(`branding.colors.${key}`, key.charAt(0).toUpperCase() + key.slice(1))}
                      </label>
                      <div className="color-input-group">
                        <input
                          type="color"
                          value={value}
                          onChange={(e) => handleColorChange(key, e.target.value)}
                          className="color-picker"
                        />
                        <input
                          type="text"
                          value={value}
                          onChange={(e) => handleColorChange(key, e.target.value)}
                          className="color-text"
                          placeholder="#000000"
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Typography Tab */}
            {activeTab === 'typography' && (
              <div className="typography-section">
                <h3>{t('branding.typography.title', 'Typography')}</h3>
                <div className="typography-controls">
                  <div className="typography-control">
                    <label>{t('branding.typography.primaryFont', 'Primary Font')}</label>
                    <select
                      value={branding.typography.font_family}
                      onChange={(e) => handleTypographyChange('font_family', e.target.value)}
                    >
                      <option value="Inter, sans-serif">Inter</option>
                      <option value="Roboto, sans-serif">Roboto</option>
                      <option value="Poppins, sans-serif">Poppins</option>
                      <option value="Nunito, sans-serif">Nunito</option>
                      <option value="Open Sans, sans-serif">Open Sans</option>
                      <option value="Lato, sans-serif">Lato</option>
                    </select>
                  </div>
                  <div className="typography-control">
                    <label>{t('branding.typography.headingFont', 'Heading Font')}</label>
                    <select
                      value={branding.typography.heading_font}
                      onChange={(e) => handleTypographyChange('heading_font', e.target.value)}
                    >
                      <option value="Inter, sans-serif">Inter</option>
                      <option value="Roboto, sans-serif">Roboto</option>
                      <option value="Poppins, sans-serif">Poppins</option>
                      <option value="Nunito, sans-serif">Nunito</option>
                      <option value="Playfair Display, serif">Playfair Display</option>
                      <option value="Roboto Slab, serif">Roboto Slab</option>
                    </select>
                  </div>
                  <div className="typography-control">
                    <label>{t('branding.layout.themeMode', 'Theme Mode')}</label>
                    <select
                      value={branding.layout.theme_mode}
                      onChange={(e) => handleLayoutChange('theme_mode', e.target.value)}
                    >
                      <option value="light">{t('branding.layout.light', 'Light')}</option>
                      <option value="dark">{t('branding.layout.dark', 'Dark')}</option>
                      <option value="auto">{t('branding.layout.auto', 'Auto (System)')}</option>
                    </select>
                  </div>
                </div>
              </div>
            )}

            {/* Presets Tab */}
            {activeTab === 'presets' && (
              <div className="presets-section">
                <h3>{t('branding.presets.title', 'Theme Presets')}</h3>
                <div className="preset-grid">
                  {Object.entries(presets).map(([key, preset]) => (
                    <div key={key} className="preset-card" onClick={() => applyPreset(key)}>
                      <div className="preset-preview">
                        <div 
                          className="preset-color-bar"
                          style={{
                            background: `linear-gradient(90deg, ${preset.colors?.primary}, ${preset.colors?.accent})`
                          }}
                        />
                      </div>
                      <div className="preset-info">
                        <h4>{preset.name}</h4>
                        <p>{preset.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Advanced Tab */}
            {activeTab === 'advanced' && (
              <div className="advanced-section">
                <h3>{t('branding.advanced.title', 'Advanced Customization')}</h3>
                <div className="advanced-controls">
                  <div className="advanced-control">
                    <label>{t('branding.advanced.customCSS', 'Custom CSS')}</label>
                    <textarea
                      value={branding.custom_css}
                      onChange={(e) => handleCustomCSSChange(e.target.value)}
                      rows={10}
                      placeholder={t('branding.advanced.cssPlaceholder', 'Enter custom CSS rules...')}
                      className="custom-css-textarea"
                    />
                    <p className="help-text">
                      {t('branding.advanced.cssHelp', 'Add custom CSS to further customize your organization\'s appearance.')}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="branding-actions">
            <button onClick={resetToDefaults} className="btn btn-secondary">
              {t('branding.actions.reset', 'Reset to Defaults')}
            </button>
            <button 
              onClick={saveBranding} 
              className="btn btn-primary"
              disabled={loading}
            >
              {loading ? t('common.saving', 'Saving...') : t('branding.actions.save', 'Save Changes')}
            </button>
          </div>
        </div>

        {/* Right Panel - Preview */}
        <div className="branding-preview">
          <h3>{t('branding.preview.title', 'Live Preview')}</h3>
          <div className="preview-container org-branded" style={{
            '--color-primary': branding.colors.primary,
            '--color-secondary': branding.colors.secondary,
            '--color-accent': branding.colors.accent,
            '--color-background': branding.colors.background,
            '--color-text': branding.colors.text,
            '--font-font-family': branding.typography.font_family,
            '--font-heading-font': branding.typography.heading_font
          }}>
            {/* Sample content to show the branding */}
            <div className="preview-header">
              <h1>{t('branding.preview.sampleTitle', 'Your Organization Portal')}</h1>
              <p>{t('branding.preview.sampleSubtitle', 'This is how your branding will appear to users')}</p>
            </div>
            
            <div className="preview-content">
              <div className="preview-card">
                <h3>{t('branding.preview.cardTitle', 'Dashboard Card')}</h3>
                <p>{t('branding.preview.cardContent', 'This is sample content showing your brand colors and typography.')}</p>
                <button className="btn-primary">
                  {t('branding.preview.primaryButton', 'Primary Button')}
                </button>
                <button className="btn-secondary">
                  {t('branding.preview.secondaryButton', 'Secondary Button')}
                </button>
              </div>
              
              <div className="preview-stats">
                <div className="stat-item">
                  <div className="stat-value accent">142</div>
                  <div className="stat-label">{t('branding.preview.statLabel', 'Sample Metric')}</div>
                </div>
                <div className="stat-item">
                  <div className="stat-value accent">89%</div>
                  <div className="stat-label">{t('branding.preview.statLabel2', 'Another Metric')}</div>
                </div>
              </div>
            </div>

            {/* Custom CSS Preview */}
            {branding.custom_css && (
              <style dangerouslySetInnerHTML={{ __html: branding.custom_css }} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default OrganizationBranding;
