import React from 'react';
import { useTranslation } from 'react-i18next';

function LanguageDebugInfo() {
  const { i18n } = useTranslation();

  // Only show in development mode
  if (process.env.NODE_ENV !== 'development') {
    return null;
  }

  const browserLang = navigator.language || 'Unknown';
  const browserLangs = navigator.languages ? navigator.languages.join(', ') : 'Unknown';
  const currentLang = i18n.language;
  const storedLang = localStorage.getItem('i18nextLng') || 'None';

  return (
    <div style={{
      position: 'fixed',
      bottom: '10px',
      left: '10px',
      background: 'rgba(0, 0, 0, 0.8)',
      color: 'white',
      padding: '10px',
      borderRadius: '5px',
      fontSize: '12px',
      fontFamily: 'monospace',
      zIndex: 1000,
      maxWidth: '300px'
    }}>
      <div><strong>🌍 Language Debug Info</strong></div>
      <div>Current: <strong>{currentLang}</strong></div>
      <div>Browser: {browserLang}</div>
      <div>All Browser: {browserLangs}</div>
      <div>Stored: {storedLang}</div>
      <div>URL Param: {new URLSearchParams(window.location.search).get('lng') || 'None'}</div>
    </div>
  );
}

export default LanguageDebugInfo;
