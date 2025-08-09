import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useTenant } from '../context/TenantContext';
import './CustomThemeBuilder.css';

const CustomThemeBuilder = () => {
  const { tenantInfo, isDarkMode, setIsDarkMode } = useTenant();
  const [activeTab, setActiveTab] = useState('themes');
  
  // Theme management state
  const [themes, setThemes] = useState([]);
  const [loading, setLoading] = useState(false);
  
  // Theme creation state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newTheme, setNewTheme] = useState({
    name: '',
    description: '',
    colors: {
      mode: 'light',
      primary: '#3b82f6',
      secondary: '#64748b',
      accent: '#8b5cf6',
      success: '#10b981',
      warning: '#f59e0b',
      error: '#ef4444',
      background: '#ffffff',
      surface: '#f8fafc',
      text: '#1e293b',
      text_secondary: '#64748b'
    },
    typography: {
      primary_font: 'Inter',
      secondary_font: 'system-ui',
      font_scale: 1.0,
      line_height: 1.5
    },
    layout: {
      border_radius: '8px',
      spacing_scale: 1.0,
      container_max_width: '1200px'
    }
  });
  
  // Industry theme generation
  const [showIndustryModal, setShowIndustryModal] = useState(false);
  const [industryTheme, setIndustryTheme] = useState({
    industry: 'corporate',
    base_colors: ['#3b82f6'],
    name: ''
  });
  
  // Templates state
  const [templates, setTemplates] = useState([]);
  
  // Schedules state
  const [schedules, setSchedules] = useState([]);
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [newSchedule, setNewSchedule] = useState({
    theme_id: '',
    name: '',
    start_time: '09:00',
    end_time: '17:00',
    days_of_week: [0, 1, 2, 3, 4], // Monday to Friday
    priority: 0
  });
  
  // Color intelligence state
  const [colorAnalysis, setColorAnalysis] = useState(null);
  const [colorsToAnalyze, setColorsToAnalyze] = useState(['#3b82f6']);

  useEffect(() => {
    if (tenantInfo?.organization_id) {
      loadThemes();
      loadTemplates();
      loadSchedules();
    }
  }, [tenantInfo?.organization_id]); // Added missing dependency

  const loadThemes = async () => {
    try {
      const response = await axios.get('/api/themes/', {
        headers: { 'X-Tenant': tenantInfo.domain }
      });
      setThemes(response.data);
      
      // No need to set activeTheme here since we removed it
    } catch (error) {
      console.error('Error loading themes:', error);
    }
  };

  const loadTemplates = async () => {
    try {
      const response = await axios.get('/api/themes/templates');
      setTemplates(response.data);
    } catch (error) {
      console.error('Error loading templates:', error);
    }
  };

  const loadSchedules = async () => {
    try {
      const response = await axios.get('/api/themes/schedules', {
        headers: { 'X-Tenant': tenantInfo.domain }
      });
      setSchedules(response.data);
    } catch (error) {
      console.error('Error loading schedules:', error);
    }
  };

  const createCustomTheme = async () => {
    setLoading(true);
    try {
      const response = await axios.post('/api/themes/', newTheme, {
        headers: { 'X-Tenant': tenantInfo.domain }
      });
      
      setThemes([response.data, ...themes]);
      setShowCreateModal(false);
      resetNewTheme();
      
      // Auto-activate if it's the first theme
      if (themes.length === 0) {
        await activateTheme(response.data.id);
      }
    } catch (error) {
      console.error('Error creating theme:', error);
      alert('Failed to create theme: ' + (error.response?.data?.detail || error.message));
    }
    setLoading(false);
  };

  const generateIndustryTheme = async () => {
    setLoading(true);
    try {
      const response = await axios.post('/api/themes/generate/industry', industryTheme, {
        headers: { 'X-Tenant': tenantInfo.domain }
      });
      
      setThemes([response.data, ...themes]);
      setShowIndustryModal(false);
      resetIndustryTheme();
    } catch (error) {
      console.error('Error generating theme:', error);
      alert('Failed to generate theme: ' + (error.response?.data?.detail || error.message));
    }
    setLoading(false);
  };

  const generateAccessibilityVariant = async (themeId) => {
    setLoading(true);
    try {
      const response = await axios.post(`/api/themes/${themeId}/accessibility`, {}, {
        headers: { 'X-Tenant': tenantInfo.domain }
      });
      
      setThemes([response.data, ...themes]);
    } catch (error) {
      console.error('Error generating accessibility variant:', error);
      alert('Failed to generate accessibility variant: ' + (error.response?.data?.detail || error.message));
    }
    setLoading(false);
  };

  const activateTheme = async (themeId) => {
    setLoading(true);
    try {
      await axios.put(`/api/themes/${themeId}/activate`, {}, {
        headers: { 'X-Tenant': tenantInfo.domain }
      });
      
      // Update active theme in state - find the newly activated theme
      const newActiveTheme = themes.find(theme => theme.id === themeId);
      
      // Update themes list to reflect active status
      setThemes(themes.map(theme => ({
        ...theme,
        is_active: theme.id === themeId
      })));
      
      // Apply theme to current page
      if (newActiveTheme) {
        applyThemeToPage(newActiveTheme);
      }
    } catch (error) {
      console.error('Error activating theme:', error);
      alert('Failed to activate theme: ' + (error.response?.data?.detail || error.message));
    }
    setLoading(false);
  };

  const deleteTheme = async (themeId) => {
    if (!window.confirm('Are you sure you want to delete this theme?')) return;
    
    setLoading(true);
    try {
      await axios.delete(`/api/themes/${themeId}`, {
        headers: { 'X-Tenant': tenantInfo.domain }
      });
      
      setThemes(themes.filter(theme => theme.id !== themeId));
    } catch (error) {
      console.error('Error deleting theme:', error);
      alert('Failed to delete theme: ' + (error.response?.data?.detail || error.message));
    }
    setLoading(false);
  };

  const applyTemplate = async (templateId, customName = null) => {
    setLoading(true);
    try {
      const response = await axios.post(`/api/themes/templates/${templateId}/apply`, 
        { custom_name: customName }, 
        { headers: { 'X-Tenant': tenantInfo.domain } }
      );
      
      setThemes([response.data, ...themes]);
    } catch (error) {
      console.error('Error applying template:', error);
      alert('Failed to apply template: ' + (error.response?.data?.detail || error.message));
    }
    setLoading(false);
  };

  const analyzeColors = async () => {
    setLoading(true);
    try {
      const response = await axios.post('/api/themes/colors/analyze', 
        { colors: colorsToAnalyze }, 
        { headers: { 'X-Tenant': tenantInfo.domain } }
      );
      
      setColorAnalysis(response.data);
    } catch (error) {
      console.error('Error analyzing colors:', error);
      alert('Failed to analyze colors: ' + (error.response?.data?.detail || error.message));
    }
    setLoading(false);
  };

  const createSchedule = async () => {
    setLoading(true);
    try {
      const response = await axios.post('/api/themes/schedules', newSchedule, {
        headers: { 'X-Tenant': tenantInfo.domain }
      });
      
      setSchedules([response.data, ...schedules]);
      setShowScheduleModal(false);
      resetNewSchedule();
    } catch (error) {
      console.error('Error creating schedule:', error);
      alert('Failed to create schedule: ' + (error.response?.data?.detail || error.message));
    }
    setLoading(false);
  };

  const applyThemeToPage = (theme) => {
    const root = document.documentElement;
    const colors = theme.colors;
    
    // Determine which color set to use
    const colorSet = isDarkMode && colors.dark_variant ? colors.dark_variant : colors;
    
    // Apply color variables
    Object.entries(colorSet).forEach(([key, value]) => {
      if (key !== 'mode' && value) {
        root.style.setProperty(`--color-${key.replace('_', '-')}`, value);
      }
    });
    
    // Apply typography
    if (theme.typography) {
      Object.entries(theme.typography).forEach(([key, value]) => {
        if (value) {
          root.style.setProperty(`--typography-${key.replace('_', '-')}`, value);
        }
      });
    }
    
    // Apply layout
    if (theme.layout) {
      Object.entries(theme.layout).forEach(([key, value]) => {
        if (value) {
          root.style.setProperty(`--layout-${key.replace('_', '-')}`, value);
        }
      });
    }
  };

  const resetNewTheme = () => {
    setNewTheme({
      name: '',
      description: '',
      colors: {
        mode: 'light',
        primary: '#3b82f6',
        secondary: '#64748b',
        accent: '#8b5cf6',
        success: '#10b981',
        warning: '#f59e0b',
        error: '#ef4444',
        background: '#ffffff',
        surface: '#f8fafc',
        text: '#1e293b',
        text_secondary: '#64748b'
      },
      typography: {
        primary_font: 'Inter',
        secondary_font: 'system-ui',
        font_scale: 1.0,
        line_height: 1.5
      },
      layout: {
        border_radius: '8px',
        spacing_scale: 1.0,
        container_max_width: '1200px'
      }
    });
  };

  const resetIndustryTheme = () => {
    setIndustryTheme({
      industry: 'corporate',
      base_colors: ['#3b82f6'],
      name: ''
    });
  };

  const resetNewSchedule = () => {
    setNewSchedule({
      theme_id: '',
      name: '',
      start_time: '09:00',
      end_time: '17:00',
      days_of_week: [0, 1, 2, 3, 4],
      priority: 0
    });
  };

  const handleColorChange = (colorKey, value) => {
    setNewTheme({
      ...newTheme,
      colors: {
        ...newTheme.colors,
        [colorKey]: value
      }
    });
  };

  const handleTypographyChange = (key, value) => {
    setNewTheme({
      ...newTheme,
      typography: {
        ...newTheme.typography,
        [key]: value
      }
    });
  };

  const renderThemesTab = () => (
    <div className="themes-section">
      <div className="section-header">
        <h3>Custom Themes</h3>
        <div className="header-actions">
          <button 
            className="btn-primary" 
            onClick={() => setShowCreateModal(true)}
            disabled={loading}
          >
            Create Custom Theme
          </button>
          <button 
            className="btn-secondary" 
            onClick={() => setShowIndustryModal(true)}
            disabled={loading}
          >
            Generate Industry Theme
          </button>
        </div>
      </div>
      
      <div className="themes-grid">
        {themes.map(theme => (
          <div 
            key={theme.id} 
            className={`theme-card ${theme.is_active ? 'active' : ''}`}
          >
            <div className="theme-preview">
              <div className="color-preview">
                <div 
                  className="color-swatch primary" 
                  style={{ backgroundColor: theme.colors.primary }}
                />
                <div 
                  className="color-swatch secondary" 
                  style={{ backgroundColor: theme.colors.secondary }}
                />
                <div 
                  className="color-swatch accent" 
                  style={{ backgroundColor: theme.colors.accent }}
                />
              </div>
            </div>
            
            <div className="theme-info">
              <h4>{theme.name}</h4>
              {theme.description && <p>{theme.description}</p>}
              <div className="theme-meta">
                <span className="theme-type">{theme.theme_type}</span>
                {theme.category && <span className="theme-category">{theme.category}</span>}
                {theme.high_contrast && <span className="accessibility-badge">High Contrast</span>}
              </div>
            </div>
            
            <div className="theme-actions">
              <button 
                className={`btn-activate ${theme.is_active ? 'active' : ''}`}
                onClick={() => activateTheme(theme.id)}
                disabled={loading || theme.is_active}
              >
                {theme.is_active ? 'Active' : 'Activate'}
              </button>
              
              <div className="theme-menu">
                <button 
                  className="btn-menu"
                  onClick={() => generateAccessibilityVariant(theme.id)}
                  disabled={loading}
                  title="Generate High Contrast Version"
                >
                  ♿
                </button>
                
                {!theme.is_active && (
                  <button 
                    className="btn-delete"
                    onClick={() => deleteTheme(theme.id)}
                    disabled={loading}
                    title="Delete Theme"
                  >
                    🗑️
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderTemplatesTab = () => (
    <div className="templates-section">
      <div className="section-header">
        <h3>Theme Templates</h3>
        <p className="section-description">
          Professional themes designed for specific industries and use cases
        </p>
      </div>
      
      <div className="templates-grid">
        {templates.map(template => (
          <div key={template.id} className="template-card">
            <div className="template-preview">
              <div className="color-preview">
                <div 
                  className="color-swatch primary" 
                  style={{ backgroundColor: template.colors.primary }}
                />
                <div 
                  className="color-swatch secondary" 
                  style={{ backgroundColor: template.colors.secondary }}
                />
                <div 
                  className="color-swatch accent" 
                  style={{ backgroundColor: template.colors.accent }}
                />
              </div>
            </div>
            
            <div className="template-info">
              <h4>{template.name}</h4>
              <p>{template.description}</p>
              <div className="template-meta">
                <span className="template-category">{template.category}</span>
                {template.industry && <span className="template-industry">{template.industry}</span>}
                {template.is_premium && <span className="premium-badge">Premium</span>}
              </div>
              
              <div className="template-features">
                {template.has_dark_variant && <span className="feature-badge">Dark Mode</span>}
                {template.has_high_contrast_variant && <span className="feature-badge">High Contrast</span>}
                {template.accessibility_score && (
                  <span className="accessibility-score">A11y: {template.accessibility_score}/100</span>
                )}
              </div>
            </div>
            
            <div className="template-actions">
              <button 
                className="btn-primary"
                onClick={() => applyTemplate(template.id)}
                disabled={loading}
              >
                Use Template
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderSchedulesTab = () => (
    <div className="schedules-section">
      <div className="section-header">
        <h3>Theme Scheduling</h3>
        <button 
          className="btn-primary" 
          onClick={() => setShowScheduleModal(true)}
          disabled={loading}
        >
          Create Schedule
        </button>
      </div>
      
      <div className="schedules-list">
        {schedules.map(schedule => (
          <div key={schedule.id} className="schedule-card">
            <div className="schedule-info">
              <h4>{schedule.name}</h4>
              <p>
                {schedule.start_time} - {schedule.end_time} 
                {schedule.days_of_week.length === 7 ? 
                  ' (Every day)' : 
                  ` (${schedule.days_of_week.length} days/week)`
                }
              </p>
              <span className={`schedule-status ${schedule.is_active ? 'active' : 'inactive'}`}>
                {schedule.is_active ? 'Active' : 'Inactive'}
              </span>
            </div>
            
            <div className="schedule-priority">
              Priority: {schedule.priority}
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderColorIntelligenceTab = () => (
    <div className="color-intelligence-section">
      <div className="section-header">
        <h3>Color Intelligence</h3>
        <p className="section-description">
          AI-powered color analysis and palette generation
        </p>
      </div>
      
      <div className="color-analyzer">
        <div className="color-input-section">
          <label>Colors to Analyze:</label>
          <div className="color-inputs">
            {colorsToAnalyze.map((color, index) => (
              <div key={index} className="color-input-group">
                <input
                  type="color"
                  value={color}
                  onChange={(e) => {
                    const newColors = [...colorsToAnalyze];
                    newColors[index] = e.target.value;
                    setColorsToAnalyze(newColors);
                  }}
                />
                <input
                  type="text"
                  value={color}
                  onChange={(e) => {
                    const newColors = [...colorsToAnalyze];
                    newColors[index] = e.target.value;
                    setColorsToAnalyze(newColors);
                  }}
                  placeholder="#3b82f6"
                />
              </div>
            ))}
            <button 
              className="btn-secondary"
              onClick={() => setColorsToAnalyze([...colorsToAnalyze, '#3b82f6'])}
            >
              Add Color
            </button>
          </div>
          
          <button 
            className="btn-primary"
            onClick={analyzeColors}
            disabled={loading || colorsToAnalyze.length === 0}
          >
            Analyze Colors
          </button>
        </div>
        
        {colorAnalysis && (
          <div className="color-analysis-results">
            <h4>Color Analysis Results</h4>
            
            <div className="palette-section">
              <h5>Complementary Palette</h5>
              <div className="color-palette">
                {colorAnalysis.complementary_palette.map((color, index) => (
                  <div key={index} className="color-result">
                    <div 
                      className="color-swatch" 
                      style={{ backgroundColor: color }}
                    />
                    <span>{color}</span>
                  </div>
                ))}
              </div>
            </div>
            
            <div className="palette-section">
              <h5>Dark Variants</h5>
              <div className="color-palette">
                {colorAnalysis.dark_variants.map((color, index) => (
                  <div key={index} className="color-result">
                    <div 
                      className="color-swatch" 
                      style={{ backgroundColor: color }}
                    />
                    <span>{color}</span>
                  </div>
                ))}
              </div>
            </div>
            
            <div className="palette-section">
              <h5>Accessibility Colors</h5>
              <div className="color-palette">
                {Object.entries(colorAnalysis.accessibility_colors).map(([key, color]) => (
                  <div key={key} className="color-result">
                    <div 
                      className="color-swatch" 
                      style={{ backgroundColor: color }}
                    />
                    <span>{key}: {color}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className={`custom-theme-builder ${isDarkMode ? 'dark' : 'light'}`}>
      <div className="theme-builder-header">
        <h2>Advanced Theme Management</h2>
        <div className="theme-mode-toggle">
          <label className="toggle-switch">
            <input
              type="checkbox"
              checked={isDarkMode}
              onChange={(e) => setIsDarkMode(e.target.checked)}
            />
            <span className="toggle-slider"></span>
          </label>
          <span>Dark Mode</span>
        </div>
      </div>

      <div className="theme-tabs">
        <button 
          className={`tab-button ${activeTab === 'themes' ? 'active' : ''}`}
          onClick={() => setActiveTab('themes')}
        >
          Custom Themes
        </button>
        <button 
          className={`tab-button ${activeTab === 'templates' ? 'active' : ''}`}
          onClick={() => setActiveTab('templates')}
        >
          Templates
        </button>
        <button 
          className={`tab-button ${activeTab === 'schedules' ? 'active' : ''}`}
          onClick={() => setActiveTab('schedules')}
        >
          Scheduling
        </button>
        <button 
          className={`tab-button ${activeTab === 'colors' ? 'active' : ''}`}
          onClick={() => setActiveTab('colors')}
        >
          Color Intelligence
        </button>
      </div>

      <div className="tab-content">
        {activeTab === 'themes' && renderThemesTab()}
        {activeTab === 'templates' && renderTemplatesTab()}
        {activeTab === 'schedules' && renderSchedulesTab()}
        {activeTab === 'colors' && renderColorIntelligenceTab()}
      </div>

      {/* Create Theme Modal */}
      {showCreateModal && (
        <div className="modal-overlay">
          <div className="modal-content large">
            <div className="modal-header">
              <h3>Create Custom Theme</h3>
              <button 
                className="modal-close"
                onClick={() => setShowCreateModal(false)}
              >
                ×
              </button>
            </div>
            
            <div className="modal-body">
              <div className="form-section">
                <label>Theme Name *</label>
                <input
                  type="text"
                  value={newTheme.name}
                  onChange={(e) => setNewTheme({...newTheme, name: e.target.value})}
                  placeholder="My Custom Theme"
                  required
                />
              </div>
              
              <div className="form-section">
                <label>Description</label>
                <textarea
                  value={newTheme.description}
                  onChange={(e) => setNewTheme({...newTheme, description: e.target.value})}
                  placeholder="Describe your theme..."
                  rows={3}
                />
              </div>
              
              <div className="form-section">
                <h4>Colors</h4>
                <div className="color-grid">
                  {Object.entries(newTheme.colors).map(([key, value]) => 
                    key !== 'mode' && (
                      <div key={key} className="color-input-group">
                        <label>{key.replace('_', ' ')}</label>
                        <div className="color-input-wrapper">
                          <input
                            type="color"
                            value={value}
                            onChange={(e) => handleColorChange(key, e.target.value)}
                          />
                          <input
                            type="text"
                            value={value}
                            onChange={(e) => handleColorChange(key, e.target.value)}
                            placeholder="#ffffff"
                          />
                        </div>
                      </div>
                    )
                  )}
                </div>
              </div>
              
              <div className="form-section">
                <h4>Typography</h4>
                <div className="form-row">
                  <div className="form-group">
                    <label>Primary Font</label>
                    <select
                      value={newTheme.typography.primary_font}
                      onChange={(e) => handleTypographyChange('primary_font', e.target.value)}
                    >
                      <option value="Inter">Inter</option>
                      <option value="Poppins">Poppins</option>
                      <option value="Roboto">Roboto</option>
                      <option value="system-ui">System UI</option>
                    </select>
                  </div>
                  
                  <div className="form-group">
                    <label>Font Scale</label>
                    <input
                      type="number"
                      value={newTheme.typography.font_scale}
                      onChange={(e) => handleTypographyChange('font_scale', parseFloat(e.target.value))}
                      min="0.8"
                      max="1.5"
                      step="0.1"
                    />
                  </div>
                </div>
              </div>
            </div>
            
            <div className="modal-footer">
              <button 
                className="btn-secondary"
                onClick={() => setShowCreateModal(false)}
                disabled={loading}
              >
                Cancel
              </button>
              <button 
                className="btn-primary"
                onClick={createCustomTheme}
                disabled={loading || !newTheme.name}
              >
                {loading ? 'Creating...' : 'Create Theme'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Industry Theme Modal */}
      {showIndustryModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3>Generate Industry Theme</h3>
              <button 
                className="modal-close"
                onClick={() => setShowIndustryModal(false)}
              >
                ×
              </button>
            </div>
            
            <div className="modal-body">
              <div className="form-section">
                <label>Industry</label>
                <select
                  value={industryTheme.industry}
                  onChange={(e) => setIndustryTheme({...industryTheme, industry: e.target.value})}
                >
                  <option value="corporate">Corporate</option>
                  <option value="healthcare">Healthcare</option>
                  <option value="education">Education</option>
                  <option value="technology">Technology</option>
                  <option value="creative">Creative</option>
                  <option value="finance">Finance</option>
                </select>
              </div>
              
              <div className="form-section">
                <label>Base Colors</label>
                {industryTheme.base_colors.map((color, index) => (
                  <div key={index} className="color-input-wrapper">
                    <input
                      type="color"
                      value={color}
                      onChange={(e) => {
                        const newColors = [...industryTheme.base_colors];
                        newColors[index] = e.target.value;
                        setIndustryTheme({...industryTheme, base_colors: newColors});
                      }}
                    />
                    <input
                      type="text"
                      value={color}
                      onChange={(e) => {
                        const newColors = [...industryTheme.base_colors];
                        newColors[index] = e.target.value;
                        setIndustryTheme({...industryTheme, base_colors: newColors});
                      }}
                      placeholder="#3b82f6"
                    />
                  </div>
                ))}
              </div>
              
              <div className="form-section">
                <label>Custom Name (optional)</label>
                <input
                  type="text"
                  value={industryTheme.name}
                  onChange={(e) => setIndustryTheme({...industryTheme, name: e.target.value})}
                  placeholder="Leave empty for auto-generated name"
                />
              </div>
            </div>
            
            <div className="modal-footer">
              <button 
                className="btn-secondary"
                onClick={() => setShowIndustryModal(false)}
                disabled={loading}
              >
                Cancel
              </button>
              <button 
                className="btn-primary"
                onClick={generateIndustryTheme}
                disabled={loading}
              >
                {loading ? 'Generating...' : 'Generate Theme'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Schedule Modal */}
      {showScheduleModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3>Create Theme Schedule</h3>
              <button 
                className="modal-close"
                onClick={() => setShowScheduleModal(false)}
              >
                ×
              </button>
            </div>
            
            <div className="modal-body">
              <div className="form-section">
                <label>Schedule Name</label>
                <input
                  type="text"
                  value={newSchedule.name}
                  onChange={(e) => setNewSchedule({...newSchedule, name: e.target.value})}
                  placeholder="Work Hours"
                  required
                />
              </div>
              
              <div className="form-section">
                <label>Theme</label>
                <select
                  value={newSchedule.theme_id}
                  onChange={(e) => setNewSchedule({...newSchedule, theme_id: parseInt(e.target.value)})}
                  required
                >
                  <option value="">Select a theme</option>
                  {themes.map(theme => (
                    <option key={theme.id} value={theme.id}>{theme.name}</option>
                  ))}
                </select>
              </div>
              
              <div className="form-row">
                <div className="form-group">
                  <label>Start Time</label>
                  <input
                    type="time"
                    value={newSchedule.start_time}
                    onChange={(e) => setNewSchedule({...newSchedule, start_time: e.target.value})}
                  />
                </div>
                
                <div className="form-group">
                  <label>End Time</label>
                  <input
                    type="time"
                    value={newSchedule.end_time}
                    onChange={(e) => setNewSchedule({...newSchedule, end_time: e.target.value})}
                  />
                </div>
              </div>
              
              <div className="form-section">
                <label>Days of Week</label>
                <div className="days-selector">
                  {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day, index) => (
                    <label key={index} className="day-checkbox">
                      <input
                        type="checkbox"
                        checked={newSchedule.days_of_week.includes(index)}
                        onChange={(e) => {
                          const days = [...newSchedule.days_of_week];
                          if (e.target.checked) {
                            days.push(index);
                          } else {
                            days.splice(days.indexOf(index), 1);
                          }
                          setNewSchedule({...newSchedule, days_of_week: days});
                        }}
                      />
                      {day}
                    </label>
                  ))}
                </div>
              </div>
            </div>
            
            <div className="modal-footer">
              <button 
                className="btn-secondary"
                onClick={() => setShowScheduleModal(false)}
                disabled={loading}
              >
                Cancel
              </button>
              <button 
                className="btn-primary"
                onClick={createSchedule}
                disabled={loading || !newSchedule.name || !newSchedule.theme_id}
              >
                {loading ? 'Creating...' : 'Create Schedule'}
              </button>
            </div>
          </div>
        </div>
      )}
      
      {loading && (
        <div className="loading-overlay">
          <div className="loading-spinner">Creating theme...</div>
        </div>
      )}
    </div>
  );
};

export default CustomThemeBuilder;
