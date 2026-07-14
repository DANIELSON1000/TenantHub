import { useEffect, useState } from 'react';
import { Plus, Pencil, X, Calendar, Shield } from 'lucide-react';
import { api, formatCurrency, formatDate, statusBadge, formatRooms } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';

function clampDay(day) {
  const n = parseInt(day, 10);
  if (Number.isNaN(n)) return 1;
  return Math.min(Math.max(n, 1), 28);
}

export function dayFromMoveIn(moveInDate) {
  if (!moveInDate) return 1;
  return clampDay(moveInDate.split('-')[2]);
}

export function dueDateFromPaymentDay(paymentDay) {
  const day = clampDay(paymentDay);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  let y = today.getFullYear();
  let m = today.getMonth() + 1;
  const lastDay = new Date(y, m, 0).getDate();
  let candidate = new Date(y, m - 1, Math.min(day, lastDay));
  if (today > candidate) {
    m += 1;
    if (m > 12) { m = 1; y += 1; }
    const lastDay2 = new Date(y, m, 0).getDate();
    candidate = new Date(y, m - 1, Math.min(day, lastDay2));
  }
  return candidate.toISOString().slice(0, 10);
}

function getTenantPaymentDay(tenant) {
  return tenant.move_in_date ? dayFromMoveIn(tenant.move_in_date) : (tenant.payment_day || 1);
}

function PaymentDayBadge({ tenant }) {
  const { t } = useLanguage();
  const day = getTenantPaymentDay(tenant);
  return (
    <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-brand-100 text-brand-800 text-sm font-semibold">
      <Calendar className="w-4 h-4" />
      {t.tenants.paymentDayDisplay(day)}
    </span>
  );
}

function TenantModal({ onClose, onSave }) {
  const { t } = useLanguage();
  const [users, setUsers] = useState([]);
  const [properties, setProperties] = useState([]);
  const [form, setForm] = useState({
    user_id: '', property_id: '', move_in_date: '',
    emergency_contact: '', emergency_phone: '', notes: '',
  });

  useEffect(() => {
    Promise.all([api.getAvailableUsers(), api.getProperties()]).then(([u, p]) => {
      setUsers(u);
      setProperties(p);
    });
  }, []);

  const paymentDayPreview = form.move_in_date ? dayFromMoveIn(form.move_in_date) : null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    await api.createTenant({
      ...form,
      user_id: parseInt(form.user_id, 10),
      property_id: parseInt(form.property_id, 10),
    });
    onSave();
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="card w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-lg font-semibold">{t.tenants.assign}</h2>
          <button onClick={onClose}><X className="w-5 h-5 text-slate-400" /></button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="label">Tenant User</label>
            <select className="input" value={form.user_id} onChange={(e) => setForm({ ...form, user_id: e.target.value })} required>
              <option value="">Select tenant...</option>
              {users.map((u) => <option key={u.id} value={u.id}>{u.full_name} ({u.email})</option>)}
            </select>
          </div>
          <div>
            <label className="label">Property</label>
            <select className="input" value={form.property_id} onChange={(e) => setForm({ ...form, property_id: e.target.value })} required>
              <option value="">Select property...</option>
              {properties.map((p) => <option key={p.id} value={p.id}>{p.name} — {formatRooms(p.rooms)} — {formatCurrency(p.monthly_rent)}/mo</option>)}
            </select>
          </div>

          <div className="rounded-xl border-2 border-orange-200 bg-orange-50/50 p-4 space-y-3">
            <p className="text-sm font-semibold text-orange-800 flex items-center gap-1.5">
              <Shield className="w-4 h-4" />
              {t.tenants.adminControls}
            </p>
            <div>
              <label className="label flex items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5 text-brand-600" />
                {t.tenants.moveInDate}
              </label>
              <input
                type="date"
                className="input"
                value={form.move_in_date}
                onChange={(e) => setForm({ ...form, move_in_date: e.target.value })}
                required
              />
              <p className="text-xs text-slate-500 mt-1">{t.tenants.moveInHint}</p>
              {paymentDayPreview && (
                <p className="text-sm font-medium text-brand-700 mt-2">
                  {t.tenants.paymentDayDisplay(paymentDayPreview)}
                </p>
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div><label className="label">Emergency Contact</label><input className="input" value={form.emergency_contact} onChange={(e) => setForm({ ...form, emergency_contact: e.target.value })} /></div>
            <div><label className="label">Emergency Phone</label><input className="input" value={form.emergency_phone} onChange={(e) => setForm({ ...form, emergency_phone: e.target.value })} /></div>
          </div>
          <div><label className="label">Notes</label><textarea className="input" rows={2} value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} /></div>
          <div className="flex gap-3 pt-2">
            <button type="submit" className="btn-primary flex-1">{t.tenants.assign}</button>
            <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
          </div>
        </form>
      </div>
    </div>
  );
}

