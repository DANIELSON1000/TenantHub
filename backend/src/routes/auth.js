import { Router } from 'express';
import crypto from 'crypto';
import bcrypt from 'bcryptjs';
import db from '../database.js';
import { generateToken, authenticate } from '../middleware/auth.js';
import { sendEmail } from '../services/email.js';

const router = Router();

const RESET_EXPIRY_MS = 60 * 60 * 1000; // 1 hour

function hashToken(token) {
  return crypto.createHash('sha256').update(token).digest('hex');
}

function getResetUrl(token) {
  const base = process.env.FRONTEND_URL || 'http://localhost:5173';
  return `${base.replace(/\/$/, '')}/reset-password?token=${token}`;
}

router.post('/register', async (req, res) => {
  try {
    const { email, password, full_name, phone } = req.body;
    if (!email || !password || !full_name) {
      return res.status(400).json({ error: 'Email, password, and full name are required' });
    }
    if (password.length < 6) {
      return res.status(400).json({ error: 'Password must be at least 6 characters' });
    }
    const existing = await db.prepare('SELECT id FROM users WHERE email = ?').get(email);
    if (existing) {
      return res.status(409).json({ error: 'Email already registered' });
    }
    const hash = bcrypt.hashSync(password, 10);
    const result = await db.prepare(
      "INSERT INTO users (email, password, full_name, phone, role) VALUES (?, ?, ?, ?, 'tenant')"
    ).run(email, hash, full_name, phone || null);
    const user = await db.prepare('SELECT id, email, full_name, phone, role FROM users WHERE id = ?').get(result.lastInsertRowid);
    res.status(201).json({ user, token: generateToken(user) });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Registration failed' });
  }
});

router.post('/login', async (req, res) => {
  try {
    const { email, password } = req.body;
    if (!email || !password) {
      return res.status(400).json({ error: 'Email and password are required' });
    }
    const user = await db.prepare('SELECT * FROM users WHERE email = ?').get(email);
    if (!user || !bcrypt.compareSync(password, user.password)) {
      return res.status(401).json({ error: 'Invalid email or password' });
    }
    const { password: _, ...safeUser } = user;
    res.json({ user: safeUser, token: generateToken(safeUser) });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Login failed' });
  }
});

router.post('/forgot-password', async (req, res) => {
  try {
    const { email } = req.body;
    if (!email) {
      return res.status(400).json({ error: 'Email is required' });
    }

    const user = await db.prepare('SELECT id, email, full_name, role FROM users WHERE email = ?').get(email);

    if (user) {
      await db.prepare('DELETE FROM password_reset_tokens WHERE user_id = ?').run(user.id);

      const token = crypto.randomBytes(32).toString('hex');
      const tokenHash = hashToken(token);
      const expiresAt = new Date(Date.now() + RESET_EXPIRY_MS).toISOString();

      await db.prepare(
        'INSERT INTO password_reset_tokens (user_id, token_hash, expires_at) VALUES (?, ?, ?)'
      ).run(user.id, tokenHash, expiresAt);

      const resetUrl = getResetUrl(token);
      const name = user.full_name?.split(' ')[0] || 'there';

      await sendEmail({
        to: user.email,
        subject: '[TenantHub] Reset your password',
        text: `Hi ${name},\n\nWe received a request to reset your TenantHub password.\n\nClick this link to choose a new password (valid for 1 hour):\n${resetUrl}\n\nIf you did not request this, you can ignore this email.\n\n— TenantHub\n\nMuraho ${name},\n\nTwakiriye ubusabe bwo guhindura ijambo ry'ibanga rya TenantHub.\n\nKanda aha kugira ngo uhitemo ijambo rishya (rikora mu isaha 1):\n${resetUrl}`,
        html: `
          <div style="font-family:sans-serif;max-width:520px;margin:0 auto;padding:24px">
            <h2 style="color:#006fc7">TenantHub — Password Reset</h2>
            <p style="color:#334155">Hi ${name},</p>
            <p style="color:#334155">We received a request to reset your password. Click the button below to choose a new one. This link expires in <strong>1 hour</strong>.</p>
            <p style="margin:24px 0">
              <a href="${resetUrl}" style="display:inline-block;background:#006fc7;color:#fff;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:600">Reset Password</a>
            </p>
            <p style="color:#64748b;font-size:13px">If you didn't request this, you can safely ignore this email.</p>
            <hr style="border:none;border-top:1px solid #e2e8f0;margin:20px 0" />
            <p style="color:#64748b;font-size:14px">Muraho ${name}, kanda buto hejuru kugira ngo uhindure ijambo ry'ibanga. Ihuza rirangira mu isaha 1.</p>
          </div>
        `,
      });
    }

    res.json({
      message: 'If an account exists with that email, we sent password reset instructions.',
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to process password reset request' });
  }
});

router.post('/reset-password', async (req, res) => {
  try {
    const { token, password } = req.body;
    if (!token || !password) {
      return res.status(400).json({ error: 'Token and new password are required' });
    }
    if (password.length < 6) {
      return res.status(400).json({ error: 'Password must be at least 6 characters' });
    }

    const tokenHash = hashToken(token);
    const record = await db.prepare(`
      SELECT prt.*, u.email, u.full_name
      FROM password_reset_tokens prt
      JOIN users u ON prt.user_id = u.id
      WHERE prt.token_hash = ?
    `).get(tokenHash);

    if (!record) {
      return res.status(400).json({ error: 'Invalid or expired reset link. Please request a new one.' });
    }

    if (new Date(record.expires_at) < new Date()) {
      await db.prepare('DELETE FROM password_reset_tokens WHERE id = ?').run(record.id);
      return res.status(400).json({ error: 'This reset link has expired. Please request a new one.' });
    }

    const hash = bcrypt.hashSync(password, 10);
    await db.prepare('UPDATE users SET password = ? WHERE id = ?').run(hash, record.user_id);
    await db.prepare('DELETE FROM password_reset_tokens WHERE user_id = ?').run(record.user_id);

    res.json({ message: 'Password updated successfully. You can now sign in.' });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to reset password' });
  }
});

router.get('/me', authenticate, async (req, res) => {
  try {
    const user = await db.prepare('SELECT id, email, full_name, phone, role, created_at FROM users WHERE id = ?').get(req.user.id);
    if (!user) return res.status(404).json({ error: 'User not found' });
    res.json(user);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to fetch user' });
  }
});

export default router;
