import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useTenant } from '../../../context/TenantContext';
import './CustomThemeBuilder.css';

const CustomThemeBuilder = () => {
  const { tenantInfo } = useTenant();
  
  // Theme Builder State
  const [themes, setThemes] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [schedules, setSchedules] = useState([]);
  const [activeTab, setActiveTab] = useState('builder');
  
  // Theme Creation State
  const [newTheme, setNewTheme] = useState({
    name: '',
    description: '',
    category: '',
    colors: {
      mode: 'light',
      primary: '#3b82f6',
      secondary: '#6366f1',
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
      line_height: 1.5,
      font_weight: '400'
    },
    layout: {
      border_radius: '8px',
      spacing_scale: 1.0,
      container_max_width: '1200px',
      border_width: '1px',
      focus_ring_width: '2px'
    }
  });
  
  // Schedule Creation State
  const [newSchedule, setNewSchedule] = useState({
    theme_id: '',
    name: '',
    start_time: '09:00',
    end_time: '17:00',
    days_of_week: [1, 2, 3, 4, 5], // Monday-Friday
    priority: 0
  });
  
  // Color Intelligence State
  const [colorAnalysis, setColorAnalysis] = useState(null);
  const [previewCss, setPreviewCss] = useState('');
  
  const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:18100';
  
  useEffect(() => {
    if (tenantInfo?.token) {
      fetchThemes();
      fetchTemplates();
      fetchSchedules();
    }
  }, [tenantInfo]);
  
  useEffect(() => {
    generatePreview();
  }, [newTheme]);
  
  // API Functions
  const fetchThemes = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/themes/`, {
        headers: { Authorization: `Bearer ${tenantInfo.token}` }
      });
      setThemes(response.data);
    } catch (error) {
      console.error('Error fetching themes:', error);
    }
  };
  
  const fetchTemplates = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/themes/templates`);
      setTemplates(response.data);
    } catch (error) {
      console.error('Error fetching templates:', error);
    }
  };
  
  const fetchSchedules = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/themes/schedules`, {
        headers: { Authorization: `Bearer ${tenantInfo.token}` }
      });
      setSchedules(response.data);
    } catch (error) {
      console.error('Error fetching schedules:', error);
    }
  };
  
  const createTheme = async () => {
    try {
      const response = await axios.post(`${API_BASE}/api/themes/`, newTheme, {
        headers: { Authorization: `Bearer ${tenantInfo.token}` }
      });
      setThemes([...themes, response.data]);
      resetThemeForm();
      alert('Theme created successfully!');
    } catch (error) {
      console.error('Error creating theme:', error);
      alert('Failed to create theme');
    }
  };
  
  const generateIndustryTheme = async (industry, baseColors) => {
    try {
      const response = await axios.post(`${API_BASE}/api/themes/generate/industry`, {
        industry,
        base_colors: baseColors,
        name: `${industry} Auto-Generated`
      }, {
        headers: { Authorization: `Bearer ${tenantInfo.token}` }
      });
      setThemes([...themes, response.data]);
      alert('Industry theme generated!');
    } catch (error) {
      console.error('Error generating industry theme:', error);
      alert('Failed to generate theme');
    }
  };
  
  const generateAccessibilityVariant = async (themeId) => {
    try {
      const response = await axios.post(`${API_BASE}/api/themes/${themeId}/accessibility`, {}, {
        headers: { Authorization: `Bearer ${tenantInfo.token}` }
      });
      setThemes([...themes, response.data]);
      alert('Accessibility variant created!');
    } catch (error) {
      console.error('Error generating accessibility variant:', error);
      alert('Failed to create accessibility variant');
    }
  };
  
  const activateTheme = async (themeId) => {
    try {
      await axios.put(`${API_BASE}/api/themes/${themeId}/activate`, {}, {
        headers: { Authorization: `Bearer ${tenantInfo.token}` }
      });
      fetchThemes(); // Refresh to update active status
      alert('Theme activated!');
    } catch (error) {
      console.error('Error activating theme:', error);
      alert('Failed to activate theme');
    }
  };
  
  const createSchedule = async () => {
    try {
      const response = await axios.post(`${API_BASE}/api/themes/schedules`, newSchedule, {
        headers: { Authorization: `Bearer ${tenantInfo.token}` }
      });
      setSchedules([...schedules, response.data]);
      resetScheduleForm();
      alert('Schedule created successfully!');
    } catch (error) {
      console.error('Error creating schedule:', error);
      alert('Failed to create schedule');
    }
  };
  
  const analyzeColors = async () => {
    try {
      const colors = [
        newTheme.colors.primary,
        newTheme.colors.secondary,
        newTheme.colors.accent
      ];
      
      const response = await axios.post(`${API_BASE}/api/themes/colors/analyze`, colors, {
        headers: { Authorization: `Bearer ${tenantInfo.token}` }
      });
      setColorAnalysis(response.data);
    } catch (error) {
      console.error('Error analyzing colors:', error);
    }
  };
  
  const generatePreview = async () => {
    try {
      const response = await axios.post(`${API_BASE}/api/themes/preview`, {
        colors: newTheme.colors,
        typography: newTheme.typography,
        layout: newTheme.layout
      });
      setPreviewCss(response.data.css_preview);
    } catch (error) {
      console.error('Error generating preview:', error);
    }
  };
  
  const applyTemplate = async (templateId, customName) => {
    try {
      const response = await axios.post(
        `${API_BASE}/api/themes/templates/${templateId}/apply`,
        {},
        {
          headers: { Authorization: `Bearer ${tenantInfo.token}` },
          params: { custom_name: customName }
        }
      );
      setThemes([...themes, response.data]);
      alert('Template applied successfully!');
    } catch (error) {
      console.error('Error applying template:', error);
      alert('Failed to apply template');
    }
  };
  
  // Helper Functions
  const resetThemeForm = () => {
    setNewTheme({
      name: '',
      description: '',
      category: '',
      colors: {
        mode: 'light',
        primary: '#3b82f6',
        secondary: '#6366f1',
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
        line_height: 1.5,
        font_weight: '400'
      },
      layout: {
        border_radius: '8px',
        spacing_scale: 1.0,
        container_max_width: '1200px',
        border_width: '1px',
        focus_ring_width: '2px'
      }
    });
  };
  
  const resetScheduleForm = () => {
    setNewSchedule({
      theme_id: '',
      name: '',
      start_time: '09:00',
      end_time: '17:00',
      days_of_week: [1, 2, 3, 4, 5],
      priority: 0
    });
  };
  
  const updateThemeColor = (colorKey, value) => {
    setNewTheme(prev => ({
      ...prev,
      colors: {
        ...prev.colors,
        [colorKey]: value
      }
    }));
  };
  
  const updateTypography = (key, value) => {
    setNewTheme(prev => ({
      ...prev,
      typography: {
        ...prev.typography,
        [key]: value
      }
    }));
  };
  
  const updateLayout = (key, value) => {
    setNewTheme(prev => ({
      ...prev,
      layout: {
        ...prev.layout,
        [key]: value
      }
    }));
  };
  
  const getDayName = (dayNum) => {
    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    return days[dayNum];
  };
  
  return (
    <div className="custom-theme-builder">
      <div className="theme-builder-header">
        <h1>🎨 Advanced Theme Builder</h1>
        <p>Create, customize, and schedule unlimited themes for your organization</p>
      </div>
      
      {/* Tab Navigation */}
      <div className="theme-builder-tabs">
        <button 
          className={activeTab === 'builder' ? 'active' : ''}
          onClick={() => setActiveTab('builder')}
        >
          🏗️ Theme Builder
        </button>
        <button 
          className={activeTab === 'templates' ? 'active' : ''}
          onClick={() => setActiveTab('templates')}
        >
          📋 Templates
        </button>
        <button 
          className={activeTab === 'scheduler' ? 'active' : ''}
          onClick={() => setActiveTab('scheduler')}
        >
          ⏰ Scheduler
        </button>
        <button 
          className={activeTab === 'manager' ? 'active' : ''}
          onClick={() => setActiveTab('manager')}
        >
          🗂️ Theme Manager
        </button>
      </div>
      
      {/* Theme Builder Tab */}
      {activeTab === 'builder' && (
        <div className="theme-builder-content">
          <div className="builder-layout">
            <div className="builder-controls">
              <div className="theme-info">
                <h3>Theme Information</h3>
                <input
                  type="text"
                  placeholder="Theme Name"
                  value={newTheme.name}
                  onChange={(e) => setNewTheme({...newTheme, name: e.target.value})}
                />
                <textarea
                  placeholder="Theme Description"
                  value={newTheme.description}
                  onChange={(e) => setNewTheme({...newTheme, description: e.target.value})}
                />
                <select
                  value={newTheme.category}
                  onChange={(e) => setNewTheme({...newTheme, category: e.target.value})}
                >
                  <option value="">Select Category</option>
                  <option value="corporate">Corporate</option>
                  <option value="healthcare">Healthcare</option>
                  <option value="creative">Creative</option>
                  <option value="technology">Technology</option>
                  <option value="finance">Finance</option>
                  <option value="education">Education</option>
                  <option value="wellness">Wellness</option>
                </select>
              </div>
              
              <div className="color-controls">
                <h3>🎨 Colors</h3>
                {Object.entries(newTheme.colors).map(([key, value]) => (
                  key !== 'mode' && (
                    <div key={key} className="color-input">
                      <label>{key.replace('_', ' ')}:</label>
                      <input
                        type="color"
                        value={value}
                        onChange={(e) => updateThemeColor(key, e.target.value)}
                      />
                      <span>{value}</span>
                    </div>
                  )
                ))}
                <button onClick={analyzeColors} className="analyze-colors-btn">
                  🔍 Analyze Colors
                </button>
              </div>
              
              <div className="typography-controls">
                <h3>📝 Typography</h3>
                <div className="typography-input">
                  <label>Primary Font:</label>
                  <select 
                    value={newTheme.typography.primary_font}
                    onChange={(e) => updateTypography('primary_font', e.target.value)}
                  >
                    <option value="Inter">Inter</option>
                    <option value="Poppins">Poppins</option>
                    <option value="Roboto">Roboto</option>
                    <option value="Open Sans">Open Sans</option>
                    <option value="Lato">Lato</option>
                  </select>
                </div>
                <div className="typography-input">
                  <label>Font Scale:</label>
                  <input
                    type="range"
                    min="0.8"
                    max="1.3"
                    step="0.05"
                    value={newTheme.typography.font_scale}
                    onChange={(e) => updateTypography('font_scale', parseFloat(e.target.value))}
                  />
                  <span>{newTheme.typography.font_scale}</span>
                </div>
                <div className="typography-input">
                  <label>Line Height:</label>
                  <input
                    type="range"
                    min="1.2"
                    max="2.0"
                    step="0.1"
                    value={newTheme.typography.line_height}
                    onChange={(e) => updateTypography('line_height', parseFloat(e.target.value))}
                  />
                  <span>{newTheme.typography.line_height}</span>
                </div>
              </div>
              
              <div className="layout-controls">
                <h3>📐 Layout</h3>
                <div className="layout-input">
                  <label>Border Radius:</label>
                  <select 
                    value={newTheme.layout.border_radius}
                    onChange={(e) => updateLayout('border_radius', e.target.value)}
                  >
                    <option value="0px">Sharp (0px)</option>
                    <option value="4px">Subtle (4px)</option>
                    <option value="8px">Moderate (8px)</option>
                    <option value="12px">Rounded (12px)</option>
                    <option value="16px">Very Rounded (16px)</option>
                  </select>
                </div>
                <div className="layout-input">
                  <label>Spacing Scale:</label>
                  <input
                    type="range"
                    min="0.8"
                    max="1.5"
                    step="0.1"
                    value={newTheme.layout.spacing_scale}
                    onChange={(e) => updateLayout('spacing_scale', parseFloat(e.target.value))}
                  />
                  <span>{newTheme.layout.spacing_scale}x</span>
                </div>
              </div>
              
              <div className="builder-actions">
                <button onClick={createTheme} className="create-theme-btn">
                  ✨ Create Theme
                </button>
                <button onClick={resetThemeForm} className="reset-btn">
                  🔄 Reset Form
                </button>
              </div>
            </div>
            
            <div className="theme-preview">
              <h3>🖼️ Live Preview</h3>
              <div className="preview-container" style={{
                backgroundColor: newTheme.colors.background,
                color: newTheme.colors.text,
                fontFamily: newTheme.typography.primary_font,
                fontSize: `${newTheme.typography.font_scale}rem`,
                lineHeight: newTheme.typography.line_height,
                padding: `${parseFloat(newTheme.layout.spacing_scale) * 20}px`,
                borderRadius: newTheme.layout.border_radius
              }}>
                <div className="preview-header" style={{
                  backgroundColor: newTheme.colors.primary,
                  color: '#ffffff',
                  padding: `${parseFloat(newTheme.layout.spacing_scale) * 15}px`,
                  borderRadius: newTheme.layout.border_radius,
                  marginBottom: `${parseFloat(newTheme.layout.spacing_scale) * 20}px`
                }}>
                  <h2>Sample Header</h2>
                </div>
                
                <div className="preview-content" style={{
                  backgroundColor: newTheme.colors.surface,
                  padding: `${parseFloat(newTheme.layout.spacing_scale) * 15}px`,
                  borderRadius: newTheme.layout.border_radius,
                  marginBottom: `${parseFloat(newTheme.layout.spacing_scale) * 15}px`
                }}>
                  <p>This is a preview of your theme. You can see how the colors, typography, and layout work together.</p>
                  <button style={{
                    backgroundColor: newTheme.colors.accent,
                    color: '#ffffff',
                    padding: `${parseFloat(newTheme.layout.spacing_scale) * 8}px ${parseFloat(newTheme.layout.spacing_scale) * 16}px`,
                    borderRadius: newTheme.layout.border_radius,
                    border: 'none',
                    margin: `${parseFloat(newTheme.layout.spacing_scale) * 10}px ${parseFloat(newTheme.layout.spacing_scale) * 5}px`
                  }}>
                    Sample Button
                  </button>
                  <button style={{
                    backgroundColor: newTheme.colors.success,
                    color: '#ffffff',
                    padding: `${parseFloat(newTheme.layout.spacing_scale) * 8}px ${parseFloat(newTheme.layout.spacing_scale) * 16}px`,
                    borderRadius: newTheme.layout.border_radius,
                    border: 'none',
                    margin: `${parseFloat(newTheme.layout.spacing_scale) * 10}px ${parseFloat(newTheme.layout.spacing_scale) * 5}px`
                  }}>
                    Success Action
                  </button>
                </div>
                
                <div className="preview-sidebar" style={{
                  backgroundColor: newTheme.colors.surface,
                  color: newTheme.colors.text_secondary,
                  padding: `${parseFloat(newTheme.layout.spacing_scale) * 15}px`,
                  borderRadius: newTheme.layout.border_radius
                }}>
                  <h4>Secondary Content</h4>
                  <p>This shows secondary text color and surface background.</p>
                </div>
              </div>
              
              {colorAnalysis && (
                <div className="color-analysis">
                  <h4>🔍 Color Analysis</h4>
                  <div className="analysis-results">
                    <div className="complementary-colors">
                      <h5>Complementary Palette:</h5>
                      <div className="color-swatches">
                        {colorAnalysis.complementary_palette.map((color, index) => (
                          <div 
                            key={index}
                            className="color-swatch"
                            style={{ backgroundColor: color }}
                            title={color}
                          />
                        ))}
                      </div>
                    </div>
                    <div className="dark-variants">
                      <h5>Dark Mode Variants:</h5>
                      <div className="color-swatches">
                        {colorAnalysis.dark_variants.map((color, index) => (
                          <div 
                            key={index}
                            className="color-swatch"
                            style={{ backgroundColor: color }}
                            title={color}
                          />
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
      
      {/* Templates Tab */}
      {activeTab === 'templates' && (
        <div className="templates-content">
          <h2>🏛️ Theme Templates</h2>
          <p>Choose from professionally designed themes for your industry</p>
          
          <div className="templates-grid">
            {templates.map(template => (
              <div key={template.id} className="template-card">
                <div className="template-preview" style={{
                  background: `linear-gradient(135deg, ${template.colors.primary}, ${template.colors.secondary})`
                }}>
                  <div className="template-colors">
                    <div className="color-dot" style={{ backgroundColor: template.colors.primary }} />
                    <div className="color-dot" style={{ backgroundColor: template.colors.secondary }} />
                    <div className="color-dot" style={{ backgroundColor: template.colors.accent }} />
                  </div>
                </div>
                
                <div className="template-info">
                  <h3>{template.name}</h3>
                  <p>{template.description}</p>
                  
                  <div className="template-meta">
                    <span className="category">{template.category}</span>
                    {template.industry && <span className="industry">{template.industry}</span>}
                    {template.accessibility_score && (
                      <span className="accessibility-score">
                        ♿ {template.accessibility_score}%
                      </span>
                    )}
                  </div>
                  
                  <div className="template-features">
                    {template.has_dark_variant && <span className="feature">🌙 Dark</span>}
                    {template.has_high_contrast_variant && <span className="feature">🔆 High Contrast</span>}
                    {template.is_premium && <span className="feature premium">⭐ Premium</span>}
                  </div>
                  
                  <button 
                    onClick={() => applyTemplate(template.id, `${template.name} Custom`)}
                    className="apply-template-btn"
                  >
                    Apply Template
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Theme Manager Tab */}
      {activeTab === 'manager' && (
        <div className="theme-manager-content">
          <h2>🗂️ Theme Manager</h2>
          <p>Manage all your custom and applied themes</p>
          
          <div className="themes-list">
            {themes.map(theme => (
              <div key={theme.id} className={`theme-item ${theme.is_active ? 'active' : ''}`}>
                <div className="theme-colors">
                  <div className="color-dot" style={{ backgroundColor: theme.colors.primary }} />
                  <div className="color-dot" style={{ backgroundColor: theme.colors.secondary }} />
                  <div className="color-dot" style={{ backgroundColor: theme.colors.accent }} />
                </div>
                
                <div className="theme-details">
                  <div className="theme-header">
                    <h3>{theme.name}</h3>
                    {theme.is_active && <span className="active-badge">Active</span>}
                  </div>
                  <p>{theme.description}</p>
                  <div className="theme-meta">
                    <span>Type: {theme.theme_type}</span>
                    {theme.category && <span>Category: {theme.category}</span>}
                    <span>Used: {theme.usage_count} times</span>
                  </div>
                  
                  <div className="theme-features">
                    {theme.high_contrast && <span className="feature">🔆 High Contrast</span>}
                    {theme.large_text && <span className="feature">🔍 Large Text</span>}
                    {theme.reduced_motion && <span className="feature">🎭 Reduced Motion</span>}
                  </div>
                </div>
                
                <div className="theme-actions">
                  {!theme.is_active && (
                    <button onClick={() => activateTheme(theme.id)} className="activate-btn">
                      ✨ Activate
                    </button>
                  )}
                  <button onClick={() => generateAccessibilityVariant(theme.id)} className="accessibility-btn">
                    ♿ Accessibility Variant
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Scheduler Tab */}
      {activeTab === 'scheduler' && (
        <div className="scheduler-content">
          <h2>⏰ Theme Scheduler</h2>
          <p>Automatically switch themes based on time of day</p>
          
          <div className="scheduler-layout">
            <div className="schedule-creator">
              <h3>Create Schedule</h3>
              <div className="schedule-form">
                <input
                  type="text"
                  placeholder="Schedule Name"
                  value={newSchedule.name}
                  onChange={(e) => setNewSchedule({...newSchedule, name: e.target.value})}
                />
                
                <select
                  value={newSchedule.theme_id}
                  onChange={(e) => setNewSchedule({...newSchedule, theme_id: parseInt(e.target.value)})}
                >
                  <option value="">Select Theme</option>
                  {themes.map(theme => (
                    <option key={theme.id} value={theme.id}>{theme.name}</option>
                  ))}
                </select>
                
                <div className="time-inputs">
                  <div>
                    <label>Start Time:</label>
                    <input
                      type="time"
                      value={newSchedule.start_time}
                      onChange={(e) => setNewSchedule({...newSchedule, start_time: e.target.value})}
                    />
                  </div>
                  <div>
                    <label>End Time:</label>
                    <input
                      type="time"
                      value={newSchedule.end_time}
                      onChange={(e) => setNewSchedule({...newSchedule, end_time: e.target.value})}
                    />
                  </div>
                </div>
                
                <div className="days-selector">
                  <label>Days of Week:</label>
                  <div className="days-checkboxes">
                    {[0, 1, 2, 3, 4, 5, 6].map(day => (
                      <label key={day} className="day-checkbox">
                        <input
                          type="checkbox"
                          checked={newSchedule.days_of_week.includes(day)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setNewSchedule({
                                ...newSchedule,
                                days_of_week: [...newSchedule.days_of_week, day]
                              });
                            } else {
                              setNewSchedule({
                                ...newSchedule,
                                days_of_week: newSchedule.days_of_week.filter(d => d !== day)
                              });
                            }
                          }}
                        />
                        {getDayName(day)}
                      </label>
                    ))}
                  </div>
                </div>
                
                <div className="priority-input">
                  <label>Priority:</label>
                  <input
                    type="number"
                    min="0"
                    max="10"
                    value={newSchedule.priority}
                    onChange={(e) => setNewSchedule({...newSchedule, priority: parseInt(e.target.value)})}
                  />
                  <small>Higher priority schedules override lower ones</small>
                </div>
                
                <button onClick={createSchedule} className="create-schedule-btn">
                  ⏰ Create Schedule
                </button>
              </div>
            </div>
            
            <div className="schedules-list">
              <h3>Active Schedules</h3>
              {schedules.map(schedule => (
                <div key={schedule.id} className="schedule-item">
                  <div className="schedule-header">
                    <h4>{schedule.name}</h4>
                    <span className="priority">Priority: {schedule.priority}</span>
                  </div>
                  
                  <div className="schedule-details">
                    <div className="time-range">
                      {schedule.start_time} - {schedule.end_time}
                    </div>
                    <div className="schedule-days">
                      {schedule.days_of_week.map(day => getDayName(day)).join(', ')}
                    </div>
                  </div>
                  
                  {schedule.is_active ? (
                    <span className="status active">✅ Active</span>
                  ) : (
                    <span className="status inactive">⏸️ Inactive</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CustomThemeBuilder;
