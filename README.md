# TenantHub — Landlord & Tenant Management System

A full-stack web application for landlords to manage tenants, properties, communications, lease agreements, and rent payments.

## Features

| Module | Description |
|--------|-------------|
| **Tenant Management** | Store and update tenant information (contact details, emergency contacts, lease dates) |
| **Properties** | Landlords can add, edit, and manage rental properties |
| **Messaging** | Direct communication between landlord and tenant |
| **Agreements** | Auto-generate lease documents with PDF download and digital signing |
| **Payments** | Track rent due/paid/overdue status with analytics dashboard |

## Tech Stack

- **Frontend:** React 18, Vite, Tailwind CSS, React Router
- **Backend:** Node.js 22+, Express, **Neon PostgreSQL** (cloud database)
- **Auth:** JWT-based authentication with role-based access (landlord / tenant)

## Project Structure

```
Tenant/
├── backend/
│   ├── src/
│   │   ├── routes/        # API endpoints
│   │   ├── middleware/    # Auth middleware
│   │   ├── database.js    # PostgreSQL (Neon) connection
│   │   ├── server.js      # Express server
│   │   └── seed.js        # Demo data
│   └── .env.example       # DATABASE_URL template (never commit .env)
├── frontend/
│   ├── src/
│   │   ├── components/    # Layout, shared UI
│   │   ├── pages/         # Dashboard, Tenants, Payments, etc.
│   │   ├── context/       # Auth context
│   │   └── services/      # API client
│   └── index.html
└── README.md
```

## Getting Started

### Prerequisites

- Node.js 22+ installed
- A [Neon](https://neon.tech) PostgreSQL database (connection string in `backend/.env`)

### 1. Install dependencies

```bash
# Backend
cd backend
npm install

# Frontend (new terminal)
cd frontend
npm install
```

### 2. Configure database

Copy the example env file and add your Neon connection string:

```bash
cd backend
cp .env.example .env
# Edit .env and set DATABASE_URL=postgresql://...
```

### 3. Seed demo data

```bash
cd backend
npm run seed
```

### 4. Start the servers

```bash
# Terminal 1 — Backend (port 3001)
cd backend
npm run dev

# Terminal 2 — Frontend (port 5173)
cd frontend
npm run dev
```

Open **http://localhost:5173** in your browser.

## Authentication

- **Landlord (Admin):** Pre-created system account only — cannot self-register. Credentials are set via `npm run seed`.
- **Tenants:** Self-register on the login page with their own email and password. After registering, the admin assigns them to a property.

## Demo Accounts

| Role | Email | Password | How to get access |
|------|-------|----------|-------------------|
| Admin (Landlord) | `admin@tenanthub.com` | `admin123` | Created by `npm run seed` |
| Tenant | Your own email | Your own password | Sign up on the login page |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | Login |
| POST | `/api/auth/register` | Tenant self-registration only |
| GET | `/api/dashboard` | Dashboard stats |
| CRUD | `/api/properties` | Property management |
| CRUD | `/api/tenants` | Tenant management |
| GET/POST | `/api/messages` | Messaging |
| GET/POST | `/api/agreements` | Lease agreements |
| GET | `/api/agreements/:id/pdf` | Download PDF |
| GET/POST | `/api/payments` | Payment tracking |
| GET | `/api/payments/analytics` | Payment analytics |

## Data Storage

All history (payments, messages, agreements, tenant info) is stored in your **Neon PostgreSQL** cloud database — accessible from anywhere, not just your local machine.

## Put on GitHub

```bash
cd d:\Tenant
git init
git add .
git commit -m "Initial commit: TenantHub landlord-tenant management app"
```

Create a new repository on [GitHub](https://github.com/new) (name it e.g. `tenanthub`), then:

```bash
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/tenanthub.git
git push -u origin main
```

**Never commit** `backend/.env` — it contains your database password. Only commit `.env.example` files.

## Free hosting (recommended setup)

| Part | Free service | Why |
|------|--------------|-----|
| **Database** | [Neon](https://neon.tech) | You already use this — free PostgreSQL tier |
| **Backend API** | [Render](https://render.com) | Free Node.js web service |
| **Frontend** | [Vercel](https://vercel.com) or [Netlify](https://netlify.com) | Free static hosting for React |

### Step 1 — Database (Neon)

You already have Neon. Copy your `DATABASE_URL` from the Neon dashboard.

### Step 2 — Backend on Render (free)

1. Push code to GitHub.
2. Go to [render.com](https://render.com) → **New +** → **Web Service**.
3. Connect your GitHub repo.
4. Settings:
   - **Root Directory:** `backend`
   - **Build Command:** `npm install`
   - **Start Command:** `npm start`
   - **Instance Type:** Free
5. Environment variables:
   - `DATABASE_URL` = your Neon connection string
   - `JWT_SECRET` = any long random string
   - `SMTP_HOST`, `SMTP_USER`, `SMTP_PASS` (optional, for email reminders)
6. Deploy. Copy your URL, e.g. `https://tenanthub-api.onrender.com`

After deploy, run seed once (Render **Shell** tab):

```bash
npm run seed
```

### Step 3 — Frontend on Vercel (free)

1. Go to [vercel.com](https://vercel.com) → **Add New Project** → import your GitHub repo.
2. Settings:
   - **Root Directory:** `frontend`
   - **Framework:** Vite
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
3. Environment variable:
   - `VITE_API_URL` = `https://YOUR-RENDER-URL.onrender.com/api`
4. Deploy. You get a URL like `https://tenanthub.vercel.app`

### Step 4 — Use on phone

Open your Vercel URL on any phone browser. Add to home screen for an app-like experience.

### Other free options

| Service | Good for |
|---------|----------|
| [Railway](https://railway.app) | Backend (limited free credits/month) |
| [Fly.io](https://fly.io) | Backend (small free allowance) |
| [Cloudflare Pages](https://pages.cloudflare.com) | Frontend (alternative to Vercel) |
| [GitHub Pages](https://pages.github.com) | Frontend only (needs API URL config) |

### Notes

- Render free tier **sleeps after 15 min** inactive — first request may take ~30 seconds to wake up.
- Neon free tier is enough for small projects.
- Change the default admin password after going live.

## License

MIT
