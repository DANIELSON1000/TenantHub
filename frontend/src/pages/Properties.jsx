import { useEffect, useState } from 'react';

import { Plus, Pencil, Trash2, X, BedDouble, Sparkles } from 'lucide-react';

import { api } from '../services/api';

import { useLanguage } from '../context/LanguageContext';



function PropertyModal({ property, onClose, onSave }) {

  const { t, formatMoney, formatRoomCount } = useLanguage();

  const [form, setForm] = useState(property || { name: '', address: '', unit: '', rooms: '1', monthly_rent: '', hygiene_fee: '', description: '' });



  const handleSubmit = async (e) => {

    e.preventDefault();

    const data = {

      ...form,

      rooms: parseInt(form.rooms, 10),

      monthly_rent: parseInt(form.monthly_rent, 10),

      hygiene_fee: parseInt(form.hygiene_fee, 10) || 0,

    };

    if (property) {

      await api.updateProperty(property.id, data);

    } else {

      await api.createProperty(data);

    }

    onSave();

  };



  return (

    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">

      <div className="card w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto">

        <div className="flex justify-between items-center mb-6">

          <h2 className="text-lg font-semibold text-accent">{property ? t.properties.edit : t.properties.add}</h2>

          <button onClick={onClose}><X className="w-5 h-5 text-slate-400" /></button>

        </div>

        <form onSubmit={handleSubmit} className="space-y-4">

          <div><label className="label">{t.properties.name}</label><input className="input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required /></div>

          <div><label className="label">{t.properties.address}</label><input className="input" value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} required /></div>

          <div><label className="label">{t.properties.unit}</label><input className="input" value={form.unit} onChange={(e) => setForm({ ...form, unit: e.target.value })} placeholder="12B" /></div>

          <div className="grid grid-cols-2 gap-4">

            <div>

              <label className="label">{t.properties.rooms}</label>

              <input type="number" min="1" max="20" className="input" value={form.rooms} onChange={(e) => setForm({ ...form, rooms: e.target.value })} required />

            </div>

            <div>

              <label className="label">{t.properties.rent}</label>

              <input type="number" min="0" step="1000" className="input" value={form.monthly_rent} onChange={(e) => setForm({ ...form, monthly_rent: e.target.value })} required placeholder="250000" />

            </div>

          </div>

          <div>

            <label className="label flex items-center gap-1.5">

              <Sparkles className="w-3.5 h-3.5 text-teal-600" />

              {t.properties.hygieneFee}

            </label>

            <input type="number" min="0" step="500" className="input" value={form.hygiene_fee} onChange={(e) => setForm({ ...form, hygiene_fee: e.target.value })} placeholder="5000" />

            <p className="text-xs text-slate-500 mt-1">{t.properties.hygieneFeeHint}</p>

          </div>

          <div><label className="label">{t.properties.description}</label><textarea className="input" rows={3} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></div>

          <div className="flex gap-3 pt-2">

            <button type="submit" className="btn-primary flex-1">Save</button>

            <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>

          </div>

        </form>

      </div>

    </div>

  );

}



export default function Properties() {

  const { t, formatMoney, formatRoomCount } = useLanguage();

  const [properties, setProperties] = useState([]);

  const [modal, setModal] = useState(null);

  const [loading, setLoading] = useState(true);



  const load = () => api.getProperties().then(setProperties).finally(() => setLoading(false));

  useEffect(() => { load(); }, []);



  const handleDelete = async (id) => {

    if (!confirm('Delete this property?')) return;

    await api.deleteProperty(id);

    load();

  };



  if (loading) return <div className="text-accent">{t.loading}</div>;



  return (

    <div>

      <div className="flex items-center justify-between mb-8">

        <div>

          <h1 className="page-title">{t.properties.title}</h1>

          <p className="page-subtitle">{t.properties.subtitle}</p>

        </div>

        <button onClick={() => setModal('new')} className="btn-primary"><Plus className="w-4 h-4" /> {t.properties.add}</button>

      </div>



      {properties.length === 0 ? (

        <div className="card p-12 text-center text-slate-500">{t.properties.empty}</div>

      ) : (

        <div className="grid gap-4 md:grid-cols-2">

          {properties.map((p) => (

            <div key={p.id} className="card p-5 flex flex-col justify-between gap-4 hover:shadow-md transition-shadow">

              <div>

                <div className="flex items-center gap-2 mb-2">

                  <h3 className="font-semibold text-lg text-value">{p.name}</h3>

                  <span className="badge-blue flex items-center gap-1">

                    <BedDouble className="w-3 h-3" />

                    {formatRoomCount(p.rooms)}

                  </span>

                </div>

                <p className="text-slate-500 text-sm">{p.address}{p.unit ? `, ${p.unit}` : ''}</p>

                <p className="text-money-lg mt-2">{formatMoney(p.monthly_rent)}<span className="text-sm font-normal text-slate-500">{t.properties.perMonth}</span></p>

                {Number(p.hygiene_fee) > 0 && (

                  <p className="text-sm text-teal-700 mt-1 flex items-center gap-1">

                    <Sparkles className="w-3.5 h-3.5" />

                    {t.payments.hygiene}: {formatMoney(p.hygiene_fee)}{t.properties.perMonth}

                  </p>

                )}

                {p.description && <p className="text-sm text-slate-500 mt-2">{p.description}</p>}

              </div>

              <div className="flex gap-2">

                <button onClick={() => setModal(p)} className="btn-secondary flex-1"><Pencil className="w-4 h-4" /> Edit</button>

                <button onClick={() => handleDelete(p.id)} className="btn-danger"><Trash2 className="w-4 h-4" /></button>

              </div>

            </div>

          ))}

        </div>

      )}



      {modal && <PropertyModal property={modal === 'new' ? null : modal} onClose={() => setModal(null)} onSave={() => { setModal(null); load(); }} />}

    </div>

  );

}


