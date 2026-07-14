import pg from 'pg';
import dotenv from 'dotenv';

dotenv.config();

const { Pool } = pg;

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.DATABASE_URL?.includes('localhost') ? false : { rejectUnauthorized: false },
});

function toPgSql(sql) {
  let i = 0;
  return sql.replace(/\?/g, () => `$${++i}`);
}

function appendReturningId(sql) {
  const trimmed = sql.trim();
  if (/^INSERT/i.test(trimmed) && !/RETURNING/i.test(trimmed)) {
    return trimmed.replace(/;?\s*$/, ' RETURNING id');
  }
  return trimmed;
}

const db = {
  prepare(sql) {
    const pgSql = toPgSql(sql);
    return {
      async get(...params) {
        const { rows } = await pool.query(pgSql, params);
        return rows[0];
      },
      async all(...params) {
        const { rows } = await pool.query(pgSql, params);
        return rows;
      },
      async run(...params) {
        const finalSql = toPgSql(appendReturningId(sql));
        const { rows, rowCount } = await pool.query(finalSql, params);
        return { lastInsertRowid: rows[0]?.id, changes: rowCount };
      },
    };
  },
  async exec(sql) {
    await pool.query(sql);
  },
};

export async function initDb() {
  await pool.query(`
    CREATE TABLE IF NOT EXISTS users (
      id SERIAL PRIMARY KEY,
      email TEXT UNIQUE NOT NULL,
      password TEXT NOT NULL,
      full_name TEXT NOT NULL,
      phone TEXT,
      role TEXT NOT NULL CHECK(role IN ('landlord', 'tenant')),
      created_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS properties (
      id SERIAL PRIMARY KEY,
      landlord_id INTEGER NOT NULL REFERENCES users(id),
      name TEXT NOT NULL,
      address TEXT NOT NULL,
      unit TEXT,
      rooms INTEGER NOT NULL DEFAULT 1,
      monthly_rent NUMERIC(12,0) NOT NULL,
      description TEXT,
      created_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS tenants (
      id SERIAL PRIMARY KEY,
      user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
      property_id INTEGER NOT NULL REFERENCES properties(id),
      landlord_id INTEGER NOT NULL REFERENCES users(id),
      emergency_contact TEXT,
      emergency_phone TEXT,
      move_in_date DATE,
      lease_start DATE,
      lease_end DATE,
      status TEXT DEFAULT 'active' CHECK(status IN ('active', 'inactive', 'pending')),
      notes TEXT,
      created_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS messages (
      id SERIAL PRIMARY KEY,
      sender_id INTEGER NOT NULL REFERENCES users(id),
      receiver_id INTEGER NOT NULL REFERENCES users(id),
      property_id INTEGER REFERENCES properties(id),
      subject TEXT NOT NULL,
      body TEXT NOT NULL,
      is_read BOOLEAN DEFAULT FALSE,
      created_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS agreements (
      id SERIAL PRIMARY KEY,
      tenant_id INTEGER NOT NULL REFERENCES tenants(id),
      property_id INTEGER NOT NULL REFERENCES properties(id),
      landlord_id INTEGER NOT NULL REFERENCES users(id),
      title TEXT NOT NULL,
      content TEXT NOT NULL,
      status TEXT DEFAULT 'draft' CHECK(status IN ('draft', 'sent', 'signed')),
      signed_at TIMESTAMPTZ,
      created_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS payments (
      id SERIAL PRIMARY KEY,
      tenant_id INTEGER NOT NULL REFERENCES tenants(id),
      property_id INTEGER NOT NULL REFERENCES properties(id),
      amount NUMERIC(12,0) NOT NULL,
      due_date DATE NOT NULL,
      paid_date DATE,
      status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'paid', 'overdue', 'partial')),
      payment_method TEXT,
      notes TEXT,
      created_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS notifications (
      id SERIAL PRIMARY KEY,
      user_id INTEGER NOT NULL REFERENCES users(id),
      type TEXT NOT NULL,
      title_en TEXT NOT NULL,
      title_rw TEXT NOT NULL,
      message_en TEXT NOT NULL,
      message_rw TEXT NOT NULL,
      data JSONB,
      is_read BOOLEAN DEFAULT FALSE,
      email_sent BOOLEAN DEFAULT FALSE,
      created_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS payment_reminder_log (
      payment_id INTEGER NOT NULL REFERENCES payments(id),
      reminder_key TEXT NOT NULL,
      email_sent BOOLEAN DEFAULT FALSE,
      created_at TIMESTAMPTZ DEFAULT NOW(),
      PRIMARY KEY (payment_id, reminder_key)
    );

    CREATE TABLE IF NOT EXISTS password_reset_tokens (
      id SERIAL PRIMARY KEY,
      user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      token_hash TEXT NOT NULL UNIQUE,
      expires_at TIMESTAMPTZ NOT NULL,
      created_at TIMESTAMPTZ DEFAULT NOW()
    );
  `);

  // Migrations for existing databases
  await pool.query(`ALTER TABLE properties ADD COLUMN IF NOT EXISTS rooms INTEGER NOT NULL DEFAULT 1`);
  await pool.query(`ALTER TABLE properties ADD COLUMN IF NOT EXISTS hygiene_fee NUMERIC(12,0) NOT NULL DEFAULT 0`);
  await pool.query(`ALTER TABLE payments ADD COLUMN IF NOT EXISTS payment_type TEXT NOT NULL DEFAULT 'rent'`);
  await pool.query(`ALTER TABLE tenants ADD COLUMN IF NOT EXISTS payment_day INTEGER NOT NULL DEFAULT 1`);
  await pool.query(`ALTER TABLE properties ALTER COLUMN monthly_rent TYPE NUMERIC(12,0)`).catch(() => {});
  await pool.query(`ALTER TABLE payments ALTER COLUMN amount TYPE NUMERIC(12,0)`).catch(() => {});

  console.log('Connected to Neon PostgreSQL');
}

export default db;
