import { Router } from 'express';
import db from '../database.js';
import { authenticate } from '../middleware/auth.js';

const router = Router();
router.use(authenticate);

router.get('/', async (req, res) => {
  try {
    const notifications = await db.prepare(`
      SELECT * FROM notifications
      WHERE user_id = ?
      ORDER BY created_at DESC
      LIMIT 50
    `).all(req.user.id);
    res.json(notifications.map((n) => ({
      ...n,
      data: typeof n.data === 'string' ? JSON.parse(n.data) : n.data,
    })));
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to fetch notifications' });
  }
});

router.get('/unread-count', async (req, res) => {
  try {
    const result = await db.prepare(
      'SELECT COUNT(*)::int AS count FROM notifications WHERE user_id = ? AND is_read = FALSE'
    ).get(req.user.id);
    res.json({ count: result.count });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to fetch count' });
  }
});

router.patch('/read-all', async (req, res) => {
  try {
    await db.prepare('UPDATE notifications SET is_read = TRUE WHERE user_id = ?').run(req.user.id);
    res.json({ message: 'All marked as read' });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to update notifications' });
  }
});

router.patch('/:id/read', async (req, res) => {
  try {
    const notif = await db.prepare('SELECT * FROM notifications WHERE id = ? AND user_id = ?').get(req.params.id, req.user.id);
    if (!notif) return res.status(404).json({ error: 'Notification not found' });
    await db.prepare('UPDATE notifications SET is_read = TRUE WHERE id = ?').run(req.params.id);
    res.json({ message: 'Marked as read' });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to update notification' });
  }
});

export default router;
