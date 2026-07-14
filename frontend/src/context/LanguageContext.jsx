import { createContext, useContext, useState, useCallback } from 'react';
import { translations } from '../i18n/translations';

const LanguageContext = createContext(null);

export function LanguageProvider({ children }) {
  const [lang, setLang] = useState(() => localStorage.getItem('lang') || 'en');

  const changeLanguage = useCallback((newLang) => {
    setLang(newLang);
    localStorage.setItem('lang', newLang);
  }, []);

  const t = translations[lang] || translations.en;

  const formatMoney = useCallback((amount) => t.currency(amount), [t]);
  const formatRoomCount = useCallback((rooms) => {
    if (!rooms) return '—';
    return t.rooms(rooms);
  }, [t]);

  const notifTitle = useCallback((n) => (lang === 'rw' ? n.title_rw : n.title_en), [lang]);
  const notifMessage = useCallback((n) => (lang === 'rw' ? n.message_rw : n.message_en), [lang]);

  return (
    <LanguageContext.Provider value={{ lang, changeLanguage, t, formatMoney, formatRoomCount, notifTitle, notifMessage }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  return useContext(LanguageContext);
}
