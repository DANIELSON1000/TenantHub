import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, Users, Building2, MessageSquare, FileText,
  CreditCard, LogOut, Home, Menu, X,
} from 'lucide-react';
import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import LanguageSwitcher from './LanguageSwitcher';
import NotificationPanel from './NotificationPanel';

export default function Layout({ children }) {
  const { user, logout, isLandlord } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const landlordNav = [
    { to: '/', icon: LayoutDashboard, label: t.nav.dashboard },
    { to: '/properties', icon: Building2, label: t.nav.properties },
    { to: '/tenants', icon: Users, label: t.nav.tenants },
    { to: '/payments', icon: CreditCard, label: t.nav.payments },
    { to: '/agreements', icon: FileText, label: t.nav.agreements },
    { to: '/messages', icon: MessageSquare, label: t.nav.messages },
  ];

  const tenantNav = [
    { to: '/', icon: LayoutDashboard, label: t.nav.dashboard },
    { to: '/my-info', icon: Users, label: t.nav.myInfo },
    { to: '/payments', icon: CreditCard, label: t.nav.payments },
    { to: '/agreements', icon: FileText, label: t.nav.agreements },
    { to: '/messages', icon: MessageSquare, label: t.nav.messages },
  ];

  const nav = isLandlord ? landlordNav : tenantNav;

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen flex bg-gradient-to-br from-slate-50 via-brand-50/30 to-slate-100">
      {sidebarOpen && (
        <div className="fixed inset-0 bg-black/50 z-40 lg:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      <aside className={`fixed lg:static inset-y-0 left-0 z-50 w-64 bg-white border-r border-brand-100 flex flex-col transform transition-transform lg:translate-x-0 shadow-sm ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="p-6 border-b border-brand-100 bg-gradient-to-br from-brand-600 to-brand-800 text-white">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-white/20 flex items-center justify-center">
              <Home className="w-5 h-5" />
            </div>
            <div>
              <h1 className="font-bold text-lg">{t.appName}</h1>
              <p className="text-xs text-brand-100">{isLandlord ? t.adminPortal : t.tenantPortal}</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 p-4 space-y-1">
          {nav.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-gradient-to-r from-brand-600 to-brand-500 text-white shadow-md shadow-brand-500/25'
                    : 'text-slate-600 hover:bg-brand-50 hover:text-brand-700'
                }`
              }
            >
              <Icon className="w-5 h-5" />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-slate-200 space-y-3">
          <LanguageSwitcher />
          <div className="px-3 py-2 rounded-lg bg-slate-50">
            <p className="text-sm font-semibold text-brand-800">{user?.full_name}</p>
            <p className="text-xs text-slate-500">{user?.email}</p>
          </div>
          <button onClick={handleLogout} className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm font-medium text-red-600 hover:bg-red-50 transition-colors">
            <LogOut className="w-5 h-5" />
            {t.signOut}
          </button>
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="bg-white/80 backdrop-blur border-b border-brand-100 px-4 py-3 flex items-center gap-3 sticky top-0 z-30">
          <button onClick={() => setSidebarOpen(true)} className="lg:hidden p-2 rounded-lg hover:bg-brand-50">
            <Menu className="w-5 h-5 text-brand-700" />
          </button>
          <span className="font-bold bg-gradient-to-r from-brand-700 to-brand-500 bg-clip-text text-transparent lg:hidden">
            {t.appName}
          </span>
          <div className="ml-auto flex items-center gap-2">
            <div className="hidden sm:block"><LanguageSwitcher compact /></div>
            {!isLandlord && <NotificationPanel />}
            {sidebarOpen && (
              <button onClick={() => setSidebarOpen(false)} className="lg:hidden p-2">
                <X className="w-5 h-5" />
              </button>
            )}
          </div>
        </header>
        <main className="flex-1 p-4 lg:p-8 overflow-auto">{children}</main>
      </div>
    </div>
  );
}
