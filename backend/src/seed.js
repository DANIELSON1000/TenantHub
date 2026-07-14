import bcrypt from 'bcryptjs';
import db, { initDb } from './database.js';

const ADMIN_EMAIL = 'admin@tenanthub.com';
const ADMIN_PASSWORD = 'admin123';

await initDb();

const hash = bcrypt.hashSync(ADMIN_PASSWORD, 10);

let adminUser = await db.prepare('SELECT id FROM users WHERE email = ?').get(ADMIN_EMAIL);

if (!adminUser) {
  const result = await db.prepare(
    "INSERT INTO users (email, password, full_name, phone, role) VALUES (?, ?, ?, ?, 'landlord')"
  ).run(ADMIN_EMAIL, hash, 'Admin Landlord', '+250 788 000 100');
  adminUser = { id: result.lastInsertRowid };
}

const propCount = await db.prepare('SELECT COUNT(*)::int AS count FROM properties WHERE landlord_id = ?').get(adminUser.id);

if (propCount.count === 0) {
  const sampleProperties = [
    { name: 'Kigali Studio', address: 'KN 5 Rd, Nyarugenge, Kigali', unit: 'A1', rooms: 1, rent: 120000, description: 'Compact studio — ideal for one person' },
    { name: 'Remera Apartment', address: 'KG 11 Ave, Remera, Kigali', unit: '12B', rooms: 2, rent: 250000, description: '2-bedroom apartment near amenities' },
    { name: 'Kacyiru Family House', address: 'KG 7 Ave, Kacyiru, Kigali', unit: null, rooms: 3, rent: 450000, description: '3-bedroom house with parking' },
    { name: 'Niboye Villa', address: 'KK 15 Rd, Niboye, Kigali', unit: null, rooms: 4, rent: 650000, description: 'Large 4-bedroom villa with garden' },
  ];

  for (const p of sampleProperties) {
    await db.prepare(`
      INSERT INTO properties (landlord_id, name, address, unit, rooms, monthly_rent, description)
      VALUES (?, ?, ?, ?, ?, ?, ?)
    `).run(adminUser.id, p.name, p.address, p.unit, p.rooms, p.rent, p.description);
  }
}

console.log('Neon database seeded successfully!');
console.log('');
console.log('Admin (Landlord) account — system credentials only:');
console.log(`  Email:    ${ADMIN_EMAIL}`);
console.log(`  Password: ${ADMIN_PASSWORD}`);
console.log('');
console.log('Sample properties use Rwandan Francs (RWF) with different room sizes.');
console.log('Tenants must register themselves via the Sign up page.');

process.exit(0);
