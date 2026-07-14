import { useEffect, useState, useRef, useMemo } from 'react';

import { Send, ArrowLeft, Users, X, Check, Building2, UserCheck } from 'lucide-react';

import { api, formatDate } from '../services/api';

import { useAuth } from '../context/AuthContext';

import { useLanguage } from '../context/LanguageContext';



function getBubbleStyle(isMine, senderRole) {

  const isLandlord = senderRole === 'landlord';



  if (isLandlord) {

    return isMine

      ? {

          bubble: 'bg-gradient-to-br from-orange-500 via-amber-500 to-orange-600 text-white shadow-lg shadow-orange-500/30 rounded-2xl rounded-br-sm border border-orange-400',

          name: 'text-orange-600 font-semibold',

          subject: 'text-orange-100',

        }

      : {

          bubble: 'bg-gradient-to-br from-orange-50 to-amber-100 text-orange-950 shadow-md rounded-2xl rounded-bl-sm border-2 border-orange-300',

          name: 'text-orange-700 font-semibold',

          subject: 'text-orange-800',

        };

  }



  return isMine

    ? {

        bubble: 'bg-gradient-to-br from-violet-600 via-purple-500 to-indigo-600 text-white shadow-lg shadow-violet-500/30 rounded-2xl rounded-br-sm border border-violet-400',

        name: 'text-violet-600 font-semibold',

        subject: 'text-violet-100',

      }

    : {

        bubble: 'bg-gradient-to-br from-violet-50 to-purple-100 text-violet-950 shadow-md rounded-2xl rounded-bl-sm border-2 border-violet-300',

        name: 'text-violet-700 font-semibold',

        subject: 'text-violet-800',

      };

}



