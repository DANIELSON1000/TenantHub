import { Router } from 'express';

import db from '../database.js';

import { authenticate, requireRole } from '../middleware/auth.js';

import { processPaymentReminders } from '../services/reminders.js';

import { scheduleNextPayment, getAmountForType } from '../services/paymentScheduler.js';



const router = Router();



router.use(authenticate);



const paymentSelect = `

  SELECT pay.*, u.full_name as tenant_name, p.name as property_name, p.address,

         p.monthly_rent, p.hygiene_fee

  FROM payments pay

  JOIN tenants t ON pay.tenant_id = t.id

  JOIN users u ON t.user_id = u.id

  JOIN properties p ON pay.property_id = p.id

`;



async function updateOverduePayments() {

  await db.prepare(`

    UPDATE payments SET status = 'overdue'

    WHERE status = 'pending' AND due_date < CURRENT_DATE

  `).run();

}



router.get('/', async (req, res) => {

  try {

    await updateOverduePayments();

    const { type } = req.query;

    let typeFilter = '';

    const params = [];



    if (req.user.role === 'landlord') {

      params.push(req.user.id);

      let sql = `${paymentSelect} WHERE t.landlord_id = ?`;

      if (type && ['rent', 'hygiene'].includes(type)) {

        sql += ' AND pay.payment_type = ?';

        params.push(type);

      }

      sql += ' ORDER BY pay.due_date DESC';

      const payments = await db.prepare(sql).all(...params);

      return res.json(payments);

    }



    params.push(req.user.id);

    let sql = `${paymentSelect} WHERE t.user_id = ?`;

    if (type && ['rent', 'hygiene'].includes(type)) {

      sql += ' AND pay.payment_type = ?';

      params.push(type);

    }

    sql += ' ORDER BY pay.due_date DESC';

    const payments = await db.prepare(sql).all(...params);

    res.json(payments);

  } catch (err) {

    console.error(err);

    res.status(500).json({ error: 'Failed to fetch payments' });

  }

});



router.get('/analytics', async (req, res) => {

  try {

    await updateOverduePayments();

    let payments;

    if (req.user.role === 'landlord') {

      payments = await db.prepare(`${paymentSelect} WHERE t.landlord_id = ?`).all(req.user.id);

    } else {

      payments = await db.prepare(`${paymentSelect} WHERE t.user_id = ?`).all(req.user.id);

    }



    const totalDue = payments.reduce((s, p) => s + Number(p.amount), 0);

    const totalPaid = payments.filter(p => p.status === 'paid').reduce((s, p) => s + Number(p.amount), 0);

    const totalPending = payments.filter(p => p.status === 'pending').reduce((s, p) => s + Number(p.amount), 0);

    const totalOverdue = payments.filter(p => p.status === 'overdue').reduce((s, p) => s + Number(p.amount), 0);



    const rentPayments = payments.filter(p => (p.payment_type || 'rent') === 'rent');

    const hygienePayments = payments.filter(p => p.payment_type === 'hygiene');



    const byMonth = {};

    payments.forEach(p => {

      const month = String(p.due_date).slice(0, 7);

      if (!byMonth[month]) byMonth[month] = { due: 0, paid: 0, count: 0 };

      byMonth[month].due += Number(p.amount);

      byMonth[month].count++;

      if (p.status === 'paid') byMonth[month].paid += Number(p.amount);

    });



    const statusBreakdown = {

      paid: payments.filter(p => p.status === 'paid').length,

      pending: payments.filter(p => p.status === 'pending').length,

      overdue: payments.filter(p => p.status === 'overdue').length,

      partial: payments.filter(p => p.status === 'partial').length,

    };



    res.json({

      summary: {

        totalDue,

        totalPaid,

        totalPending,

        totalOverdue,

        collectionRate: totalDue > 0 ? Math.round((totalPaid / totalDue) * 100) : 0,

        paymentCount: payments.length,

        rentTotal: rentPayments.reduce((s, p) => s + Number(p.amount), 0),

        hygieneTotal: hygienePayments.reduce((s, p) => s + Number(p.amount), 0),

      },

      statusBreakdown,

      monthlyTrend: Object.entries(byMonth)

        .map(([month, data]) => ({ month, ...data }))

        .sort((a, b) => a.month.localeCompare(b.month)),

      recentPayments: payments.slice(0, 10),

    });

  } catch (err) {

    console.error(err);

    res.status(500).json({ error: 'Failed to fetch analytics' });

  }

});



router.post('/', requireRole('landlord'), async (req, res) => {

  try {

    const { tenant_id, amount, due_date, notes, payment_type } = req.body;

    const type = payment_type === 'hygiene' ? 'hygiene' : 'rent';

    if (!tenant_id || !due_date) {

      return res.status(400).json({ error: 'Tenant ID and due date are required' });

    }

    const tenant = await db.prepare('SELECT * FROM tenants WHERE id = ? AND landlord_id = ?').get(tenant_id, req.user.id);

    if (!tenant) return res.status(404).json({ error: 'Tenant not found' });



    const property = await db.prepare('SELECT * FROM properties WHERE id = ?').get(tenant.property_id);

    const finalAmount = amount ? Number(amount) : getAmountForType(property, type);

    if (!finalAmount || finalAmount <= 0) {

      return res.status(400).json({ error: type === 'hygiene' ? 'Hygiene fee is not set for this property' : 'Amount is required' });

    }



    const result = await db.prepare(

      'INSERT INTO payments (tenant_id, property_id, amount, due_date, payment_type, notes) VALUES (?, ?, ?, ?, ?, ?)'

    ).run(tenant_id, tenant.property_id, finalAmount, due_date, type, notes || null);



    const payment = await db.prepare(`${paymentSelect} WHERE pay.id = ?`).get(result.lastInsertRowid);

    processPaymentReminders().catch(console.error);

    res.status(201).json(payment);

  } catch (err) {

    console.error(err);

    res.status(500).json({ error: 'Failed to create payment' });

  }

});



router.patch('/:id/pay', async (req, res) => {

  try {

    const payment = await db.prepare(`

      SELECT pay.*, t.user_id, t.landlord_id

      FROM payments pay JOIN tenants t ON pay.tenant_id = t.id

      WHERE pay.id = ?

    `).get(req.params.id);

    if (!payment) return res.status(404).json({ error: 'Payment not found' });



    const canPay = req.user.role === 'landlord' && payment.landlord_id === req.user.id;

    const isTenant = req.user.role === 'tenant' && payment.user_id === req.user.id;

    if (!canPay && !isTenant) return res.status(403).json({ error: 'Access denied' });



    const { payment_method, notes } = req.body;

    await db.prepare(`

      UPDATE payments SET status = 'paid', paid_date = CURRENT_DATE, payment_method = ?, notes = COALESCE(?, notes)

      WHERE id = ?

    `).run(payment_method || 'manual', notes || null, req.params.id);



    await scheduleNextPayment(parseInt(req.params.id, 10));



    const updated = await db.prepare(`${paymentSelect} WHERE pay.id = ?`).get(req.params.id);

    res.json(updated);

  } catch (err) {

    console.error(err);

    res.status(500).json({ error: 'Failed to mark payment as paid' });

  }

});



export default router;


