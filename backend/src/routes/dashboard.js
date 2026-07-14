import { Router } from 'express';
import db from '../database.js';
import { authenticate } from '../middleware/auth.js';

const router = Router();

router.use(authenticate);

router.get('/', async (req, res) => {
  try {
    if (req.user.role === 'landlord') {
      const tenants = await db.prepare("SELECT COUNT(*)::int AS count FROM tenants WHERE landlord_id = ? AND status = 'active'").get(req.user.id);
      const properties = await db.prepare('SELECT COUNT(*)::int AS count FROM properties WHERE landlord_id = ?').get(req.user.id);
      const unread = await db.prepare('SELECT COUNT(*)::int AS count FROM messages WHERE receiver_id = ? AND is_read = FALSE').get(req.user.id);
      const overdue = await db.prepare(`
        SELECT COUNT(*)::int AS count FROM payments pay
        JOIN tenants t ON pay.tenant_id = t.id
        WHERE t.landlord_id = ? AND pay.status = 'overdue'
      `).get(req.user.id);
      const pendingPayments = await db.prepare(`
        SELECT COUNT(*)::int AS count FROM payments pay
        JOIN tenants t ON pay.tenant_id = t.id
        WHERE t.landlord_id = ? AND pay.status = 'pending'
      `).get(req.user.id);
      const monthlyRevenue = await db.prepare(`
        SELECT COALESCE(SUM(pay.amount), 0)::float AS total FROM payments pay
        JOIN tenants t ON pay.tenant_id = t.id
        WHERE t.landlord_id = ? AND pay.status = 'paid'
        AND TO_CHAR(pay.paid_date, 'YYYY-MM') = TO_CHAR(CURRENT_DATE, 'YYYY-MM')
      `).get(req.user.id);

      return res.json({
        role: 'landlord',
        stats: {
          activeTenants: tenants.count,
          properties: properties.count,
          unreadMessages: unread.count,
          overduePayments: overdue.count,
          pendingPayments: pendingPayments.count,
          monthlyRevenue: monthlyRevenue.total,
        },
      });
    }

    const tenant = await db.prepare(`
      SELECT t.*, p.name as property_name, p.address, p.rooms, p.monthly_rent,
             l.full_name as landlord_name, l.email as landlord_email
      FROM tenants t
      JOIN properties p ON t.property_id = p.id
      JOIN users l ON t.landlord_id = l.id
      WHERE t.user_id = ?
    `).get(req.user.id);

    if (!tenant) {
      return res.json({ role: 'tenant', stats: null, message: 'No property assigned yet' });
    }

    const unread = await db.prepare('SELECT COUNT(*)::int AS count FROM messages WHERE receiver_id = ? AND is_read = FALSE').get(req.user.id);
    const nextPayment = await db.prepare(`
      SELECT * FROM payments WHERE tenant_id = ? AND status IN ('pending', 'overdue')
      ORDER BY due_date ASC LIMIT 1
    `).get(tenant.id);
    const paidThisYear = await db.prepare(`
      SELECT COALESCE(SUM(amount), 0)::float AS total FROM payments
      WHERE tenant_id = ? AND status = 'paid' AND TO_CHAR(paid_date, 'YYYY') = TO_CHAR(CURRENT_DATE, 'YYYY')
    `).get(tenant.id);

    res.json({
      role: 'tenant',
      tenant,
      stats: {
        unreadMessages: unread.count,
        nextPayment,
        paidThisYear: paidThisYear.total,
        monthlyRent: tenant.monthly_rent,
      },
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to fetch dashboard' });
  }
});

export default router;
