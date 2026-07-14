import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mail, Lock, User, Phone, Home } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import LanguageSwitcher from '../components/LanguageSwitcher';
import { ForgotPasswordForm } from './ResetPassword';

export default function Login() {
  const [isRegister, setIsRegister] = useState(false);
  const [showForgot, setShowForgot] = useState(false);
  const [form, setForm] = useState({ email: '', password: '', full_name: '', phone: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, register } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (isRegister) {
        await register(form);
      } else {
        await login(form.email, form.password);
      }
      navigate('/');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const switchMode = (register) => {
    setIsRegister(register);
    setShowForgot(false);
    setError('');
    setForm({ email: '', password: '', full_name: '', phone: '' });
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-8 bg-gradient-to-b from-brand-50 via-white to-brand-50/50">
      <div className="absolute top-4 right-4 w-36">
        <LanguageSwitcher />
      </div>

      <div className="text-center mb-6">
        <div className="inline-flex items-center justify-center gap-2.5 mb-2">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center shadow-md shadow-brand-500/20">
            <Home className="w-5 h-5 text-white" />
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight bg-gradient-to-r from-brand-700 via-brand-600 to-emerald-600 bg-clip-text text-transparent">
            {t.appName}
          </h1>
        </div>
        <p className="text-slate-500 text-xs sm:text-sm">{t.motto}</p>
      </div>

      <div className="w-full max-w-md card p-8 shadow-lg border-brand-100/80">
        {showForgot ? (
          <>
            <h2 className="text-lg font-semibold text-accent mb-4">{t.forgotPassword.title}</h2>
            <ForgotPasswordForm onBack={() => setShowForgot(false)} />
          </>
        ) : (
          <>
            {error && (
              <div className="mb-4 p-3 rounded-lg bg-red-50 text-red-700 text-sm border border-red-200">{error}</div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              {isRegister && (
                <>
                  <div>
                    <label className="label text-brand-800">{t.fullName}</label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-brand-400" />
                      <input className="input pl-10 border-brand-200 focus:border-brand-500" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} required />
                    </div>
                  </div>
                  <div>
                    <label className="label text-brand-800">{t.phone}</label>
                    <div className="relative">
                      <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-brand-400" />
                      <input className="input pl-10 border-brand-200" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
                    </div>
                  </div>
                </>
              )}
              <div>
                <label className="label text-brand-800">{t.email}</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-brand-400" />
                  <input type="email" className="input pl-10 border-brand-200" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="label text-brand-800 mb-0">{t.password}</label>
                  {!isRegister && (
                    <button
                      type="button"
                      onClick={() => { setShowForgot(true); setError(''); }}
                      className="text-xs text-brand-600 font-medium hover:underline"
                    >
                      {t.forgotPassword.forgotLink}
                    </button>
                  )}
                </div>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-brand-400" />
                  <input type="password" className="input pl-10 border-brand-200" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required minLength={6} />
                </div>
              </div>
              <button type="submit" disabled={loading} className="btn-primary w-full py-2.5 bg-gradient-to-r from-brand-600 to-brand-500 hover:from-brand-700 hover:to-brand-600 shadow-md shadow-brand-500/30">
                {loading ? t.pleaseWait : isRegister ? t.createAccount : t.signIn}
              </button>
            </form>

            <p className="mt-6 text-center text-sm text-slate-500">
              {isRegister ? t.alreadyHaveAccount : t.noAccount}{' '}
              <button onClick={() => switchMode(!isRegister)} className="text-brand-600 font-semibold hover:text-brand-700 hover:underline">
                {isRegister ? t.signIn : t.signUp}
              </button>
            </p>
          </>
        )}
      </div>
    </div>
  );
}
