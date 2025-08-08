import React from 'react';
import { useTranslation } from 'react-i18next';
import './LanguageSwitcher.css';

const languages = [
  // North America
  { code: 'en-US', name: 'English (US)', flag: '🇺🇸' },
  
  // South America
  { code: 'pt-BR', name: 'Português (Brasil)', flag: '🇧🇷' },
  
  // Western Europe (Atlantic Coast)
  { code: 'pt-PT', name: 'Português (Portugal)', flag: '🇵🇹' },
  { code: 'es', name: 'Español', flag: '🇪🇸' },
  { code: 'fr', name: 'Français', flag: '🇫🇷' },
  
  // British Isles
  { code: 'en-GB', name: 'English (UK)', flag: '🇬🇧' },
  { code: 'ga', name: 'Gaeilge', flag: '🇮🇪' },
  
  // Low Countries & Central Europe
  { code: 'nl', name: 'Nederlands', flag: '🇳🇱' },
  { code: 'de', name: 'Deutsch', flag: '🇩🇪' },
  
  // Alpine Region
  { code: 'it', name: 'Italiano', flag: '🇮🇹' },
  
  // Nordic Countries
  { code: 'da', name: 'Dansk', flag: '🇩🇰' },
  { code: 'sv', name: 'Svenska', flag: '🇸🇪' },
  { code: 'fi', name: 'Suomi', flag: '🇫🇮' },
  
  // Baltic States (North to South)
  { code: 'et', name: 'Eesti keel', flag: '🇪🇪' },
  { code: 'lv', name: 'Latviešu valoda', flag: '🇱🇻' },
  { code: 'lt', name: 'Lietuvių kalba', flag: '🇱🇹' },
  
  // Central Europe (West to East)
  { code: 'cs', name: 'Čeština', flag: '🇨🇿' },
  { code: 'sk', name: 'Slovenčina', flag: '🇸🇰' },
  { code: 'pl', name: 'Polski', flag: '🇵🇱' },
  { code: 'hu', name: 'Magyar', flag: '🇭🇺' },
  
  // Southeast Europe (West to East)
  { code: 'sl', name: 'Slovenščina', flag: '🇸🇮' },
  { code: 'hr', name: 'Hrvatski', flag: '🇭🇷' },
  { code: 'ro', name: 'Română', flag: '🇷🇴' },
  { code: 'bg', name: 'Български', flag: '🇧🇬' },
  
  // Mediterranean
  { code: 'el', name: 'Ελληνικά', flag: '🇬🇷' },
  { code: 'mt', name: 'Malti', flag: '🇲🇹' }
];

function LanguageSwitcher() {
  const { i18n } = useTranslation();

  const handleLanguageChange = (languageCode) => {
    console.log('Language switcher: changing to', languageCode);
    i18n.changeLanguage(languageCode);
  };

  // Ensure we have a valid current language, fallback to en-US if not
  const currentLanguage = languages.find(lang => lang.code === i18n.language) 
    ? i18n.language 
    : 'en-US';

  return (
    <div className="language-switcher">
      <select 
        value={currentLanguage} 
        onChange={(e) => handleLanguageChange(e.target.value)}
        className="language-select"
      >
        {languages.map((lang) => (
          <option key={lang.code} value={lang.code}>
            {lang.flag} {lang.name}
          </option>
        ))}
      </select>
    </div>
  );
}

export default LanguageSwitcher;
