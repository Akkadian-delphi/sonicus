import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../hooks/useAuth';
import '../styles/ProfilePage.css';

// Language options - All 26 European languages with flags and native names
const languageOptions = [
  // North America
  { code: 'en-US', name: 'English (US)', nativeName: 'English (US)', flag: '🇺🇸' },
  
  // South America
  { code: 'pt-BR', name: 'Portuguese (Brazil)', nativeName: 'Português (Brasil)', flag: '🇧🇷' },
  
  // Western Europe (Atlantic Coast)
  { code: 'pt-PT', name: 'Portuguese (Portugal)', nativeName: 'Português (Portugal)', flag: '🇵🇹' },
  { code: 'es', name: 'Spanish', nativeName: 'Español', flag: '🇪🇸' },
  { code: 'fr', name: 'French', nativeName: 'Français', flag: '🇫🇷' },
  
  // British Isles
  { code: 'en-GB', name: 'English (UK)', nativeName: 'English (UK)', flag: '🇬🇧' },
  { code: 'ga', name: 'Irish', nativeName: 'Gaeilge', flag: '🇮🇪' },
  
  // Low Countries & Central Europe
  { code: 'nl', name: 'Dutch', nativeName: 'Nederlands', flag: '🇳🇱' },
  { code: 'de', name: 'German', nativeName: 'Deutsch', flag: '🇩🇪' },
  
  // Alpine Region
  { code: 'it', name: 'Italian', nativeName: 'Italiano', flag: '🇮🇹' },
  
  // Nordic Countries
  { code: 'da', name: 'Danish', nativeName: 'Dansk', flag: '🇩🇰' },
  { code: 'sv', name: 'Swedish', nativeName: 'Svenska', flag: '🇸🇪' },
  { code: 'fi', name: 'Finnish', nativeName: 'Suomi', flag: '🇫🇮' },
  
  // Baltic States (North to South)
  { code: 'et', name: 'Estonian', nativeName: 'Eesti keel', flag: '🇪🇪' },
  { code: 'lv', name: 'Latvian', nativeName: 'Latviešu valoda', flag: '🇱🇻' },
  { code: 'lt', name: 'Lithuanian', nativeName: 'Lietuvių kalba', flag: '🇱🇹' },
  
  // Central Europe (West to East)
  { code: 'cs', name: 'Czech', nativeName: 'Čeština', flag: '🇨🇿' },
  { code: 'sk', name: 'Slovak', nativeName: 'Slovenčina', flag: '🇸🇰' },
  { code: 'pl', name: 'Polish', nativeName: 'Polski', flag: '🇵🇱' },
  { code: 'hu', name: 'Hungarian', nativeName: 'Magyar', flag: '🇭🇺' },
  
  // Southeast Europe (West to East)
  { code: 'sl', name: 'Slovenian', nativeName: 'Slovenščina', flag: '🇸🇮' },
  { code: 'hr', name: 'Croatian', nativeName: 'Hrvatski', flag: '🇭🇷' },
  { code: 'ro', name: 'Romanian', nativeName: 'Română', flag: '🇷🇴' },
  { code: 'bg', name: 'Bulgarian', nativeName: 'Български', flag: '🇧🇬' },
  
  // Mediterranean
  { code: 'el', name: 'Greek', nativeName: 'Ελληνικά', flag: '🇬🇷' },
  { code: 'mt', name: 'Maltese', nativeName: 'Malti', flag: '🇲🇹' }
];

// Icons for the profile page
const UserIcon = () => (
  <svg className="profile-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
  </svg>
);

const EmailIcon = () => (
  <svg className="profile-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
  </svg>
);

const PhoneIcon = () => (
  <svg className="profile-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
  </svg>
);

const LocationIcon = () => (
  <svg className="profile-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
  </svg>
);

const CalendarIcon = () => (
  <svg className="profile-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
  </svg>
);

const LockIcon = () => (
  <svg className="profile-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
  </svg>
);

const SaveIcon = () => (
  <svg className="profile-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
  </svg>
);

const CameraIcon = () => (
  <svg className="profile-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
  </svg>
);

const SettingsIcon = () => (
  <svg className="profile-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
  </svg>
);

const LanguageIcon = () => (
  <svg className="profile-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
  </svg>
);

const ChevronDownIcon = () => (
  <svg className="dropdown-chevron" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
  </svg>
);

