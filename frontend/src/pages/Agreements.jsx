import { useEffect, useState } from 'react';
import { Plus, Download, FileCheck, X } from 'lucide-react';
import { api, formatDate, statusBadge } from '../services/api';
import { useAuth } from '../context/AuthContext';

function CreateAgreementModal({ onClose, onSave }) {
  const [tenants, setTenants] = useState([]);
  const [form, setForm] = useState({ tenant_id: '', title: 'Residential Lease Agreement', terms: '' });

  useEffect(() => { api.getTenants().then(setTenants); }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    await api.createAgreement({ ...form, tenant_id: parseInt(form.tenant_id) });
    onSave();
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="card w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-lg font-semibold">Generate Agreement</h2>
          <button onClick={onClose}><X className="w-5 h-5 text-slate-400" /></button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="label">Tenant</label>
            <select className="input" value={form.tenant_id} onChange={(e) => setForm({ ...form, tenant_id: e.target.value })} required>
              <option value="">Select tenant...</option>
              {tenants.map((t) => <option key={t.id} value={t.id}>{t.full_name} - {t.property_name}</option>)}
            </select>
          </div>
          <div><label className="label">Title</label><input className="input" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} /></div>
          <div>
            <label className="label">Additional Terms</label>
            <textarea className="input" rows={5} value={form.terms} onChange={(e) => setForm({ ...form, terms: e.target.value })}
              placeholder="Enter any additional lease terms and conditions..." />
          </div>
          <div className="flex gap-3 pt-2">
            <button type="submit" className="btn-primary flex-1">Generate & Send</button>
            <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
          </div>
        </form>
      </div>
    </div>
  );
}

function AgreementView({ agreement, onClose, onSign }) {
  const { isLandlord } = useAuth();

  const handleDownload = async () => {
    const res = await api.downloadAgreementPdf(agreement.id);
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `agreement-${agreement.id}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="card w-full max-w-2xl p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-start mb-6">
          <div>
            <h2 className="text-lg font-semibold">{agreement.title}</h2>
            <p className="text-sm text-slate-500">{agreement.tenant_name} · {agreement.property_name}</p>
          </div>
          <button onClick={onClose}><X className="w-5 h-5 text-slate-400" /></button>
        </div>
        <pre className="whitespace-pre-wrap text-sm bg-slate-50 rounded-lg p-4 border border-slate-200 font-sans leading-relaxed">
          {agreement.content}
        </pre>
        <div className="flex items-center gap-3 mt-6">
          <span className={statusBadge(agreement.status)}>{agreement.status}</span>
          {agreement.signed_at && <span className="text-sm text-slate-500">Signed {formatDate(agreement.signed_at)}</span>}
        </div>
        <div className="flex gap-3 mt-6">
          <button onClick={handleDownload} className="btn-secondary"><Download className="w-4 h-4" /> Download PDF</button>
          {agreement.status !== 'signed' && !isLandlord && (
            <button onClick={onSign} className="btn-primary"><FileCheck className="w-4 h-4" /> Sign Agreement</button>
          )}
        </div>
      </div>
    </div>
  );
}

export default function Agreements() {
  const { isLandlord } = useAuth();
  const [agreements, setAgreements] = useState([]);
  const [showCreate, setShowCreate] = useState(false);
  const [viewing, setViewing] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = () => api.getAgreements().then(setAgreements).finally(() => setLoading(false));
  useEffect(() => { load(); }, []);

  const handleSign = async () => {
    await api.signAgreement(viewing.id);
    setViewing(null);
    load();
  };

  if (loading) return <div className="text-slate-500">Loading...</div>;

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold">Agreements</h1>
          <p className="text-slate-500">Lease documents and contracts</p>
        </div>
        {isLandlord && (
          <button onClick={() => setShowCreate(true)} className="btn-primary"><Plus className="w-4 h-4" /> Generate Agreement</button>
        )}
      </div>

      {agreements.length === 0 ? (
        <div className="card p-12 text-center text-slate-500">No agreements yet.</div>
      ) : (
        <div className="grid gap-4">
          {agreements.map((a) => (
            <div key={a.id} className="card p-5 flex items-center justify-between gap-4 cursor-pointer hover:border-brand-300 transition-colors" onClick={() => setViewing(a)}>
              <div>
                <div className="flex items-center gap-3 mb-1">
                  <h3 className="font-semibold">{a.title}</h3>
                  <span className={statusBadge(a.status)}>{a.status}</span>
                </div>
                <p className="text-sm text-slate-500">{a.tenant_name} · {a.property_name} · Created {formatDate(a.created_at)}</p>
              </div>
              <button className="btn-secondary text-sm">View</button>
            </div>
          ))}
        </div>
      )}

      {showCreate && <CreateAgreementModal onClose={() => setShowCreate(false)} onSave={() => { setShowCreate(false); load(); }} />}
      {viewing && <AgreementView agreement={viewing} onClose={() => setViewing(null)} onSign={handleSign} />}
    </div>
  );
}
