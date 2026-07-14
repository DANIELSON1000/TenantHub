import { Router } from 'express';
import db from '../database.js';
import { authenticate, requireRole } from '../middleware/auth.js';

const router = Router();

router.use(authenticate);

router.get('/', async (req, res) => {
  try {
    const messages = await db.prepare(`
      SELECT m.*, s.full_name as sender_name, s.role as sender_role, r.full_name as receiver_name
      FROM messages m
      JOIN users s ON m.sender_id = s.id
      JOIN users r ON m.receiver_id = r.id
      WHERE m.sender_id = ? OR m.receiver_id = ?
      ORDER BY m.created_at DESC
    `).all(req.user.id, req.user.id);
    res.json(messages);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to fetch messages' });
  }
});

router.get('/unread-count', async (req, res) => {
  try {
    const result = await db.prepare('SELECT COUNT(*)::int AS count FROM messages WHERE receiver_id = ? AND is_read = FALSE').get(req.user.id);
    res.json({ count: result.count });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to fetch unread count' });
  }
});

router.get('/conversation/:userId', async (req, res) => {
  try {
    const otherId = parseInt(req.params.userId, 10);
    const messages = await db.prepare(`
      SELECT m.*, s.full_name as sender_name, s.role as sender_role, r.full_name as receiver_name
      FROM messages m
      JOIN users s ON m.sender_id = s.id
      JOIN users r ON m.receiver_id = r.id
      WHERE (m.sender_id = ? AND m.receiver_id = ?) OR (m.sender_id = ? AND m.receiver_id = ?)
      ORDER BY m.created_at ASC
    `).all(req.user.id, otherId, otherId, req.user.id);

    await db.prepare('UPDATE messages SET is_read = TRUE WHERE receiver_id = ? AND sender_id = ?').run(req.user.id, otherId);
    res.json(messages);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to fetch conversation' });
  }
});

router.get('/contacts', async (req, res) => {
  try {
    if (req.user.role === 'landlord') {
      const contacts = await db.prepare(`
        SELECT DISTINCT u.id, u.full_name, u.email, u.role,
          (SELECT COUNT(*)::int FROM messages WHERE receiver_id = ? AND sender_id = u.id AND is_read = FALSE) as unread
        FROM users u
        JOIN tenants t ON t.user_id = u.id
        WHERE t.landlord_id = ?
      `).all(req.user.id, req.user.id);
      return res.json(contacts);
    }
    const tenant = await db.prepare('SELECT landlord_id FROM tenants WHERE user_id = ?').get(req.user.id);
    if (!tenant) return res.json([]);
    const landlord = await db.prepare(`
      SELECT u.id, u.full_name, u.email, u.role,
        (SELECT COUNT(*)::int FROM messages WHERE receiver_id = ? AND sender_id = u.id AND is_read = FALSE) as unread
      FROM users u WHERE u.id = ?
    `).get(req.user.id, tenant.landlord_id);
    res.json(landlord ? [landlord] : []);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to fetch contacts' });
  }
});

router.post('/broadcast', requireRole('landlord'), async (req, res) => {
  try {
    const { subject, body, property_id, user_ids } = req.body;
    if (!body?.trim()) {
      return res.status(400).json({ error: 'Message body is required' });
    }

    let recipients;
    if (user_ids?.length) {
      const placeholders = user_ids.map(() => '?').join(',');
      recipients = await db.prepare(`
        SELECT DISTINCT t.user_id, t.property_id
        FROM tenants t
        WHERE t.landlord_id = ? AND t.status = 'active' AND t.user_id IN (${placeholders})
      `).all(req.user.id, ...user_ids);
    } else if (property_id) {
      recipients = await db.prepare(`
        SELECT DISTINCT t.user_id, t.property_id
        FROM tenants t
        WHERE t.landlord_id = ? AND t.status = 'active' AND t.property_id = ?
      `).all(req.user.id, property_id);
    } else {
      recipients = await db.prepare(`
        SELECT DISTINCT t.user_id, t.property_id
        FROM tenants t
        WHERE t.landlord_id = ? AND t.status = 'active'
      `).all(req.user.id);
    }

    if (recipients.length === 0) {
      return res.status(400).json({ error: 'No tenants found to message' });
    }

    const msgSubject = subject?.trim() || 'Announcement';
    let sent = 0;
    for (const r of recipients) {
      await db.prepare(
        'INSERT INTO messages (sender_id, receiver_id, property_id, subject, body) VALUES (?, ?, ?, ?, ?)'
      ).run(req.user.id, r.user_id, r.property_id || property_id || null, msgSubject, body.trim());
      sent++;
    }

    res.status(201).json({ sent, subject: msgSubject });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to send broadcast message' });
  }
});

router.post('/', async (req, res) => {
  try {
    const { receiver_id, subject, body, property_id } = req.body;
    if (!receiver_id || !subject || !body) {
      return res.status(400).json({ error: 'Receiver, subject, and body are required' });
    }
    const receiver = await db.prepare('SELECT id FROM users WHERE id = ?').get(receiver_id);
    if (!receiver) return res.status(400).json({ error: 'Receiver not found' });

    const result = await db.prepare(
      'INSERT INTO messages (sender_id, receiver_id, property_id, subject, body) VALUES (?, ?, ?, ?, ?)'
    ).run(req.user.id, receiver_id, property_id || null, subject, body);

    const message = await db.prepare(`
      SELECT m.*, s.full_name as sender_name, s.role as sender_role, r.full_name as receiver_name
      FROM messages m
      JOIN users s ON m.sender_id = s.id
      JOIN users r ON m.receiver_id = r.id
      WHERE m.id = ?
    `).get(result.lastInsertRowid);
    res.status(201).json(message);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to send message' });
  }
});

export default router;
