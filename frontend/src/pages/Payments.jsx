import { useEffect, useState } from 'react';

import { Plus, CheckCircle, X, TrendingUp, Home, Sparkles } from 'lucide-react';

import { api, formatDate, statusBadge } from '../services/api';

import { useAuth } from '../context/AuthContext';

import { useLanguage } from '../context/LanguageContext';
import { dueDateFromPaymentDay, dayFromMoveIn } from './Tenants';

function CreatePaymentModal({ onClose, onSave }) {

  const { t } = useLanguage();

  const [tenants, setTenants] = useState([]);

  const [form, setForm] = useState({ tenant_id: '', payment_type: 'rent', amount: '', due_date: '', notes: '' });



  useEffect(() => { api.getTenants().then(setTenants); }, []);



  const selectedTenant = tenants.find((tn) => String(tn.id) === form.tenant_id);



  const handleTenantChange = (tenantId) => {

    const tenant = tenants.find((tn) => String(tn.id) === tenantId);

    const amount = form.payment_type === 'hygiene'

      ? tenant?.hygiene_fee || ''

      : tenant?.monthly_rent || '';

    const payDay = tenant ? (tenant.move_in_date ? dayFromMoveIn(tenant.move_in_date) : tenant.payment_day) : null;
    const due_date = payDay ? dueDateFromPaymentDay(payDay) : form.due_date;
    setForm({ ...form, tenant_id: tenantId, amount: amount ? String(amount) : '', due_date });

  };



  const handleTypeChange = (paymentType) => {

    const amount = paymentType === 'hygiene'

      ? selectedTenant?.hygiene_fee || ''

      : selectedTenant?.monthly_rent || '';

    setForm({ ...form, payment_type: paymentType, amount: amount ? String(amount) : '' });

  };



  const handleSubmit = async (e) => {

    e.preventDefault();

    await api.createPayment({

      tenant_id: parseInt(form.tenant_id, 10),

      payment_type: form.payment_type,

      amount: parseInt(form.amount, 10),

      due_date: form.due_date,

      notes: form.notes || undefined,

    });

    onSave();

  };



  return (

    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">

      <div className="card w-full max-w-md p-6">

        <div className="flex justify-between items-center mb-6">

          <h2 className="text-lg font-semibold text-accent">{t.payments.addDue}</h2>

          <button onClick={onClose}><X className="w-5 h-5 text-slate-400" /></button>

        </div>

        <form onSubmit={handleSubmit} className="space-y-4">

          <div>

            <label className="label">{t.payments.type}</label>

            <div className="grid grid-cols-2 gap-2">

              <button

                type="button"

                onClick={() => handleTypeChange('rent')}

                className={`flex items-center justify-center gap-2 p-3 rounded-xl border-2 text-sm font-medium transition-all ${

                  form.payment_type === 'rent'

                    ? 'border-brand-500 bg-brand-50 text-brand-800'

                    : 'border-slate-200 text-slate-600 hover:border-brand-200'

                }`}

              >

                <Home className="w-4 h-4" />

                {t.payments.rent}

              </button>

              <button

                type="button"

                onClick={() => handleTypeChange('hygiene')}

                className={`flex items-center justify-center gap-2 p-3 rounded-xl border-2 text-sm font-medium transition-all ${

                  form.payment_type === 'hygiene'

                    ? 'border-teal-500 bg-teal-50 text-teal-800'

                    : 'border-slate-200 text-slate-600 hover:border-teal-200'

                }`}

              >

                <Sparkles className="w-4 h-4" />

                {t.payments.hygiene}

              </button>

            </div>

          </div>

          <div>

            <label className="label">{t.payments.tenant}</label>

            <select className="input" value={form.tenant_id} onChange={(e) => handleTenantChange(e.target.value)} required>

              <option value="">Select tenant...</option>

              {tenants.map((tn) => <option key={tn.id} value={tn.id}>{tn.full_name} - {tn.property_name}</option>)}

            </select>

          </div>

          <div>

            <label className="label">{t.payments.amount}</label>

            <input type="number" min="0" step="500" className="input" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} required placeholder="250000" />

          </div>

          <div>

            <label className="label">{t.payments.dueDate}</label>

            <input type="date" className="input" value={form.due_date} onChange={(e) => setForm({ ...form, due_date: e.target.value })} required />

          </div>

          <div><label className="label">Notes</label><input className="input" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} /></div>

          <div className="flex gap-3 pt-2">

            <button type="submit" className="btn-primary flex-1">Create</button>

            <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>

          </div>

        </form>

      </div>

    </div>

  );

}



