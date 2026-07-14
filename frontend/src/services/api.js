const API_BASE = import.meta.env.VITE_API_URL || '/api';

function getToken() {
  return localStorage.getItem('token');
}

async function request(endpoint, options = {}) {
  const token = getToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
    ...options.headers,
  };

  const res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    throw new Error(data.error || 'Request failed');
  }
  return data;
}

export const api = {
  login: (email, password) => request('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  forgotPassword: (email) => request('/auth/forgot-password', { method: 'POST', body: JSON.stringify({ email }) }),
  resetPassword: (token, password) => request('/auth/reset-password', { method: 'POST', body: JSON.stringify({ token, password }) }),
  register: (data) => request('/auth/register', { method: 'POST', body: JSON.stringify(data) }),
  me: () => request('/auth/me'),

  getDashboard: () => request('/dashboard'),
  getProperties: () => request('/properties'),
  createProperty: (data) => request('/properties', { method: 'POST', body: JSON.stringify(data) }),
  updateProperty: (id, data) => request(`/properties/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteProperty: (id) => request(`/properties/${id}`, { method: 'DELETE' }),

  getTenants: () => request('/tenants'),
  getTenant: (id) => request(`/tenants/${id}`),
  createTenant: (data) => request('/tenants', { method: 'POST', body: JSON.stringify(data) }),
  updateTenant: (id, data) => request(`/tenants/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  getAvailableUsers: () => request('/tenants/users/available'),

  getMessages: () => request('/messages'),
  getContacts: () => request('/messages/contacts'),
  getConversation: (userId) => request(`/messages/conversation/${userId}`),
  sendMessage: (data) => request('/messages', { method: 'POST', body: JSON.stringify(data) }),
  sendBroadcast: (data) => request('/messages/broadcast', { method: 'POST', body: JSON.stringify(data) }),
  getUnreadCount: () => request('/messages/unread-count'),

  getAgreements: () => request('/agreements'),
  createAgreement: (data) => request('/agreements', { method: 'POST', body: JSON.stringify(data) }),
  signAgreement: (id) => request(`/agreements/${id}/sign`, { method: 'PATCH' }),
  downloadAgreementPdf: (id) => {
    const token = getToken();
    return fetch(`${API_BASE}/agreements/${id}/pdf`, {
      headers: { Authorization: `Bearer ${token}` },
    });
  },

  getPayments: (type) => request(type ? `/payments?type=${type}` : '/payments'),
  getPaymentAnalytics: () => request('/payments/analytics'),
  createPayment: (data) => request('/payments', { method: 'POST', body: JSON.stringify(data) }),
  markPaymentPaid: (id, data) => request(`/payments/${id}/pay`, { method: 'PATCH', body: JSON.stringify(data) }),

  getNotifications: () => request('/notifications'),
  getNotificationUnreadCount: () => request('/notifications/unread-count'),
  markNotificationRead: (id) => request(`/notifications/${id}/read`, { method: 'PATCH' }),
  markAllNotificationsRead: () => request('/notifications/read-all', { method: 'PATCH' }),
};

/** Rwandan Francs — never uses dollar sign */
export function formatCurrency(amount) {
  const value = Number(amount) || 0;
  return `${new Intl.NumberFormat('en-RW').format(value)} Frw`;
}

export function formatRooms(rooms) {
  if (!rooms) return '—';
  return rooms === 1 ? '1 room' : `${rooms} rooms`;
}

export function formatDate(date) {
  if (!date) return '—';
  return new Date(date + (date.includes('T') ? '' : 'T00:00:00')).toLocaleDateString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric',
  });
}

export function statusBadge(status) {
  const map = {
    active: 'badge-green', paid: 'badge-green', signed: 'badge-green',
    pending: 'badge-yellow', draft: 'badge-gray', sent: 'badge-blue',
    overdue: 'badge-red', inactive: 'badge-gray', partial: 'badge-yellow',
  };
  return map[status] || 'badge-gray';
}