function BroadcastModal({ onClose, onSent }) {

  const { t } = useLanguage();

  const m = t.messages;

  const [tenants, setTenants] = useState([]);

  const [properties, setProperties] = useState([]);

  const [mode, setMode] = useState('all');

  const [propertyId, setPropertyId] = useState('');

  const [selectedIds, setSelectedIds] = useState(new Set());

  const [subject, setSubject] = useState('');

  const [body, setBody] = useState('');

  const [sending, setSending] = useState(false);

  const [error, setError] = useState('');

  const [success, setSuccess] = useState(null);



  useEffect(() => {

    Promise.all([api.getTenants(), api.getProperties()]).then(([tenantList, propList]) => {

      const active = tenantList.filter((tn) => tn.status === 'active');

      setTenants(active);

      setProperties(propList);

      setSelectedIds(new Set(active.map((tn) => tn.user_id)));

    });

  }, []);



  const recipientCount = useMemo(() => {

    if (mode === 'all') return tenants.length;

    if (mode === 'property') {

      if (!propertyId) return 0;

      return tenants.filter((tn) => String(tn.property_id) === propertyId).length;

    }

    return selectedIds.size;

  }, [mode, tenants, propertyId, selectedIds]);



  const toggleTenant = (userId) => {

    setSelectedIds((prev) => {

      const next = new Set(prev);

      if (next.has(userId)) next.delete(userId);

      else next.add(userId);

      return next;

    });

  };



  const selectAll = () => setSelectedIds(new Set(tenants.map((tn) => tn.user_id)));

  const deselectAll = () => setSelectedIds(new Set());



  const handleSend = async (e) => {

    e.preventDefault();

    if (!body.trim() || recipientCount === 0) return;

    setSending(true);

    setError('');

    try {

      const payload = { subject: subject.trim() || undefined, body: body.trim() };

      if (mode === 'property' && propertyId) payload.property_id = parseInt(propertyId, 10);

      else if (mode === 'pick') payload.user_ids = [...selectedIds];

      const result = await api.sendBroadcast(payload);

      setSuccess(result.sent);

      setTimeout(() => {

        onSent();

        onClose();

      }, 1500);

    } catch (err) {

      setError(err.message);

    } finally {

      setSending(false);

    }

  };



  const modes = [

    { id: 'all', icon: Users, label: m.allTenants },

    { id: 'property', icon: Building2, label: m.byProperty },

    { id: 'pick', icon: UserCheck, label: m.pickTenants },

  ];



  return (

    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">

      <div className="card w-full max-w-xl p-0 max-h-[90vh] overflow-hidden flex flex-col shadow-2xl">

        <div className="p-6 border-b border-slate-200 bg-gradient-to-r from-orange-50 to-amber-50">

          <div className="flex justify-between items-start gap-3">

            <div>

              <h2 className="text-lg font-bold text-accent flex items-center gap-2">

                <Users className="w-5 h-5 text-orange-500" />

                {m.broadcastTitle}

              </h2>

              <p className="text-sm text-slate-600 mt-1">{m.broadcastDesc}</p>

            </div>

            <button onClick={onClose} className="p-1 hover:bg-white/60 rounded-lg transition-colors">

              <X className="w-5 h-5 text-slate-400" />

            </button>

          </div>

        </div>



        {success ? (

          <div className="flex-1 flex flex-col items-center justify-center p-10 text-center">

            <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mb-4">

              <Check className="w-8 h-8 text-green-600" />

            </div>

            <p className="text-lg font-semibold text-green-700">{m.sentSuccess(success)}</p>

          </div>

        ) : (

          <form onSubmit={handleSend} className="flex-1 overflow-y-auto p-6 space-y-5">

            <div>

              <label className="label mb-2 block">{m.recipientMode}</label>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">

                {modes.map(({ id, icon: Icon, label }) => (

                  <button

                    key={id}

                    type="button"

                    onClick={() => setMode(id)}

                    className={`flex items-center gap-2 p-3 rounded-xl border-2 text-sm font-medium transition-all ${

                      mode === id

                        ? 'border-orange-400 bg-orange-50 text-orange-800 shadow-sm'

                        : 'border-slate-200 bg-white text-slate-600 hover:border-orange-200 hover:bg-orange-50/50'

                    }`}

                  >

                    <Icon className="w-4 h-4 shrink-0" />

                    <span className="text-left leading-tight">{label}</span>

                  </button>

                ))}

              </div>

            </div>



            {mode === 'property' && (

              <div>

                <label className="label">{m.selectProperty}</label>

                <select

                  className="input"

                  value={propertyId}

                  onChange={(e) => setPropertyId(e.target.value)}

                  required

                >

                  <option value="">—</option>

                  {properties.map((p) => (

                    <option key={p.id} value={p.id}>{p.name}</option>

                  ))}

                </select>

              </div>

            )}



            {mode === 'pick' && (

              <div>

                <div className="flex items-center justify-between mb-2">

                  <label className="label mb-0">{m.selectTenants}</label>

                  <div className="flex gap-2 text-xs">

                    <button type="button" onClick={selectAll} className="text-orange-600 hover:underline font-medium">

                      {m.selectAll}

                    </button>

                    <span className="text-slate-300">|</span>

                    <button type="button" onClick={deselectAll} className="text-slate-500 hover:underline">

                      {m.deselectAll}

                    </button>

                  </div>

                </div>

                <div className="border border-slate-200 rounded-xl max-h-40 overflow-y-auto divide-y divide-slate-100">

                  {tenants.length === 0 ? (

                    <p className="p-4 text-sm text-slate-500 text-center">—</p>

                  ) : (

                    tenants.map((tn) => (

                      <label

                        key={tn.user_id}

                        className={`flex items-center gap-3 p-3 cursor-pointer hover:bg-slate-50 transition-colors ${

                          selectedIds.has(tn.user_id) ? 'bg-orange-50/50' : ''

                        }`}

                      >

                        <input

                          type="checkbox"

                          checked={selectedIds.has(tn.user_id)}

                          onChange={() => toggleTenant(tn.user_id)}

                          className="w-4 h-4 rounded border-slate-300 text-orange-500 focus:ring-orange-400"

                        />

                        <div className="flex-1 min-w-0">

                          <p className="text-sm font-medium text-value truncate">{tn.full_name}</p>

                          <p className="text-xs text-slate-500 truncate">{tn.property_name}</p>

                        </div>

                      </label>

                    ))

                  )}

                </div>

              </div>

            )}



            <div

              className={`rounded-xl px-4 py-3 text-sm font-medium text-center ${

                recipientCount > 0

                  ? 'bg-orange-100 text-orange-800 border border-orange-200'

                  : 'bg-slate-100 text-slate-500 border border-slate-200'

              }`}

            >

              {recipientCount > 0 ? m.willSendTo(recipientCount) : m.noRecipients}

            </div>



            <div>

              <label className="label">{m.subject}</label>

              <input

                className="input"

                placeholder={m.subjectPlaceholder}

                value={subject}

                onChange={(e) => setSubject(e.target.value)}

              />

            </div>



            <div>

              <label className="label">{m.message}</label>

              <textarea

                className="input min-h-[120px] resize-y"

                placeholder={m.messagePlaceholder}

                value={body}

                onChange={(e) => setBody(e.target.value)}

                required

              />

            </div>



            {error && (

              <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-2">{error}</p>

            )}



            <div className="flex gap-3 pt-1">

              <button

                type="submit"

                disabled={sending || !body.trim() || recipientCount === 0}

                className="btn-primary flex-1 disabled:opacity-50 disabled:cursor-not-allowed"

              >

                <Send className="w-4 h-4" />

                {sending ? m.sending : mode === 'all' ? m.sendToAll : m.sendNow}

              </button>

              <button type="button" onClick={onClose} className="btn-secondary">

                {m.cancel}

              </button>

            </div>

          </form>

        )}

      </div>

    </div>

  );

}