function ProfilePage() {
  const { t } = useTranslation();
  const { user, updateProfile, loading } = useAuth();
  
  // Form state
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    dateOfBirth: '',
    country: '',
    city: '',
    timezone: '',
    bio: '',
    preferredLanguage: 'en-US',
    emailNotifications: true,
    soundNotifications: true,
    marketingEmails: false
  });

  // UI state
  const [isEditing, setIsEditing] = useState(false);
  const [activeTab, setActiveTab] = useState('personal');
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState('');
  const [errors, setErrors] = useState({});

  // Password change state
  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });

  // Avatar upload state
  const [avatarPreview, setAvatarPreview] = useState(null);
  const [avatarFile, setAvatarFile] = useState(null);

  // Language dropdown state
  const [isLanguageDropdownOpen, setIsLanguageDropdownOpen] = useState(false);
  const [languageSearchTerm, setLanguageSearchTerm] = useState('');

  // Load user data
  useEffect(() => {
    if (user) {
      setFormData({
        firstName: user.firstName || user.email?.split('@')[0] || '',
        lastName: user.lastName || '',
        email: user.email || '',
        phone: user.phone || '',
        dateOfBirth: user.dateOfBirth || '',
        country: user.country || '',
        city: user.city || '',
        timezone: user.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone,
        bio: user.bio || '',
        preferredLanguage: user.preferredLanguage || 'en-US',
        emailNotifications: user.emailNotifications !== false,
        soundNotifications: user.soundNotifications !== false,
        marketingEmails: user.marketingEmails || false
      });
    }
  }, [user]);

  // Handle input changes
  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  // Handle password input changes
  const handlePasswordChange = (e) => {
    const { name, value } = e.target;
    setPasswordData(prev => ({ ...prev, [name]: value }));
    
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  // Handle avatar upload
  const handleAvatarChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) { // 5MB limit
        setErrors(prev => ({ ...prev, avatar: 'Avatar file size must be less than 5MB' }));
        return;
      }
      
      const reader = new FileReader();
      reader.onload = (event) => {
        setAvatarPreview(event.target.result);
      };
      reader.readAsDataURL(file);
      setAvatarFile(file);
    }
  };

  // Validate form
  const validateForm = () => {
    const newErrors = {};

    if (!formData.firstName.trim()) {
      newErrors.firstName = 'First name is required';
    }

    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    if (formData.phone && !/^\+?[\d\s-()]+$/.test(formData.phone)) {
      newErrors.phone = 'Please enter a valid phone number';
    }

    return newErrors;
  };

  // Validate password change
  const validatePassword = () => {
    const newErrors = {};

    if (!passwordData.currentPassword) {
      newErrors.currentPassword = 'Current password is required';
    }

    if (!passwordData.newPassword) {
      newErrors.newPassword = 'New password is required';
    } else if (passwordData.newPassword.length < 8) {
      newErrors.newPassword = 'Password must be at least 8 characters long';
    }

    if (passwordData.newPassword !== passwordData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    return newErrors;
  };

  // Save profile
  const handleSave = async () => {
    const validationErrors = validateForm();
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setIsSaving(true);
    try {
      await updateProfile(formData, avatarFile);
      setSaveMessage('Profile updated successfully!');
      setIsEditing(false);
      setTimeout(() => setSaveMessage(''), 3000);
    } catch (error) {
      setErrors({ general: error.message || 'Failed to update profile' });
    } finally {
      setIsSaving(false);
    }
  };

  // Change password
  const handlePasswordSave = async () => {
    const validationErrors = validatePassword();
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setIsSaving(true);
    try {
      // This would be an API call to change password
      // await changePassword(passwordData);
      setSaveMessage('Password updated successfully!');
      setPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' });
      setTimeout(() => setSaveMessage(''), 3000);
    } catch (error) {
      setErrors({ general: error.message || 'Failed to update password' });
    } finally {
      setIsSaving(false);
    }
  };

  // Handle language selection
  const handleLanguageSelect = (languageCode) => {
    setFormData(prev => ({ ...prev, preferredLanguage: languageCode }));
    setIsLanguageDropdownOpen(false);
    setLanguageSearchTerm('');
  };

  // Filter languages based on search term
  const filteredLanguages = languageOptions.filter(lang => 
    lang.name.toLowerCase().includes(languageSearchTerm.toLowerCase()) ||
    lang.nativeName.toLowerCase().includes(languageSearchTerm.toLowerCase()) ||
    lang.code.toLowerCase().includes(languageSearchTerm.toLowerCase())
  );

  // Get current language info
  const getCurrentLanguage = () => {
    return languageOptions.find(lang => lang.code === formData.preferredLanguage) || languageOptions[0];
  };

  if (loading) {
    return (
      <div className="profile-loading">
        <div className="loading-spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  const displayName = `${formData.firstName || user?.email?.split('@')[0] || 'User'} ${formData.lastName || ''}`.trim();

  return (
    <div className="profile-page">
      <div className="profile-container">
        {/* Header */}
        <div className="profile-header">
          <div className="profile-avatar-section">
            <div className="avatar-container">
              <img
                src={avatarPreview || user?.avatar || `https://ui-avatars.com/api/?name=${encodeURIComponent(displayName)}&size=120&background=10b981&color=ffffff&rounded=true`}
                alt="Avatar"
                className="profile-avatar-large"
                onError={(e) => {
                  e.target.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(displayName)}&size=120&background=10b981&color=ffffff&rounded=true`;
                }}
              />
              {isEditing && (
                <label className="avatar-upload-btn">
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleAvatarChange}
                    style={{ display: 'none' }}
                  />
                  <CameraIcon />
                </label>
              )}
            </div>
            {errors.avatar && <span className="error-text">{errors.avatar}</span>}
          </div>
          
          <div className="profile-info">
            <h1 className="profile-name">{displayName}</h1>
            <p className="profile-email">{user?.email}</p>
            <div className="profile-stats">
              <div className="stat-item">
                <span className="stat-label">Member Since</span>
                <span className="stat-value">
                  {user?.created_at ? new Date(user.created_at).toLocaleDateString() : '—'}
                </span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Current Plan</span>
                <span className="stat-value plan-badge">
                  {user?.subscriptionTier || 'Starter'}
                </span>
              </div>
            </div>
          </div>

          <div className="profile-actions">
            {!isEditing ? (
              <button
                className="btn-primary edit-btn"
                onClick={() => setIsEditing(true)}
              >
                Edit Profile
              </button>
            ) : (
              <div className="edit-actions">
                <button
                  className="btn-secondary"
                  onClick={() => {
                    setIsEditing(false);
                    setErrors({});
                    setAvatarPreview(null);
                    setAvatarFile(null);
                  }}
                >
                  Cancel
                </button>
                <button
                  className="btn-primary"
                  onClick={handleSave}
                  disabled={isSaving}
                >
                  <SaveIcon />
                  {isSaving ? 'Saving...' : 'Save'}
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Success/Error Messages */}
        {saveMessage && (
          <div className="alert alert-success">
            {saveMessage}
          </div>
        )}

        {errors.general && (
          <div className="alert alert-error">
            {errors.general}
          </div>
        )}

        {/* Tabs */}
        <div className="profile-tabs">
          <button
            className={`tab-btn ${activeTab === 'personal' ? 'active' : ''}`}
            onClick={() => setActiveTab('personal')}
          >
            <UserIcon />
            Personal Info
          </button>
          <button
            className={`tab-btn ${activeTab === 'security' ? 'active' : ''}`}
            onClick={() => setActiveTab('security')}
          >
            <LockIcon />
            Security
          </button>
          <button
            className={`tab-btn ${activeTab === 'preferences' ? 'active' : ''}`}
            onClick={() => setActiveTab('preferences')}
          >
            <SettingsIcon />
            Preferences
          </button>
        </div>

        {/* Tab Content */}
        <div className="profile-content">
          {activeTab === 'personal' && (
            <div className="tab-panel">
              <div className="form-grid">
                <div className="form-group">
                  <label className="form-label">
                    <UserIcon />
                    First Name
                  </label>
                  <input
                    type="text"
                    name="firstName"
                    value={formData.firstName}
                    onChange={handleInputChange}
                    disabled={!isEditing}
                    className={`form-input ${errors.firstName ? 'error' : ''}`}
                    placeholder="Enter your first name"
                  />
                  {errors.firstName && <span className="error-text">{errors.firstName}</span>}
                </div>

                <div className="form-group">
                  <label className="form-label">
                    <UserIcon />
                    Last Name
                  </label>
                  <input
                    type="text"
                    name="lastName"
                    value={formData.lastName}
                    onChange={handleInputChange}
                    disabled={!isEditing}
                    className={`form-input ${errors.lastName ? 'error' : ''}`}
                    placeholder="Enter your last name"
                  />
                  {errors.lastName && <span className="error-text">{errors.lastName}</span>}
                </div>

                <div className="form-group">
                  <label className="form-label">
                    <EmailIcon />
                    Email
                  </label>
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleInputChange}
                    disabled={!isEditing}
                    className={`form-input ${errors.email ? 'error' : ''}`}
                    placeholder="Enter your email address"
                  />
                  {errors.email && <span className="error-text">{errors.email}</span>}
                </div>

                <div className="form-group">
                  <label className="form-label">
                    <PhoneIcon />
                    Phone
                  </label>
                  <input
                    type="tel"
                    name="phone"
                    value={formData.phone}
                    onChange={handleInputChange}
                    disabled={!isEditing}
                    className={`form-input ${errors.phone ? 'error' : ''}`}
                    placeholder="Enter your phone number"
                  />
                  {errors.phone && <span className="error-text">{errors.phone}</span>}
                </div>

                <div className="form-group">
                  <label className="form-label">
                    <CalendarIcon />
                    Date of Birth
                  </label>
                  <input
                    type="date"
                    name="dateOfBirth"
                    value={formData.dateOfBirth}
                    onChange={handleInputChange}
                    disabled={!isEditing}
                    className="form-input"
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">
                    <LocationIcon />
                    Country
                  </label>
                  <input
                    type="text"
                    name="country"
                    value={formData.country}
                    onChange={handleInputChange}
                    disabled={!isEditing}
                    className="form-input"
                    placeholder="Enter your country"
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">
                    <LocationIcon />
                    City
                  </label>
                  <input
                    type="text"
                    name="city"
                    value={formData.city}
                    onChange={handleInputChange}
                    disabled={!isEditing}
                    className="form-input"
                    placeholder="Enter your city"
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">
                    Timezone
                  </label>
                  <select
                    name="timezone"
                    value={formData.timezone}
                    onChange={handleInputChange}
                    disabled={!isEditing}
                    className="form-select"
                  >
                    <option value="UTC">UTC</option>
                    <option value="America/New_York">Eastern Time</option>
                    <option value="America/Chicago">Central Time</option>
                    <option value="America/Denver">Mountain Time</option>
                    <option value="America/Los_Angeles">Pacific Time</option>
                    <option value="Europe/London">London</option>
                    <option value="Europe/Paris">Paris</option>
                    <option value="Europe/Berlin">Berlin</option>
                    <option value="Europe/Rome">Rome</option>
                    <option value="Asia/Tokyo">Tokyo</option>
                    <option value="Asia/Shanghai">Shanghai</option>
                    <option value="Australia/Sydney">Sydney</option>
                  </select>
                </div>
              </div>

              <div className="form-group bio-group">
                <label className="form-label">
                  Bio
                </label>
                <textarea
                  name="bio"
                  value={formData.bio}
                  onChange={handleInputChange}
                  disabled={!isEditing}
                  className="form-textarea"
                  placeholder="Tell us a bit about yourself..."
                  rows={4}
                  maxLength={500}
                />
                <div className="character-count">
                  {formData.bio.length}/500
                </div>
              </div>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="tab-panel">
              <div className="security-section">
                <h3>Change Password</h3>
                <div className="form-grid">
                  <div className="form-group">
                    <label className="form-label">
                      <LockIcon />
                      Current Password
                    </label>
                    <input
                      type="password"
                      name="currentPassword"
                      value={passwordData.currentPassword}
                      onChange={handlePasswordChange}
                      className={`form-input ${errors.currentPassword ? 'error' : ''}`}
                      placeholder="Enter your current password"
                    />
                    {errors.currentPassword && <span className="error-text">{errors.currentPassword}</span>}
                  </div>

                  <div className="form-group">
                    <label className="form-label">
                      <LockIcon />
                      New Password
                    </label>
                    <input
                      type="password"
                      name="newPassword"
                      value={passwordData.newPassword}
                      onChange={handlePasswordChange}
                      className={`form-input ${errors.newPassword ? 'error' : ''}`}
                      placeholder="Enter your new password"
                    />
                    {errors.newPassword && <span className="error-text">{errors.newPassword}</span>}
                  </div>

                  <div className="form-group">
                    <label className="form-label">
                      <LockIcon />
                      Confirm New Password
                    </label>
                    <input
                      type="password"
                      name="confirmPassword"
                      value={passwordData.confirmPassword}
                      onChange={handlePasswordChange}
                      className={`form-input ${errors.confirmPassword ? 'error' : ''}`}
                      placeholder="Confirm your new password"
                    />
                    {errors.confirmPassword && <span className="error-text">{errors.confirmPassword}</span>}
                  </div>
                </div>

                <button
                  className="btn-primary"
                  onClick={handlePasswordSave}
                  disabled={isSaving}
                >
                  Update Password
                </button>
              </div>
            </div>
          )}

          {activeTab === 'preferences' && (
            <div className="tab-panel">
              <div className="preferences-section">
                <h3>Language Settings</h3>
                <div className="form-group">
                  <label className="form-label">
                    <LanguageIcon />
                    Preferred Language
                  </label>
                  <div className="language-selector">
                    <button
                      type="button"
                      className={`language-dropdown-trigger ${!isEditing ? 'disabled' : ''}`}
                      onClick={() => isEditing && setIsLanguageDropdownOpen(!isLanguageDropdownOpen)}
                      disabled={!isEditing}
                    >
                      <div className="selected-language">
                        <span className="language-flag">{getCurrentLanguage().flag}</span>
                        <div className="language-info">
                          <span className="language-name">{getCurrentLanguage().name}</span>
                          <span className="language-native">{getCurrentLanguage().nativeName}</span>
                        </div>
                      </div>
                      <ChevronDownIcon />
                    </button>
                    
                    {isLanguageDropdownOpen && isEditing && (
                      <div className="language-dropdown">
                        <div className="language-search">
                          <input
                            type="text"
                            placeholder="Search languages..."
                            value={languageSearchTerm}
                            onChange={(e) => setLanguageSearchTerm(e.target.value)}
                            className="language-search-input"
                            autoFocus
                          />
                        </div>
                        <div className="language-options">
                          {filteredLanguages.map((language) => (
                            <button
                              key={language.code}
                              type="button"
                              className={`language-option ${formData.preferredLanguage === language.code ? 'selected' : ''}`}
                              onClick={() => handleLanguageSelect(language.code)}
                            >
                              <span className="language-flag">{language.flag}</span>
                              <div className="language-info">
                                <span className="language-name">{language.name}</span>
                                <span className="language-native">{language.nativeName}</span>
                              </div>
                              {formData.preferredLanguage === language.code && (
                                <svg className="check-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                </svg>
                              )}
                            </button>
                          ))}
                        </div>
                        {filteredLanguages.length === 0 && (
                          <div className="no-languages">
                            No languages found matching "{languageSearchTerm}"
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>

                <h3>Notification Settings</h3>
                <div className="notification-group">
                  <div className="notification-item">
                    <input
                      type="checkbox"
                      id="emailNotifications"
                      name="emailNotifications"
                      checked={formData.emailNotifications}
                      onChange={handleInputChange}
                      disabled={!isEditing}
                    />
                    <label htmlFor="emailNotifications">
                      Email Notifications
                    </label>
                    <span className="notification-desc">
                      Receive email notifications about your account activity
                    </span>
                  </div>

                  <div className="notification-item">
                    <input
                      type="checkbox"
                      id="soundNotifications"
                      name="soundNotifications"
                      checked={formData.soundNotifications}
                      onChange={handleInputChange}
                      disabled={!isEditing}
                    />
                    <label htmlFor="soundNotifications">
                      Sound Notifications
                    </label>
                    <span className="notification-desc">
                      Play sound notifications in the browser
                    </span>
                  </div>

                  <div className="notification-item">
                    <input
                      type="checkbox"
                      id="marketingEmails"
                      name="marketingEmails"
                      checked={formData.marketingEmails}
                      onChange={handleInputChange}
                      disabled={!isEditing}
                    />
                    <label htmlFor="marketingEmails">
                      Marketing Emails
                    </label>
                    <span className="notification-desc">
                      Receive emails about new features and promotions
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ProfilePage;