function TypeBadge({ type }) {

  const { t } = useLanguage();

  if (type === 'hygiene') {

    return (

      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-teal-100 text-teal-800">

        <Sparkles className="w-3 h-3" />

        {t.payments.hygiene}

      </span>

    );

  }

  return (

    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-brand-100 text-brand-800">

      <Home className="w-3 h-3" />

      {t.payments.rent}

    </span>

  );

}



function AnalyticsPanel({ analytics }) {

  const { t, formatMoney } = useLanguage();

  const { summary, statusBreakdown, monthlyTrend } = analytics;

  const maxMonth = Math.max(...monthlyTrend.map((m) => m.due), 1);



  return (

    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-8">

      <div className="card p-5">

        <div className="flex items-center gap-2 mb-4">

          <TrendingUp className="w-5 h-5 text-brand-600" />

          <h3 className="font-semibold text-accent">{t.payments.collectionSummary}</h3>

        </div>

        <div className="space-y-3">

          <div className="flex justify-between"><span className="text-label">{t.payments.totalDue}</span><span className="text-money">{formatMoney(summary.totalDue)}</span></div>

          <div className="flex justify-between"><span className="text-label">{t.payments.collected}</span><span className="text-money">{formatMoney(summary.totalPaid)}</span></div>

          <div className="flex justify-between"><span className="text-label">{t.payments.pending}</span><span className="text-warning">{formatMoney(summary.totalPending)}</span></div>

          <div className="flex justify-between"><span className="text-label">{t.payments.overdue}</span><span className="text-danger">{formatMoney(summary.totalOverdue)}</span></div>

          {(summary.rentTotal > 0 || summary.hygieneTotal > 0) && (

            <div className="pt-2 border-t border-slate-100 space-y-1.5 text-xs">

              <div className="flex justify-between"><span className="text-slate-500">{t.payments.rent}</span><span>{formatMoney(summary.rentTotal)}</span></div>

              <div className="flex justify-between"><span className="text-slate-500">{t.payments.hygiene}</span><span>{formatMoney(summary.hygieneTotal)}</span></div>

            </div>

          )}

          <div className="pt-3 border-t">

            <div className="flex justify-between mb-2"><span className="text-label">{t.payments.collectionRate}</span><span className="font-bold text-accent">{summary.collectionRate}%</span></div>

            <div className="w-full bg-slate-100 rounded-full h-2">

              <div className="bg-brand-600 h-2 rounded-full transition-all" style={{ width: `${summary.collectionRate}%` }} />

            </div>

          </div>

        </div>

      </div>



      <div className="card p-5">

        <h3 className="font-semibold text-accent mb-4">{t.payments.statusBreakdown}</h3>

        <div className="grid grid-cols-2 gap-3">

          {Object.entries(statusBreakdown).map(([status, count]) => (

            <div key={status} className="text-center p-3 bg-slate-50 rounded-lg">

              <p className="text-2xl font-bold text-value">{count}</p>

              <span className={statusBadge(status)}>{t.status[status] || status}</span>

            </div>

          ))}

        </div>

      </div>



      <div className="card p-5">

        <h3 className="font-semibold text-accent mb-4">{t.payments.monthlyTrend}</h3>

        {monthlyTrend.length === 0 ? (

          <p className="text-sm text-slate-500">—</p>

        ) : (

          <div className="space-y-3">

            {monthlyTrend.map((m) => (

              <div key={m.month}>

                <div className="flex justify-between text-sm mb-1">

                  <span className="text-label">{m.month}</span>

                  <span className="text-money">{formatMoney(m.paid)} / {formatMoney(m.due)}</span>

                </div>

                <div className="w-full bg-slate-100 rounded-full h-2">

                  <div className="bg-green-500 h-2 rounded-full" style={{ width: `${(m.paid / maxMonth) * 100}%` }} />

                </div>

              </div>

            ))}

          </div>

        )}

      </div>

    </div>

  );

}



const FILTER_TABS = [

  { id: 'all', icon: null },

  { id: 'rent', icon: Home },

  { id: 'hygiene', icon: Sparkles },

];



