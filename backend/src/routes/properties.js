import { Router } from 'express';
import db from '../database.js';
import { authenticate, requireRole } from '../middleware/auth.js';

const router = Router();

router.use(authenticate);

router.get('/', async (req, res) => {
  try {
    if (req.user.role === 'landlord') {
      const properties = await db.prepare('SELECT * FROM properties WHERE landlord_id = ? ORDER BY rooms ASC, monthly_rent ASC').all(req.user.id);
      return res.json(properties);
    }
    const tenant = await db.prepare('SELECT property_id FROM tenants WHERE user_id = ?').get(req.user.id);
    if (!tenant) return res.json([]);
    const property = await db.prepare('SELECT * FROM properties WHERE id = ?').get(tenant.property_id);
    res.json(property ? [property] : []);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to fetch properties' });
  }
});

router.get('/:id', async (req, res) => {
  try {
    const property = await db.prepare('SELECT * FROM properties WHERE id = ?').get(req.params.id);
    if (!property) return res.status(404).json({ error: 'Property not found' });
    if (req.user.role === 'landlord' && property.landlord_id !== req.user.id) {
      return res.status(403).json({ error: 'Access denied' });
    }
    if (req.user.role === 'tenant') {
      const tenant = await db.prepare('SELECT id FROM tenants WHERE user_id = ? AND property_id = ?').get(req.user.id, property.id);
      if (!tenant) return res.status(403).json({ error: 'Access denied' });
    }
    res.json(property);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to fetch property' });
  }
});

router.post('/', requireRole('landlord'), async (req, res) => {
  try {
    const { name, address, unit, rooms, monthly_rent, hygiene_fee, description } = req.body;
    if (!name || !address || !monthly_rent || !rooms) {
      return res.status(400).json({ error: 'Name, address, number of rooms, and monthly rent are required' });
    }
    if (rooms < 1) {
      return res.status(400).json({ error: 'Rooms must be at least 1' });
    }
    const result = await db.prepare(
      'INSERT INTO properties (landlord_id, name, address, unit, rooms, monthly_rent, hygiene_fee, description) VALUES (?, ?, ?, ?, ?, ?, ?, ?)'
    ).run(req.user.id, name, address, unit || null, rooms, monthly_rent, hygiene_fee || 0, description || null);
    const property = await db.prepare('SELECT * FROM properties WHERE id = ?').get(result.lastInsertRowid);
    res.status(201).json(property);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to create property' });
  }
});

router.put('/:id', requireRole('landlord'), async (req, res) => {
  try {
    const property = await db.prepare('SELECT * FROM properties WHERE id = ?').get(req.params.id);
    if (!property) return res.status(404).json({ error: 'Property not found' });
    if (property.landlord_id !== req.user.id) return res.status(403).json({ error: 'Access denied' });

    const { name, address, unit, rooms, monthly_rent, hygiene_fee, description } = req.body;
    await db.prepare(
      'UPDATE properties SET name = ?, address = ?, unit = ?, rooms = ?, monthly_rent = ?, hygiene_fee = ?, description = ? WHERE id = ?'
    ).run(
      name ?? property.name,
      address ?? property.address,
      unit ?? property.unit,
      rooms ?? property.rooms,
      monthly_rent ?? property.monthly_rent,
      hygiene_fee ?? property.hygiene_fee ?? 0,
      description ?? property.description,
      req.params.id
    );
    res.json(await db.prepare('SELECT * FROM properties WHERE id = ?').get(req.params.id));
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to update property' });
  }
});

router.delete('/:id', requireRole('landlord'), async (req, res) => {
  try {
    const property = await db.prepare('SELECT * FROM properties WHERE id = ?').get(req.params.id);
    if (!property) return res.status(404).json({ error: 'Property not found' });
    if (property.landlord_id !== req.user.id) return res.status(403).json({ error: 'Access denied' });
    await db.prepare('DELETE FROM properties WHERE id = ?').run(req.params.id);
    res.json({ message: 'Property deleted' });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to delete property' });
  }
});

export default router;
