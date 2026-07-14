import { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { Mail, Lock, Home, ArrowLeft, CheckCircle } from 'lucide-react';
import { api } from '../services/api';
import { useLanguage } from '../context/LanguageContext';
import LanguageSwitcher from '../components/LanguageSwitcher';

export default function ResetPassword() {
  const { t } = useLanguage();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token') || '';

  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (password !== confirm) {
      setError(t.forgotPassword.mismatch);
      return;
    }
    if (!token) {
      setError(t.forgotPassword.invalidLink);
      return;
    }
    setLoading(true);
    try {
      await api.resetPassword(token, password);
      setDone(true);
      setTimeout(() => navigate('/login'), 3000);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <AuthShell>
        <div className="text-center space-y-4">
          <p className="text-red-600">{t.forgotPassword.invalidLink}</p>
          <Link to="/login" className="text-brand-600 font-semibold hover:underline inline-flex items-center gap-1">
            <ArrowLeft className="w-4 h-4" /> {t.forgotPassword.backToLogin}
          </Link>
        </div>
      </AuthShell>
    );
  }

  return (
    <AuthShell title={t.forgotPassword.resetTitle} subtitle={t.forgotPassword.resetSubtitle}>
      {done ? (
        <div className="text-center space-y-4 py-4">
          <div className="w-14 h-14 rounded-full bg-green-100 flex items-center justify-center mx-auto">
            <CheckCircle className="w-8 h-8 text-green-600" />
          </div>
          <p className="text-green-700 font-medium">{t.forgotPassword.resetSuccess}</p>
          <p className="text-sm text-slate-500">{t.forgotPassword.redirecting}</p>
        </div>
      ) : (
        <>
          {error && (
            <div className="mb-4 p-3 rounded-lg bg-red-50 text-red-700 text-sm border border-red-200">{error}</div>
          )}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label text-brand-800">{t.forgotPassword.newPassword}</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-brand-400" />
                <input
                  type="password"
                  className="input pl-10 border-brand-200"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={6}
                />
              </div>
            </div>
            <div>
              <label className="label text-brand-800">{t.forgotPassword.confirmPassword}</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-brand-400" />
                <input
                  type="password"
                  className="input pl-10 border-brand-200"
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  required
                  minLength={6}
                />
              </div>
            </div>
            <button type="submit" disabled={loading} className="btn-primary w-full py-2.5">
              {loading ? t.pleaseWait : t.forgotPassword.resetButton}
            </button>
          </form>
          <p className="mt-6 text-center">
            <Link to="/login" className="text-sm text-brand-600 font-semibold hover:underline inline-flex items-center gap-1">
              <ArrowLeft className="w-4 h-4" /> {t.forgotPassword.backToLogin}
            </Link>
          </p>
        </>
      )}
    </AuthShell>
  );
}

function AuthShell({ title, subtitle, children }) {
  const { t } = useLanguage();
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
          <h1 className="text-2xl font-bold text-brand-700">{title || t.appName}</h1>
        </div>
        {subtitle && <p className="text-slate-500 text-sm">{subtitle}</p>}
      </div>
      <div className="w-full max-w-md card p-8 shadow-lg border-brand-100/80">{children}</div>
    </div>
  );
}

export function ForgotPasswordForm({ onBack }) {
  const { t } = useLanguage();
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await api.forgotPassword(email);
      setSent(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (sent) {
    return (
      <div className="text-center space-y-4">
        <div className="w-14 h-14 rounded-full bg-brand-100 flex items-center justify-center mx-auto">
          <Mail className="w-7 h-7 text-brand-600" />
        </div>
        <p className="text-brand-800 font-medium">{t.forgotPassword.emailSent}</p>
        <p className="text-sm text-slate-500">{t.forgotPassword.checkInbox}</p>
        <button onClick={onBack} className="text-brand-600 font-semibold hover:underline text-sm">
          {t.forgotPassword.backToLogin}
        </button>
      </div>
    );
  }

  return (
    <>
      {error && (
        <div className="mb-4 p-3 rounded-lg bg-red-50 text-red-700 text-sm border border-red-200">{error}</div>
      )}
      <form onSubmit={handleSubmit} className="space-y-4">
        <p className="text-sm text-slate-600">{t.forgotPassword.instructions}</p>
        <div>
          <label className="label text-brand-800">{t.email}</label>
          <div className="relative">
            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-brand-400" />
            <input
              type="email"
              className="input pl-10 border-brand-200"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoFocus
            />
          </div>
        </div>
        <button type="submit" disabled={loading} className="btn-primary w-full py-2.5">
          {loading ? t.pleaseWait : t.forgotPassword.sendLink}
        </button>
      </form>
      <p className="mt-6 text-center">
        <button onClick={onBack} className="text-sm text-brand-600 font-semibold hover:underline inline-flex items-center gap-1">
          <ArrowLeft className="w-4 h-4" /> {t.forgotPassword.backToLogin}
        </button>
      </p>
    </>
  );
}