export default function Payments() {

  const { isLandlord } = useAuth();

  const { t, formatMoney } = useLanguage();

  const [payments, setPayments] = useState([]);

  const [analytics, setAnalytics] = useState(null);

  const [showCreate, setShowCreate] = useState(false);

  const [loading, setLoading] = useState(true);

  const [filter, setFilter] = useState('all');



  const load = () => {

    const typeParam = filter === 'all' ? undefined : filter;

    Promise.all([api.getPayments(typeParam), api.getPaymentAnalytics()])

      .then(([p, a]) => { setPayments(p); setAnalytics(a); })

      .finally(() => setLoading(false));

  };

  useEffect(() => { setLoading(true); load(); }, [filter]);



  const handleMarkPaid = async (id) => {

    await api.markPaymentPaid(id, { payment_method: 'manual' });

    load();

  };



  const tabLabel = (id) => {

    if (id === 'all') return t.payments.allTypes;

    if (id === 'rent') return t.payments.rent;

    return t.payments.hygiene;

  };



  if (loading) return <div className="text-accent">{t.loading}</div>;



  return (

    <div>

      <div className="flex items-center justify-between mb-8">

        <div>

          <h1 className="page-title">{t.payments.title}</h1>

          <p className="page-subtitle">{t.payments.subtitle}</p>

        </div>

        {isLandlord && (

          <button onClick={() => setShowCreate(true)} className="btn-primary"><Plus className="w-4 h-4" /> {t.payments.addDue}</button>

        )}

      </div>



      {isLandlord && (

        <div className="card p-4 mb-6 bg-brand-50/50 border-brand-200 border-l-4 border-l-brand-500">

          <p className="text-sm text-brand-800 font-medium">{t.payments.autoSchedule}</p>

          <p className="text-xs text-brand-700 mt-1">{t.payments.hygieneNote}</p>

        </div>

      )}



      {!isLandlord && (

        <div className="card p-4 mb-6 bg-amber-50/50 border-amber-200 border-l-4 border-l-amber-500">

          <p className="text-sm text-amber-800 font-medium">{t.payments.reminders}</p>

          <p className="text-xs text-amber-700 mt-1">{t.payments.remindersDesc}</p>

        </div>

      )}



      <div className="flex gap-2 mb-6 flex-wrap">

        {FILTER_TABS.map(({ id, icon: Icon }) => (

          <button

            key={id}

            onClick={() => setFilter(id)}

            className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-medium transition-all ${

              filter === id

                ? id === 'hygiene'

                  ? 'bg-teal-600 text-white shadow-md'

                  : 'bg-brand-600 text-white shadow-md'

                : 'bg-white border border-slate-200 text-slate-600 hover:border-brand-300'

            }`}

          >

            {Icon && <Icon className="w-4 h-4" />}

            {tabLabel(id)}

          </button>

        ))}

      </div>



      {analytics && <AnalyticsPanel analytics={analytics} />}



      <div className="card overflow-hidden">

        <div className="overflow-x-auto">

          <table className="w-full text-sm">

            <thead className="bg-brand-50 border-b border-brand-100">

              <tr>

                {isLandlord && <th className="text-left px-4 py-3 font-medium text-accent">{t.payments.tenant}</th>}

                <th className="text-left px-4 py-3 font-medium text-accent">{t.payments.type}</th>

                <th className="text-left px-4 py-3 font-medium text-accent">{t.dashboard.property}</th>

                <th className="text-left px-4 py-3 font-medium text-accent">{t.payments.amount}</th>

                <th className="text-left px-4 py-3 font-medium text-accent">{t.payments.dueDate}</th>

                <th className="text-left px-4 py-3 font-medium text-accent">Paid</th>

                <th className="text-left px-4 py-3 font-medium text-accent">Status</th>

                <th className="text-left px-4 py-3 font-medium text-accent">Actions</th>

              </tr>

            </thead>

            <tbody>

              {payments.length === 0 ? (

                <tr><td colSpan={8} className="px-4 py-8 text-center text-slate-500">—</td></tr>

              ) : (

                payments.map((p) => (

                  <tr key={p.id} className="border-b border-slate-100 hover:bg-brand-50/30">

                    {isLandlord && <td className="px-4 py-3 text-value">{p.tenant_name}</td>}

                    <td className="px-4 py-3"><TypeBadge type={p.payment_type || 'rent'} /></td>

                    <td className="px-4 py-3">{p.property_name}</td>

                    <td className="px-4 py-3 text-money">{formatMoney(p.amount)}</td>

                    <td className="px-4 py-3">{formatDate(p.due_date)}</td>

                    <td className="px-4 py-3">{formatDate(p.paid_date)}</td>

                    <td className="px-4 py-3"><span className={statusBadge(p.status)}>{t.status[p.status] || p.status}</span></td>

                    <td className="px-4 py-3">

                      {p.status !== 'paid' && isLandlord && (

                        <button onClick={() => handleMarkPaid(p.id)} className="btn-secondary text-xs py-1">

                          <CheckCircle className="w-3 h-3" /> {t.payments.markPaid}

                        </button>

                      )}

                    </td>

                  </tr>

                ))

              )}

            </tbody>

          </table>

        </div>

      </div>



      {showCreate && <CreatePaymentModal onClose={() => setShowCreate(false)} onSave={() => { setShowCreate(false); load(); }} />}

    </div>

  );

}