export default function Messages() {

  const { user, isLandlord } = useAuth();

  const { t } = useLanguage();

  const m = t.messages;

  const [contacts, setContacts] = useState([]);

  const [selected, setSelected] = useState(null);

  const [messages, setMessages] = useState([]);

  const [newMsg, setNewMsg] = useState({ subject: '', body: '' });

  const [loading, setLoading] = useState(true);

  const [showBroadcast, setShowBroadcast] = useState(false);

  const bottomRef = useRef(null);



  const loadContacts = () => api.getContacts().then(setContacts);



  useEffect(() => {

    loadContacts().finally(() => setLoading(false));

  }, []);



  useEffect(() => {

    if (selected) {

      api.getConversation(selected.id).then(setMessages);

    }

  }, [selected]);



  useEffect(() => {

    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });

  }, [messages]);



  const handleSend = async (e) => {

    e.preventDefault();

    if (!newMsg.body.trim()) return;

    await api.sendMessage({

      receiver_id: selected.id,

      subject: newMsg.subject || 'Message',

      body: newMsg.body,

    });

    setNewMsg({ subject: '', body: '' });

    const updated = await api.getConversation(selected.id);

    setMessages(updated);

    loadContacts();

  };



  if (loading) return <div className="text-accent">{t.loading}</div>;



  return (

    <div>

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">

        <div>

          <h1 className="page-title mb-1">{t.nav.messages}</h1>

          <p className="page-subtitle">{m.subtitle}</p>

        </div>

        {isLandlord && (

          <button

            onClick={() => setShowBroadcast(true)}

            className="btn-primary shrink-0 self-start sm:self-auto"

          >

            <Users className="w-4 h-4" />

            {m.messageTenants}

          </button>

        )}

      </div>



      <div className="card overflow-hidden border-brand-100" style={{ height: 'calc(100vh - 220px)', minHeight: '400px' }}>

        <div className="flex h-full">

          <div className={`w-full sm:w-72 border-r border-slate-200 flex flex-col bg-slate-50/50 ${selected ? 'hidden sm:flex' : 'flex'}`}>

            <div className="p-4 border-b border-slate-200 font-semibold text-accent">{m.contacts}</div>

            <div className="flex-1 overflow-y-auto">

              {contacts.length === 0 ? (

                <p className="p-4 text-sm text-slate-500">—</p>

              ) : (

                contacts.map((c) => (

                  <button

                    key={c.id}

                    onClick={() => setSelected(c)}

                    className={`w-full text-left p-4 border-b border-slate-100 hover:bg-white transition-colors ${selected?.id === c.id ? `bg-white border-l-4 ${c.role === 'landlord' ? 'border-l-orange-500' : 'border-l-violet-500'}` : ''}`}

                  >

                    <div className="flex items-center justify-between gap-2">

                      <p className="font-medium text-sm text-value">{c.full_name}</p>

                      {c.unread > 0 && <span className="badge-red">{c.unread}</span>}

                    </div>

                    <p className={`text-xs capitalize mt-0.5 ${c.role === 'landlord' ? 'text-orange-600' : 'text-violet-600'}`}>

                      {c.role === 'landlord' ? t.adminPortal : t.tenantPortal}

                    </p>

                  </button>

                ))

              )}

            </div>

          </div>



          <div className={`flex-1 flex flex-col bg-gradient-to-b from-slate-50 to-white ${!selected ? 'hidden sm:flex' : 'flex'}`}>

            {selected ? (

              <>

                <div className="p-4 border-b border-slate-200 bg-white flex items-center justify-between gap-3 flex-wrap">

                  <div className="flex items-center gap-3">

                    <button onClick={() => setSelected(null)} className="sm:hidden p-1"><ArrowLeft className="w-5 h-5" /></button>

                    <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-bold text-sm shrink-0 ${selected.role === 'landlord' ? 'bg-gradient-to-br from-orange-500 to-amber-600' : 'bg-gradient-to-br from-violet-500 to-purple-600'}`}>

                      {selected.full_name?.charAt(0)}

                    </div>

                    <div>

                      <p className="font-semibold text-value">{selected.full_name}</p>

                      <p className={`text-xs capitalize ${selected.role === 'landlord' ? 'text-orange-600' : 'text-violet-600'}`}>

                        {selected.role === 'landlord' ? t.adminPortal : t.tenantPortal}

                      </p>

                    </div>

                  </div>

                  <div className="flex gap-3 text-xs">

                    <span className="flex items-center gap-1.5">

                      <span className="w-3 h-3 rounded-full bg-gradient-to-br from-orange-500 to-amber-500" />

                      <span className="text-orange-700 font-medium">{m.landlord}</span>

                    </span>

                    <span className="flex items-center gap-1.5">

                      <span className="w-3 h-3 rounded-full bg-gradient-to-br from-violet-500 to-purple-600" />

                      <span className="text-violet-700 font-medium">{m.tenant}</span>

                    </span>

                  </div>

                </div>



                <div className="flex-1 overflow-y-auto p-4 space-y-4">

                  {messages.map((msg) => {

                    const isMine = msg.sender_id === user?.id;

                    const senderRole = msg.sender_role || (isMine ? user?.role : selected.role);

                    const style = getBubbleStyle(isMine, senderRole);



                    return (

                      <div key={msg.id} className={`flex flex-col max-w-[85%] ${isMine ? 'ml-auto items-end' : 'items-start'}`}>

                        <p className={`text-xs mb-1 px-1 ${style.name}`}>{msg.sender_name}</p>

                        <div className={`px-4 py-3 ${style.bubble}`}>

                          {msg.subject && msg.subject !== 'Message' && (

                            <p className={`text-sm font-semibold mb-1 ${style.subject}`}>{msg.subject}</p>

                          )}

                          <p className="text-sm whitespace-pre-wrap leading-relaxed">{msg.body}</p>

                        </div>

                        <p className={`text-xs text-slate-400 mt-1 px-1 ${isMine ? 'text-right' : ''}`}>

                          {formatDate(msg.created_at)}

                        </p>

                      </div>

                    );

                  })}

                  <div ref={bottomRef} />

                </div>



                <form onSubmit={handleSend} className="p-4 border-t border-slate-200 bg-white flex gap-2">

                  <input

                    className="input flex-1"

                    placeholder={m.typeMessage}

                    value={newMsg.body}

                    onChange={(e) => setNewMsg({ ...newMsg, body: e.target.value })}

                  />

                  <button type="submit" className="btn-primary shrink-0"><Send className="w-4 h-4" /></button>

                </form>

              </>

            ) : (

              <div className="flex-1 flex flex-col items-center justify-center text-slate-400 gap-3 p-6 text-center">

                <p>{m.selectContact}</p>

                {isLandlord && (

                  <button

                    onClick={() => setShowBroadcast(true)}

                    className="text-orange-600 hover:text-orange-700 font-medium text-sm flex items-center gap-1.5"

                  >

                    <Users className="w-4 h-4" />

                    {m.messageTenants}

                  </button>

                )}

              </div>

            )}

          </div>

        </div>

      </div>



      {showBroadcast && (

        <BroadcastModal

          onClose={() => setShowBroadcast(false)}

          onSent={loadContacts}

        />

      )}

    </div>

  );

}