function EditTenantModal({ tenant, isLandlord, onClose, onSave }) {
  const { t } = useLanguage();
  const [form, setForm] = useState({
    emergency_contact: tenant.emergency_contact || '',
    emergency_phone: tenant.emergency_phone || '',
    move_in_date: tenant.move_in_date || '',
    status: tenant.status,
    notes: tenant.notes || '',
  });

  const paymentDayPreview = form.move_in_date ? dayFromMoveIn(form.move_in_date) : null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    const payload = isLandlord
      ? form
      : { emergency_contact: form.emergency_contact, emergency_phone: form.emergency_phone };
    await api.updateTenant(tenant.id, payload);
    onSave();
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="card w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-lg font-semibold">{isLandlord ? `${t.tenants.edit} — ${tenant.full_name}` : t.tenants.updateInfo}</h2>
          <button onClick={onClose}><X className="w-5 h-5 text-slate-400" /></button>
        </div>

        {!isLandlord && (
          <p className="text-sm text-slate-600 bg-slate-50 border border-slate-200 rounded-lg px-4 py-3 mb-4">
            {t.tenants.emergencyOnly}
          </p>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {isLandlord && (
            <div className="rounded-xl border-2 border-orange-200 bg-orange-50/50 p-4 space-y-3">
              <p className="text-sm font-semibold text-orange-800 flex items-center gap-1.5">
                <Shield className="w-4 h-4" />
                {t.tenants.adminControls}
              </p>
              <div>
                <label className="label flex items-center gap-1.5">
                  <Calendar className="w-3.5 h-3.5 text-brand-600" />
                  {t.tenants.moveInDate}
                </label>
                <input
                  type="date"
                  className="input"
                  value={form.move_in_date}
                  onChange={(e) => setForm({ ...form, move_in_date: e.target.value })}
                  required
                />
                <p className="text-xs text-slate-500 mt-1">{t.tenants.moveInHint}</p>
                {paymentDayPreview && (
                  <p className="text-sm font-medium text-brand-700 mt-2">
                    {t.tenants.paymentDayDisplay(paymentDayPreview)}
                  </p>
                )}
              </div>
              <div>
                <label className="label">Status</label>
                <select className="input" value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                  <option value="pending">Pending</option>
                </select>
              </div>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div><label className="label">Emergency Contact</label><input className="input" value={form.emergency_contact} onChange={(e) => setForm({ ...form, emergency_contact: e.target.value })} /></div>
            <div><label className="label">Emergency Phone</label><input className="input" value={form.emergency_phone} onChange={(e) => setForm({ ...form, emergency_phone: e.target.value })} /></div>
          </div>

          {isLandlord && (
            <div><label className="label">Notes</label><textarea className="input" rows={2} value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} /></div>
          )}

          <div className="flex gap-3 pt-2">
            <button type="submit" className="btn-primary flex-1">Save</button>
            <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function Tenants() {
  const { isLandlord } = useAuth();
  const { t } = useLanguage();
  const [tenants, setTenants] = useState([]);
  const [showAdd, setShowAdd] = useState(false);
  const [editTenant, setEditTenant] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = () => api.getTenants().then(setTenants).finally(() => setLoading(false));
  useEffect(() => { load(); }, []);

  if (loading) return <div className="text-slate-500">{t.loading}</div>;

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold">{isLandlord ? t.tenants.title : t.tenants.myInfo}</h1>
          <p className="text-slate-500">{isLandlord ? t.tenants.subtitle : t.tenants.myInfoSubtitle}</p>
        </div>
        {isLandlord && (
          <button onClick={() => setShowAdd(true)} className="btn-primary"><Plus className="w-4 h-4" /> {t.tenants.assign}</button>
        )}
      </div>

      {tenants.length === 0 ? (
        <div className="card p-12 text-center text-slate-500">{t.tenants.empty}</div>
      ) : (
        <div className="grid gap-4">
          {tenants.map((tn) => (
            <div key={tn.id} className="card p-5">
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex flex-wrap items-center gap-3 mb-3">
                    <h3 className="font-semibold text-lg">{tn.full_name}</h3>
                    <span className={statusBadge(tn.status)}>{tn.status}</span>
                    <PaymentDayBadge tenant={tn} />
                  </div>
                  <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3 text-sm">
                    <div><span className="text-slate-500">Email:</span> {tn.email}</div>
                    <div><span className="text-slate-500">Phone:</span> {tn.user_phone || tn.phone || '—'}</div>
                    <div><span className="text-slate-500">Property:</span> {tn.property_name}</div>
                    <div><span className="text-slate-500">Size:</span> {formatRooms(tn.rooms)}</div>
                    <div><span className="text-slate-500">Rent:</span> {formatCurrency(tn.monthly_rent)}/mo</div>
                    {Number(tn.hygiene_fee) > 0 && (
                      <div><span className="text-slate-500">{t.payments.hygiene}:</span> {formatCurrency(tn.hygiene_fee)}/mo</div>
                    )}
                    <div><span className="text-slate-500">{t.tenants.moveInDate}:</span> {formatDate(tn.move_in_date)}</div>
                    <div><span className="text-slate-500">Emergency:</span> {tn.emergency_contact || '—'} {tn.emergency_phone && `(${tn.emergency_phone})`}</div>
                  </div>
                  <p className="text-xs text-brand-700 mt-3 font-medium">{t.tenants.moveInHint}</p>
                  {tn.notes && <p className="text-sm text-slate-500 mt-3 border-t pt-3">{tn.notes}</p>}
                </div>
                <button onClick={() => setEditTenant(tn)} className="btn-secondary shrink-0">
                  <Pencil className="w-4 h-4" /> {isLandlord ? t.tenants.edit : t.tenants.updateInfo}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {showAdd && <TenantModal onClose={() => setShowAdd(false)} onSave={() => { setShowAdd(false); load(); }} />}
      {editTenant && (
        <EditTenantModal
          tenant={editTenant}
          isLandlord={isLandlord}
          onClose={() => setEditTenant(null)}
          onSave={() => { setEditTenant(null); load(); }}
        />
      )}
    </div>
  );
}
