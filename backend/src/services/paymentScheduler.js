import db from '../database.js';

const MIN_DAY = 1;
const MAX_DAY = 28;

export function dayFromMoveIn(moveInDate) {
  if (!moveInDate) return 1;
  return clampPaymentDay(moveInDate.split('-')[2]);
}

export function clampPaymentDay(day) {
  const n = parseInt(day, 10);
  if (Number.isNaN(n)) return 1;
  return Math.min(Math.max(n, MIN_DAY), MAX_DAY);
}

function formatDate(y, m, day) {
  const lastDay = new Date(y, m, 0).getDate();
  const actualDay = Math.min(day, lastDay);
  return `${y}-${String(m).padStart(2, '0')}-${String(actualDay).padStart(2, '0')}`;
}

/** Next due date on the tenant's payment day (this month or next). */
export function dueDateFromPaymentDay(paymentDay, referenceDate = new Date()) {
  const day = clampPaymentDay(paymentDay);
  const ref = new Date(referenceDate);
  ref.setHours(0, 0, 0, 0);
  let y = ref.getFullYear();
  let m = ref.getMonth() + 1;

  let candidate = new Date(formatDate(y, m, day) + 'T00:00:00');
  if (ref > candidate) {
    m += 1;
    if (m > 12) {
      m = 1;
      y += 1;
    }
    candidate = new Date(formatDate(y, m, day) + 'T00:00:00');
  }
  return candidate.toISOString().slice(0, 10);
}

/** Due date for the month after currentDueDate, on paymentDay. */
export function nextMonthDueDate(paymentDay, currentDueDate) {
  const day = clampPaymentDay(paymentDay);
  const [y, m] = currentDueDate.split('-').map(Number);
  let newMonth = m + 1;
  let newYear = y;
  if (newMonth > 12) {
    newMonth = 1;
    newYear += 1;
  }
  return formatDate(newYear, newMonth, day);
}

export function getAmountForType(property, paymentType) {
  if (paymentType === 'hygiene') return Number(property.hygiene_fee) || 0;
  return Number(property.monthly_rent) || 0;
}

async function paymentExists(tenantId, paymentType, dueDate) {
  const row = await db.prepare(`
    SELECT id FROM payments
    WHERE tenant_id = ? AND payment_type = ? AND due_date = ?
  `).get(tenantId, paymentType, dueDate);
  return !!row;
}

export async function createPaymentDue({ tenantId, propertyId, amount, dueDate, paymentType, notes }) {
  if (!amount || amount <= 0) return null;
  if (await paymentExists(tenantId, paymentType, dueDate)) return null;

  const result = await db.prepare(`
    INSERT INTO payments (tenant_id, property_id, amount, due_date, payment_type, notes)
    VALUES (?, ?, ?, ?, ?, ?)
  `).run(tenantId, propertyId, amount, dueDate, paymentType, notes || null);
  return result.lastInsertRowid;
}

/** Create first rent (+ hygiene if configured) using the tenant's monthly payment day. */
export async function createInitialPayments(tenantId, property, paymentDay) {
  const dueDate = dueDateFromPaymentDay(paymentDay);
  const created = [];

  const rentId = await createPaymentDue({
    tenantId,
    propertyId: property.id,
    amount: getAmountForType(property, 'rent'),
    dueDate,
    paymentType: 'rent',
    notes: 'Monthly rent',
  });
  if (rentId) created.push(rentId);

  const hygieneAmount = getAmountForType(property, 'hygiene');
  if (hygieneAmount > 0) {
    const hygieneId = await createPaymentDue({
      tenantId,
      propertyId: property.id,
      amount: hygieneAmount,
      dueDate,
      paymentType: 'hygiene',
      notes: 'Hygiene fee',
    });
    if (hygieneId) created.push(hygieneId);
  }

  return created;
}

/** After a payment is marked paid, schedule next month on the tenant's payment day. */
export async function scheduleNextPayment(paymentId) {
  const payment = await db.prepare(`
    SELECT pay.*, p.monthly_rent, p.hygiene_fee, t.payment_day
    FROM payments pay
    JOIN properties p ON pay.property_id = p.id
    JOIN tenants t ON pay.tenant_id = t.id
    WHERE pay.id = ?
  `).get(paymentId);

  if (!payment || payment.status !== 'paid') return null;

  const paymentType = payment.payment_type || 'rent';
  const nextDueDate = nextMonthDueDate(payment.payment_day, payment.due_date);
  const amount = getAmountForType(payment, paymentType);

  return createPaymentDue({
    tenantId: payment.tenant_id,
    propertyId: payment.property_id,
    amount,
    dueDate: nextDueDate,
    paymentType,
    notes: paymentType === 'hygiene' ? 'Hygiene fee' : 'Monthly rent',
  });
}

/** When admin changes payment day, update pending/overdue due dates to match. */
export async function syncPendingDueDates(tenantId, paymentDay) {
  const day = clampPaymentDay(paymentDay);
  const pending = await db.prepare(`
    SELECT id, due_date, payment_type FROM payments
    WHERE tenant_id = ? AND status IN ('pending', 'overdue')
  `).all(tenantId);

  for (const pay of pending) {
    const [y, m] = pay.due_date.split('-').map(Number);
    const newDue = formatDate(y, m, day);
    if (newDue !== pay.due_date) {
      await db.prepare('UPDATE payments SET due_date = ?, status = ? WHERE id = ?')
        .run(newDue, 'pending', pay.id);
    }
  }
}
