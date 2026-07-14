import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Users, Building2, MessageSquare, CreditCard, AlertTriangle, Banknote, Bell } from 'lucide-react';
import { api, formatDate } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';

function StatCard({ icon: Icon, label, value, color = 'brand', alert, money }) {
  const colors = {
    brand: 'bg-brand-50 text-brand-600',
    green: 'bg-emerald-50 text-emerald-600',
    red: 'bg-red-50 text-red-600',
    yellow: 'bg-amber-50 text-amber-600',
  };
  return (
    <div className={`card p-5 ${alert ? 'border-red-300 bg-red-50/30' : ''}`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-label mb-1">{label}</p>
          <p className={`text-2xl font-bold ${money ? 'text-money-lg' : 'text-slate-900'}`}>{value}</p>
        </div>
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${colors[color]}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const { isLandlord } = useAuth();
  const { t, formatMoney, formatRoomCount } = useLanguage();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getDashboard().then(setData).catch(console.error).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-accent">{t.loading}</div>;
  if (!data) return <div className="text-danger">Error</div>;

  if (isLandlord) {
    const { stats } = data;
    return (
      <div>
        <h1 className="page-title mb-1">{t.dashboard.title}</h1>
        <p className="page-subtitle mb-8">{t.dashboard.subtitle}</p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
          <StatCard icon={Users} label={t.dashboard.activeTenants} value={stats.activeTenants} />
          <StatCard icon={Building2} label={t.dashboard.properties} value={stats.properties} />
          <StatCard icon={Banknote} label={t.dashboard.revenueMonth} value={formatMoney(stats.monthlyRevenue)} color="green" money />
          <StatCard icon={CreditCard} label={t.dashboard.pendingPayments} value={stats.pendingPayments} color="yellow" />
          <StatCard icon={AlertTriangle} label={t.dashboard.overduePayments} value={stats.overduePayments} color="red" alert={stats.overduePayments > 0} />
          <StatCard icon={MessageSquare} label={t.dashboard.unreadMessages} value={stats.unreadMessages} />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link to="/tenants" className="card p-5 hover:border-brand-300 hover:shadow-md transition-all group">
            <Users className="w-8 h-8 text-brand-600 mb-3 group-hover:scale-110 transition-transform" />
            <h3 className="font-semibold text-accent mb-1">{t.dashboard.manageTenants}</h3>
          </Link>
          <Link to="/payments" className="card p-5 hover:border-emerald-300 hover:shadow-md transition-all group">
            <CreditCard className="w-8 h-8 text-emerald-600 mb-3 group-hover:scale-110 transition-transform" />
            <h3 className="font-semibold text-emerald-700 mb-1">{t.dashboard.paymentAnalytics}</h3>
          </Link>
          <Link to="/messages" className="card p-5 hover:border-brand-300 hover:shadow-md transition-all group">
            <MessageSquare className="w-8 h-8 text-brand-600 mb-3 group-hover:scale-110 transition-transform" />
            <h3 className="font-semibold text-accent mb-1">{t.nav.messages}</h3>
          </Link>
        </div>
      </div>
    );
  }

  const { tenant, stats } = data;
  if (!tenant) {
    return (
      <div className="card p-8 text-center">
        <h2 className="text-xl font-semibold text-accent mb-2">{t.dashboard.noProperty}</h2>
        <p className="text-slate-500">{t.dashboard.noPropertyDesc}</p>
      </div>
    );
  }

  const showReminder = stats.nextPayment && ['pending', 'overdue'].includes(stats.nextPayment.status);

  return (
    <div>
      <h1 className="page-title mb-1">{t.dashboard.welcome}, {tenant.full_name?.split(' ')[0]}</h1>
      <p className="page-subtitle mb-8">{t.dashboard.yourOverview}</p>

      {showReminder && (
        <div className={`card p-4 mb-6 flex items-start gap-3 border-l-4 ${stats.nextPayment.status === 'overdue' ? 'border-l-red-500 bg-red-50/50' : 'border-l-amber-500 bg-amber-50/50'}`}>
          <Bell className={`w-5 h-5 shrink-0 mt-0.5 ${stats.nextPayment.status === 'overdue' ? 'text-red-600' : 'text-amber-600'}`} />
          <div>
            <p className={`font-semibold ${stats.nextPayment.status === 'overdue' ? 'text-danger' : 'text-warning'}`}>
              {t.payments.reminders}
            </p>
            <p className="text-sm text-slate-600 mt-1">
              {formatMoney(stats.nextPayment.amount)} — {t.payments.dueDate}: {formatDate(stats.nextPayment.due_date)}
            </p>
            <p className="text-xs text-slate-500 mt-1">{t.payments.remindersDesc}</p>
          </div>
        </div>
      )}

      <div className="card p-6 mb-8 border-brand-100">
        <h2 className="font-semibold text-lg text-accent mb-4">{t.dashboard.yourProperty}</h2>
        <div className="grid sm:grid-cols-2 gap-4">
          <div><p className="text-label">{t.dashboard.property}</p><p className="text-value">{tenant.property_name}</p></div>
          <div><p className="text-label">{t.dashboard.address}</p><p className="text-value">{tenant.property_address}</p></div>
          <div><p className="text-label">{t.dashboard.size}</p><p className="text-value">{formatRoomCount(tenant.rooms)}</p></div>
          <div><p className="text-label">{t.dashboard.monthlyRent}</p><p className="text-money-lg">{formatMoney(stats.monthlyRent)}</p></div>
          <div><p className="text-label">{t.tenants.moveInDate}</p><p className="text-value">{formatDate(tenant.move_in_date)}</p></div>
          <div><p className="text-label">{t.dashboard.paymentDay}</p><p className="text-value font-semibold text-brand-700">{t.dashboard.paysEveryMonth(tenant.move_in_date ? parseInt(tenant.move_in_date.split('-')[2], 10) : (tenant.payment_day || 1))}</p></div>
          <div><p className="text-label">{t.dashboard.landlord}</p><p className="text-value">{tenant.landlord_name}</p></div>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        <StatCard icon={Banknote} label={t.dashboard.paidThisYear} value={formatMoney(stats.paidThisYear)} color="green" money />
        <StatCard icon={MessageSquare} label={t.dashboard.unreadMessages} value={stats.unreadMessages} />
        <StatCard
          icon={CreditCard}
          label={t.dashboard.nextPaymentDue}
          value={stats.nextPayment ? formatMoney(stats.nextPayment.amount) : t.dashboard.none}
          color={stats.nextPayment?.status === 'overdue' ? 'red' : 'yellow'}
          money={!!stats.nextPayment}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Link to="/my-info" className="card p-5 hover:border-brand-300 transition-colors">
          <Users className="w-8 h-8 text-brand-600 mb-3" />
          <h3 className="font-semibold text-accent">{t.dashboard.updateInfo}</h3>
        </Link>
        <Link to="/payments" className="card p-5 hover:border-emerald-300 transition-colors">
          <CreditCard className="w-8 h-8 text-emerald-600 mb-3" />
          <h3 className="font-semibold text-emerald-700">{t.dashboard.paymentHistory}</h3>
        </Link>
        <Link to="/messages" className="card p-5 hover:border-brand-300 transition-colors">
          <MessageSquare className="w-8 h-8 text-brand-600 mb-3" />
          <h3 className="font-semibold text-accent">{t.dashboard.contactLandlord}</h3>
        </Link>
      </div>
    </div>
  );
}
