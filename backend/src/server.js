import express from 'express';
import cors from 'cors';
import { initDb } from './database.js';
import authRoutes from './routes/auth.js';
import propertyRoutes from './routes/properties.js';
import tenantRoutes from './routes/tenants.js';
import messageRoutes from './routes/messages.js';
import agreementRoutes from './routes/agreements.js';
import paymentRoutes from './routes/payments.js';
import dashboardRoutes from './routes/dashboard.js';
import notificationRoutes from './routes/notifications.js';
import { processPaymentReminders } from './services/reminders.js';

const app = express();
const PORT = process.env.PORT || 3001;

app.use(cors());
app.use(express.json());

app.use('/api/auth', authRoutes);
app.use('/api/properties', propertyRoutes);
app.use('/api/tenants', tenantRoutes);
app.use('/api/messages', messageRoutes);
app.use('/api/agreements', agreementRoutes);
app.use('/api/payments', paymentRoutes);
app.use('/api/dashboard', dashboardRoutes);
app.use('/api/notifications', notificationRoutes);

app.get('/api/health', (_, res) => res.json({ status: 'ok', service: 'TenantHub API', database: 'neon-postgresql' }));

await initDb();
await processPaymentReminders();
setInterval(() => processPaymentReminders().catch(console.error), 60 * 60 * 1000);

app.listen(PORT, '0.0.0.0', () => {
  console.log(`TenantHub API running on http://localhost:${PORT}`);
  console.log(`Phone access: use your PC IP address with port ${PORT} when deployed`);
});
