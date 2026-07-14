import { Router } from 'express';
import PDFDocument from 'pdfkit';
import db from '../database.js';
import { authenticate, requireRole } from '../middleware/auth.js';

const router = Router();

router.use(authenticate);

function formatRwf(amount) {
  return `${new Intl.NumberFormat('en-RW').format(Number(amount) || 0)} Frw`;
}

function buildAgreementContent(tenant, property, landlord, terms) {
  const today = new Date().toLocaleDateString('en-RW', { year: 'numeric', month: 'long', day: 'numeric' });
  const rent = formatRwf(property.monthly_rent);
  const roomLabel = property.rooms === 1 ? '1 room' : `${property.rooms} rooms`;
  return `
RESIDENTIAL LEASE AGREEMENT

Date: ${today}

PARTIES
-------
Landlord: ${landlord.full_name}
Email: ${landlord.email}
Phone: ${landlord.phone || 'N/A'}

Tenant: ${tenant.full_name}
Email: ${tenant.email}
Phone: ${tenant.user_phone || tenant.phone || 'N/A'}

PROPERTY
--------
Property: ${property.name}
Address: ${property.address}${property.unit ? ', Unit ' + property.unit : ''}
Size: ${roomLabel}

LEASE TERMS
-----------
Monthly Rent: ${rent}
Lease Start: ${tenant.lease_start || 'To be determined'}
Lease End: ${tenant.lease_end || 'To be determined'}
Move-in Date: ${tenant.move_in_date || 'To be determined'}

ADDITIONAL TERMS
----------------
${terms || 'Standard terms and conditions apply. Tenant agrees to maintain the property in good condition and pay rent on time.'}

SIGNATURES
----------
Landlord Signature: _________________________ Date: ___________
Tenant Signature: _________________________ Date: ___________
`.trim();
}

router.get('/', async (req, res) => {
  try {
    if (req.user.role === 'landlord') {
      const agreements = await db.prepare(`
        SELECT a.*, u.full_name as tenant_name, p.name as property_name
        FROM agreements a
        JOIN tenants t ON a.tenant_id = t.id
        JOIN users u ON t.user_id = u.id
        JOIN properties p ON a.property_id = p.id
        WHERE a.landlord_id = ?
        ORDER BY a.created_at DESC
      `).all(req.user.id);
      return res.json(agreements);
    }
    const agreements = await db.prepare(`
      SELECT a.*, u.full_name as tenant_name, p.name as property_name
      FROM agreements a
      JOIN tenants t ON a.tenant_id = t.id
      JOIN users u ON t.user_id = u.id
      JOIN properties p ON a.property_id = p.id
      WHERE t.user_id = ?
      ORDER BY a.created_at DESC
    `).all(req.user.id);
    res.json(agreements);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to fetch agreements' });
  }
});

router.get('/:id/pdf', async (req, res) => {
  try {
    const agreement = await db.prepare(`
      SELECT a.*, t.user_id as tenant_user_id
      FROM agreements a JOIN tenants t ON a.tenant_id = t.id
      WHERE a.id = ?
    `).get(req.params.id);
    if (!agreement) return res.status(404).json({ error: 'Agreement not found' });

    const canAccess =
      (req.user.role === 'landlord' && agreement.landlord_id === req.user.id) ||
      (req.user.role === 'tenant' && agreement.tenant_user_id === req.user.id);
    if (!canAccess) return res.status(403).json({ error: 'Access denied' });

    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', `attachment; filename="agreement-${agreement.id}.pdf"`);

    const doc = new PDFDocument({ margin: 50 });
    doc.pipe(res);
    doc.fontSize(16).text(agreement.title, { align: 'center' });
    doc.moveDown();
    doc.fontSize(10).text(agreement.content, { align: 'left' });
    doc.end();
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to generate PDF' });
  }
});

router.get('/:id', async (req, res) => {
  try {
    const agreement = await db.prepare(`
      SELECT a.*, u.full_name as tenant_name, p.name as property_name
      FROM agreements a
      JOIN tenants t ON a.tenant_id = t.id
      JOIN users u ON t.user_id = u.id
      JOIN properties p ON a.property_id = p.id
      WHERE a.id = ?
    `).get(req.params.id);
    if (!agreement) return res.status(404).json({ error: 'Agreement not found' });
    res.json(agreement);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to fetch agreement' });
  }
});

router.post('/', requireRole('landlord'), async (req, res) => {
  try {
    const { tenant_id, title, terms } = req.body;
    if (!tenant_id) return res.status(400).json({ error: 'Tenant ID is required' });

    const tenant = await db.prepare(`
      SELECT t.*, u.full_name, u.email, u.phone as user_phone
      FROM tenants t JOIN users u ON t.user_id = u.id
      WHERE t.id = ? AND t.landlord_id = ?
    `).get(tenant_id, req.user.id);
    if (!tenant) return res.status(404).json({ error: 'Tenant not found' });

    const property = await db.prepare('SELECT * FROM properties WHERE id = ?').get(tenant.property_id);
    const landlord = await db.prepare('SELECT * FROM users WHERE id = ?').get(req.user.id);
    const content = buildAgreementContent(tenant, property, landlord, terms);

    const result = await db.prepare(
      'INSERT INTO agreements (tenant_id, property_id, landlord_id, title, content, status) VALUES (?, ?, ?, ?, ?, ?)'
    ).run(tenant_id, tenant.property_id, req.user.id, title || 'Residential Lease Agreement', content, 'sent');

    const agreement = await db.prepare('SELECT * FROM agreements WHERE id = ?').get(result.lastInsertRowid);
    res.status(201).json(agreement);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to create agreement' });
  }
});

router.patch('/:id/sign', async (req, res) => {
  try {
    const agreement = await db.prepare(`
      SELECT a.*, t.user_id as tenant_user_id
      FROM agreements a JOIN tenants t ON a.tenant_id = t.id
      WHERE a.id = ?
    `).get(req.params.id);
    if (!agreement) return res.status(404).json({ error: 'Agreement not found' });

    const canSign =
      (req.user.role === 'tenant' && agreement.tenant_user_id === req.user.id) ||
      (req.user.role === 'landlord' && agreement.landlord_id === req.user.id);
    if (!canSign) return res.status(403).json({ error: 'Access denied' });

    await db.prepare("UPDATE agreements SET status = 'signed', signed_at = NOW() WHERE id = ?").run(req.params.id);
    res.json(await db.prepare('SELECT * FROM agreements WHERE id = ?').get(req.params.id));
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to sign agreement' });
  }
});

export default router;
