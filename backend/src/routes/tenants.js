import { Router } from 'express';
import db from '../database.js';
import { authenticate, requireRole } from '../middleware/auth.js';
import { createInitialPayments, dayFromMoveIn, syncPendingDueDates } from '../services/paymentScheduler.js';

const router = Router();

router.use(authenticate);

const tenantSelect = `
  SELECT t.*, u.full_name, u.email, u.phone as user_phone,
         p.name as property_name, p.address as property_address, p.rooms, p.monthly_rent, p.hygiene_fee
  FROM tenants t
  JOIN users u ON t.user_id = u.id
  JOIN properties p ON t.property_id = p.id
`;

router.get('/', async (req, res) => {
  try {
    if (req.user.role === 'landlord') {
      const tenants = await db.prepare(`${tenantSelect} WHERE t.landlord_id = ? ORDER BY t.created_at DESC`).all(req.user.id);
      return res.json(tenants);
    }
    const tenant = await db.prepare(`${tenantSelect} WHERE t.user_id = ?`).get(req.user.id);
    res.json(tenant ? [tenant] : []);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to fetch tenants' });
  }
});

router.get('/users/available', requireRole('landlord'), async (req, res) => {
  try {
    const users = await db.prepare(`
      SELECT u.id, u.full_name, u.email, u.phone
      FROM users u
      WHERE u.role = 'tenant'
      AND u.id NOT IN (SELECT user_id FROM tenants)
      ORDER BY u.full_name
    `).all();
    res.json(users);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to fetch available users' });
  }
});

router.get('/:id', async (req, res) => {
  try {
    const tenant = await db.prepare(`${tenantSelect} WHERE t.id = ?`).get(req.params.id);
    if (!tenant) return res.status(404).json({ error: 'Tenant not found' });
    if (req.user.role === 'landlord' && tenant.landlord_id !== req.user.id) {
      return res.status(403).json({ error: 'Access denied' });
    }
    if (req.user.role === 'tenant' && tenant.user_id !== req.user.id) {
      return res.status(403).json({ error: 'Access denied' });
    }
    res.json(tenant);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to fetch tenant' });
  }
});

router.post('/', requireRole('landlord'), async (req, res) => {
  try {
    const { user_id, property_id, emergency_contact, emergency_phone, move_in_date, notes, status } = req.body;
    if (!user_id || !property_id || !move_in_date) {
      return res.status(400).json({ error: 'Tenant, property, and move-in date are required' });
    }
    const user = await db.prepare("SELECT id, role FROM users WHERE id = ? AND role = 'tenant'").get(user_id);
    if (!user) return res.status(400).json({ error: 'Valid tenant user not found' });
    const property = await db.prepare('SELECT * FROM properties WHERE id = ? AND landlord_id = ?').get(property_id, req.user.id);
    if (!property) return res.status(400).json({ error: 'Property not found' });

    const existing = await db.prepare('SELECT id FROM tenants WHERE user_id = ?').get(user_id);
    if (existing) return res.status(409).json({ error: 'User is already assigned as a tenant' });

    const day = dayFromMoveIn(move_in_date);

    const result = await db.prepare(`
      INSERT INTO tenants (user_id, property_id, landlord_id, emergency_contact, emergency_phone, move_in_date, status, notes, payment_day)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).run(user_id, property_id, req.user.id, emergency_contact || null, emergency_phone || null, move_in_date, status || 'active', notes || null, day);

    await createInitialPayments(result.lastInsertRowid, property, day);

    const tenant = await db.prepare(`${tenantSelect} WHERE t.id = ?`).get(result.lastInsertRowid);
    res.status(201).json(tenant);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to assign tenant' });
  }
});

router.put('/:id', async (req, res) => {
  try {
    const tenant = await db.prepare('SELECT * FROM tenants WHERE id = ?').get(req.params.id);
    if (!tenant) return res.status(404).json({ error: 'Tenant not found' });

    const isLandlord = req.user.role === 'landlord' && tenant.landlord_id === req.user.id;
    const isTenant = req.user.role === 'tenant' && tenant.user_id === req.user.id;
    if (!isLandlord && !isTenant) return res.status(403).json({ error: 'Access denied' });

    const { emergency_contact, emergency_phone, move_in_date, status, notes } = req.body;

    if (req.user.role === 'tenant') {
      await db.prepare('UPDATE tenants SET emergency_contact = ?, emergency_phone = ? WHERE id = ?')
        .run(emergency_contact ?? tenant.emergency_contact, emergency_phone ?? tenant.emergency_phone, req.params.id);
    } else {
      const finalMoveIn = move_in_date ?? tenant.move_in_date;
      const day = finalMoveIn ? dayFromMoveIn(finalMoveIn) : tenant.payment_day;
      await db.prepare(`
        UPDATE tenants SET emergency_contact = ?, emergency_phone = ?, move_in_date = ?, status = ?, notes = ?, payment_day = ?
        WHERE id = ?
      `).run(
        emergency_contact ?? tenant.emergency_contact,
        emergency_phone ?? tenant.emergency_phone,
        finalMoveIn,
        status ?? tenant.status,
        notes ?? tenant.notes,
        day,
        req.params.id
      );
      if (finalMoveIn && day !== tenant.payment_day) {
        await syncPendingDueDates(parseInt(req.params.id, 10), day);
      }
    }

    res.json(await db.prepare(`${tenantSelect} WHERE t.id = ?`).get(req.params.id));
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to update tenant' });
  }
});

export default router;
