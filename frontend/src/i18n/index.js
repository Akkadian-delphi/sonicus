import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

// Translation resources - All 24 EU Official Languages
import enUSTranslations from './locales/en-US.json';
import enGBTranslations from './locales/en-GB.json';
import esTranslations from './locales/es.json';
import frTranslations from './locales/fr.json';
import deTranslations from './locales/de.json';
import ptBRTranslations from './locales/pt-BR.json';
import ptPTTranslations from './locales/pt-PT.json';
import itTranslations from './locales/it.json';
import nlTranslations from './locales/nl.json';
import plTranslations from './locales/pl.json';
import svTranslations from './locales/sv.json';
import daTranslations from './locales/da.json';
import fiTranslations from './locales/fi.json';
import csTranslations from './locales/cs.json';
import huTranslations from './locales/hu.json';
import roTranslations from './locales/ro.json';
import elTranslations from './locales/el.json';
// Additional EU Languages
import bgTranslations from './locales/bg.json';
import hrTranslations from './locales/hr.json';
import etTranslations from './locales/et.json';
import gaTranslations from './locales/ga.json';
import lvTranslations from './locales/lv.json';
import ltTranslations from './locales/lt.json';
import skTranslations from './locales/sk.json';
import slTranslations from './locales/sl.json';
import mtTranslations from './locales/mt.json';

const resources = {
  // English variants
  'en-US': {
    translation: enUSTranslations
  },
  'en-GB': {
    translation: enGBTranslations
  },
  // Romance languages
  es: {
    translation: esTranslations
  },
  fr: {
    translation: frTranslations
  },
  it: {
    translation: itTranslations
  },
  'pt-BR': {
    translation: ptBRTranslations
  },
  'pt-PT': {
    translation: ptPTTranslations
  },
  ro: {
    translation: roTranslations
  },
  // Germanic languages
  de: {
    translation: deTranslations
  },
  nl: {
    translation: nlTranslations
  },
  sv: {
    translation: svTranslations
  },
  da: {
    translation: daTranslations
  },
  // Slavic languages
  pl: {
    translation: plTranslations
  },
  cs: {
    translation: csTranslations
  },
  bg: {
    translation: bgTranslations
  },
  hr: {
    translation: hrTranslations
  },
  sk: {
    translation: skTranslations
  },
  sl: {
    translation: slTranslations
  },
  // Finno-Ugric languages
  fi: {
    translation: fiTranslations
  },
  hu: {
    translation: huTranslations
  },
  et: {
    translation: etTranslations
  },
  // Baltic languages
  lv: {
    translation: lvTranslations
  },
  lt: {
    translation: ltTranslations
  },
  // Celtic languages
  ga: {
    translation: gaTranslations
  },
  // Hellenic languages
  el: {
    translation: elTranslations
  },
  // Semitic languages
  mt: {
    translation: mtTranslations
  }
};

