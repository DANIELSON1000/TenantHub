import { Globe } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

export default function LanguageSwitcher({ compact = false }) {
  const { lang, changeLanguage, t } = useLanguage();

  return (
    <div className={compact ? '' : 'px-3 py-2'}>
      {!compact && (
        <label className="flex items-center gap-2 text-xs font-medium text-slate-500 mb-2">
          <Globe className="w-3.5 h-3.5" />
          {t.language}
        </label>
      )}
      <div className="flex rounded-lg border border-slate-200 overflow-hidden bg-slate-50">
        <button
          onClick={() => changeLanguage('en')}
          className={`flex-1 px-3 py-1.5 text-xs font-semibold transition-colors ${
            lang === 'en' ? 'bg-brand-600 text-white' : 'text-slate-600 hover:bg-white'
          }`}
        >
          EN
        </button>
        <button
          onClick={() => changeLanguage('rw')}
          className={`flex-1 px-3 py-1.5 text-xs font-semibold transition-colors ${
            lang === 'rw' ? 'bg-brand-600 text-white' : 'text-slate-600 hover:bg-white'
          }`}
        >
          RW
        </button>
      </div>
    </div>
  );
}
