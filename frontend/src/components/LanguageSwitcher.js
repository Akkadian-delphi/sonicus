import React from 'react';
import { useTranslation } from 'react-i18next';
import './LanguageSwitcher.css';

const languages = [
  // English variants
  { code: 'en-US', name: 'English (US)', flag: '🇺🇸' },
  { code: 'en-GB', name: 'English (UK)', flag: '🇬🇧' },
  
  // Romance languages
  { code: 'es', name: 'Español', flag: '🇪🇸' },
  { code: 'fr', name: 'Français', flag: '🇫🇷' },
  { code: 'it', name: 'Italiano', flag: '��' },
  { code: 'pt-BR', name: 'Português (Brasil)', flag: '🇧🇷' },
  { code: 'pt-PT', name: 'Português (Portugal)', flag: '🇵🇹' },
  { code: 'ro', name: 'Română', flag: '🇷🇴' },
  
  // Germanic languages
  { code: 'de', name: 'Deutsch', flag: '🇩🇪' },
  { code: 'nl', name: 'Nederlands', flag: '🇳🇱' },
  { code: 'sv', name: 'Svenska', flag: '🇸🇪' },
  { code: 'da', name: 'Dansk', flag: '🇩🇰' },
  
  // Slavic languages
  { code: 'pl', name: 'Polski', flag: '🇵🇱' },
  { code: 'cs', name: 'Čeština', flag: '🇨🇿' },
  
  // Finno-Ugric languages
  { code: 'fi', name: 'Suomi', flag: '🇫🇮' },
  { code: 'hu', name: 'Magyar', flag: '🇭🇺' },
  
  // Hellenic languages
  { code: 'el', name: 'Ελληνικά', flag: '🇬🇷' }
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