i18n
  // detect user language
  .use(LanguageDetector)
  // pass the i18n instance to react-i18next.
  .use(initReactI18next)
  // init i18next
  .init({
    resources,
    fallbackLng: 'en-US',
    debug: process.env.NODE_ENV === 'development',
    
    // Language fallback configuration for all 24 EU official languages
    supportedLngs: [
      'en-US', 'en-GB', // English variants
      'es', 'fr', 'it', 'pt-BR', 'pt-PT', 'ro', // Romance languages
      'de', 'nl', 'sv', 'da', // Germanic languages  
      'pl', 'cs', 'bg', 'hr', 'sk', 'sl', // Slavic languages
      'fi', 'hu', 'et', // Finno-Ugric and Estonian
      'lv', 'lt', // Baltic languages
      'ga', // Celtic languages
      'el', // Hellenic languages
      'mt' // Semitic languages (Maltese)
    ],
    nonExplicitSupportedLngs: false, // Only use explicitly supported languages
    cleanCode: true, // Clean language codes
    
    interpolation: {
      escapeValue: false, // not needed for react as it escapes by default
    },
    
    // Language detection options
    detection: {
      order: ['querystring', 'cookie', 'localStorage', 'navigator', 'htmlTag'],
      caches: ['localStorage', 'cookie'],
      lookupQuerystring: 'lng',
      lookupCookie: 'i18next',
      lookupLocalStorage: 'i18nextLng',
      lookupFromPathIndex: 0,
      lookupFromSubdomainIndex: 0,
      
      // Enhanced language mapping for auto-detection
      convertDetectedLanguage: (lng) => {
        console.log('🔍 Detected language:', lng); // Debug logging
        
        // Handle English variants
        if (lng.startsWith('en-US') || lng === 'en-us') return 'en-US';
        if (lng.startsWith('en-GB') || lng === 'en-gb' || lng.startsWith('en-UK')) return 'en-GB';
        if (lng === 'en' || lng.startsWith('en-')) {
          // Check full browser language for region detection
          const fullLang = navigator.language || navigator.languages?.[0] || '';
          console.log('🌐 Full browser language:', fullLang);
          
          if (fullLang.includes('GB') || fullLang.includes('UK') || fullLang === 'en-GB') {
            console.log('🇬🇧 Detected UK English, using en-GB');
            return 'en-GB';
          }
          console.log('🇺🇸 Defaulting to US English, using en-US');
          return 'en-US'; // Default to American English for any English variant
        }
        
        // Handle Portuguese variants
        if (lng.startsWith('pt-BR') || lng === 'pt-br') return 'pt-BR';
        if (lng.startsWith('pt-PT') || lng === 'pt-pt') return 'pt-PT';
        if (lng === 'pt' || lng.startsWith('pt-')) {
          const fullLang = navigator.language || navigator.languages?.[0] || '';
          if (fullLang.includes('PT') || fullLang === 'pt-PT') {
            console.log('🇵🇹 Detected Portugal Portuguese, using pt-PT');
            return 'pt-PT';
          }
          console.log('🇧🇷 Defaulting to Brazilian Portuguese, using pt-BR');
          return 'pt-BR'; // Default to Brazilian Portuguese
        }
        
        // Handle Spanish variants (keep as standard Spanish for now)
        if (lng.startsWith('es')) {
          console.log('🇪🇸 Detected Spanish, using es');
          return 'es';
        }
        
        // Handle French variants
        if (lng.startsWith('fr')) {
          console.log('🇫🇷 Detected French, using fr');
          return 'fr';
        }
        
        // Handle German variants
        if (lng.startsWith('de')) {
          console.log('🇩🇪 Detected German, using de');
          return 'de';
        }
        
        // Handle Italian variants
        if (lng.startsWith('it')) {
          console.log('🇮🇹 Detected Italian, using it');
          return 'it';
        }
        
        // Handle Dutch variants
        if (lng.startsWith('nl')) {
          console.log('🇳🇱 Detected Dutch, using nl');
          return 'nl';
        }
        
        // Handle Polish variants
        if (lng.startsWith('pl')) {
          console.log('🇵🇱 Detected Polish, using pl');
          return 'pl';
        }
        
        // Handle Swedish variants
        if (lng.startsWith('sv')) {
          console.log('🇸🇪 Detected Swedish, using sv');
          return 'sv';
        }
        
        // Handle Danish variants
        if (lng.startsWith('da')) {
          console.log('🇩🇰 Detected Danish, using da');
          return 'da';
        }
        
        // Handle Finnish variants
        if (lng.startsWith('fi')) {
          console.log('🇫🇮 Detected Finnish, using fi');
          return 'fi';
        }
        
        // Handle Czech variants
        if (lng.startsWith('cs')) {
          console.log('🇨🇿 Detected Czech, using cs');
          return 'cs';
        }
        
        // Handle Hungarian variants
        if (lng.startsWith('hu')) {
          console.log('🇭🇺 Detected Hungarian, using hu');
          return 'hu';
        }
        
        // Handle Romanian variants
        if (lng.startsWith('ro')) {
          console.log('🇷🇴 Detected Romanian, using ro');
          return 'ro';
        }
        
        // Handle Greek variants
        if (lng.startsWith('el')) {
          console.log('🇬🇷 Detected Greek, using el');
          return 'el';
        }
        
        // Handle Bulgarian variants
        if (lng.startsWith('bg')) {
          console.log('🇧🇬 Detected Bulgarian, using bg');
          return 'bg';
        }
        
        // Handle Croatian variants
        if (lng.startsWith('hr')) {
          console.log('🇭🇷 Detected Croatian, using hr');
          return 'hr';
        }
        
        // Handle Estonian variants
        if (lng.startsWith('et')) {
          console.log('🇪🇪 Detected Estonian, using et');
          return 'et';
        }
        
        // Handle Irish variants
        if (lng.startsWith('ga')) {
          console.log('🇮🇪 Detected Irish, using ga');
          return 'ga';
        }
        
        // Handle Latvian variants
        if (lng.startsWith('lv')) {
          console.log('🇱🇻 Detected Latvian, using lv');
          return 'lv';
        }
        
        // Handle Lithuanian variants
        if (lng.startsWith('lt')) {
          console.log('🇱🇹 Detected Lithuanian, using lt');
          return 'lt';
        }
        
        // Handle Slovak variants
        if (lng.startsWith('sk')) {
          console.log('🇸🇰 Detected Slovak, using sk');
          return 'sk';
        }
        
        // Handle Slovene variants
        if (lng.startsWith('sl')) {
          console.log('🇸🇮 Detected Slovene, using sl');
          return 'sl';
        }
        
        // Handle Maltese variants
        if (lng.startsWith('mt')) {
          console.log('🇲🇹 Detected Maltese, using mt');
          return 'mt';
        }
        
        // For any unsupported language, fall back to English (USA)
        console.log('❌ Unsupported language detected, falling back to en-US:', lng);
        return 'en-US';
      }
    },
  })
  .catch((error) => {
    console.error('i18n initialization failed, falling back to en-US:', error);
    // If initialization fails, manually set to English (USA)
    i18n.changeLanguage('en-US');
  });

// Additional fallback check after initialization
i18n.on('initialized', () => {
  const currentLanguage = i18n.language;
  console.log('🌍 i18n initialized with language:', currentLanguage);
  console.log('🗣️ Browser language:', navigator.language);
  console.log('🗣️ Browser languages:', navigator.languages);
  
  // If the current language is not in our supported list, fall back to English (USA)
  const supportedLanguages = [
    'en-US', 'en-GB', // English variants
    'es', 'fr', 'it', 'pt-BR', 'pt-PT', 'ro', // Romance languages
    'de', 'nl', 'sv', 'da', // Germanic languages  
    'pl', 'cs', 'bg', 'hr', 'sk', 'sl', // Slavic languages
    'fi', 'hu', 'et', // Finno-Ugric and Estonian
    'lv', 'lt', // Baltic languages
    'ga', // Celtic languages
    'el', // Hellenic languages
    'mt' // Semitic languages (Maltese)
  ];
  if (!supportedLanguages.includes(currentLanguage)) {
    console.log('⚠️ Current language not supported, switching to en-US');
    i18n.changeLanguage('en-US');
  }
});

// Handle language detection failure
i18n.on('languageChanged', (lng) => {
  console.log('Language changed to:', lng);
  // Store the selected language in localStorage for persistence
  localStorage.setItem('i18nextLng', lng);
});

export default i18n;
