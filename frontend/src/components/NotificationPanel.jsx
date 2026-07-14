import { useState, useEffect } from 'react';
import { Bell, X, Mail } from 'lucide-react';
import { api } from '../services/api';
import { useLanguage } from '../context/LanguageContext';

export default function NotificationPanel() {
  const { t, notifTitle, notifMessage } = useLanguage();
  const [open, setOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unread, setUnread] = useState(0);

  const load = () => {
    Promise.all([api.getNotifications(), api.getNotificationUnreadCount()])
      .then(([n, c]) => { setNotifications(n); setUnread(c.count); })
      .catch(() => {});
  };

  useEffect(() => { load(); const id = setInterval(load, 60000); return () => clearInterval(id); }, []);

  const markAllRead = async () => {
    await api.markAllNotificationsRead();
    load();
  };

  const markRead = async (id) => {
    await api.markNotificationRead(id);
    load();
  };

  return (
    <div className="relative">
      <button
        onClick={() => { setOpen(!open); if (!open) load(); }}
        className="relative p-2 rounded-lg hover:bg-brand-50 text-brand-700 transition-colors"
      >
        <Bell className="w-5 h-5" />
        {unread > 0 && (
          <span className="absolute -top-0.5 -right-0.5 w-5 h-5 bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center">
            {unread > 9 ? '9+' : unread}
          </span>
        )}
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute right-0 top-full mt-2 w-80 sm:w-96 card shadow-xl z-50 border-brand-100 overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b bg-gradient-to-r from-brand-50 to-white">
              <h3 className="font-semibold text-brand-800">{t.notifications.title}</h3>
              <div className="flex items-center gap-2">
                {unread > 0 && (
                  <button onClick={markAllRead} className="text-xs text-brand-600 hover:underline">
                    {t.notifications.markAllRead}
                  </button>
                )}
                <button onClick={() => setOpen(false)}><X className="w-4 h-4 text-slate-400" /></button>
              </div>
            </div>
            <div className="max-h-80 overflow-y-auto">
              {notifications.length === 0 ? (
                <p className="p-6 text-center text-slate-500 text-sm">{t.notifications.empty}</p>
              ) : (
                notifications.map((n) => (
                  <button
                    key={n.id}
                    onClick={() => !n.is_read && markRead(n.id)}
                    className={`w-full text-left p-4 border-b border-slate-100 hover:bg-slate-50 transition-colors ${!n.is_read ? 'bg-amber-50/60 border-l-4 border-l-amber-400' : ''}`}
                  >
                    <div className="flex items-start gap-2">
                      <div className="w-8 h-8 rounded-lg bg-amber-100 text-amber-700 flex items-center justify-center shrink-0 mt-0.5">
                        <Bell className="w-4 h-4" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-sm text-slate-900">{notifTitle(n)}</p>
                        <p className="text-xs text-slate-600 mt-1 leading-relaxed">{notifMessage(n)}</p>
                        {n.email_sent && (
                          <span className="inline-flex items-center gap-1 text-xs text-emerald-600 mt-2">
                            <Mail className="w-3 h-3" /> {t.notifications.emailSent}
                          </span>
                        )}
                      </div>
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
