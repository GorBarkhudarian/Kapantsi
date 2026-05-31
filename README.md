# Կապանցի (Kapantsi)

**Civic Engagement Platform for Kapan, Armenia**

Kapantsi is a civic tech platform for Kapan, Syunik, Armenia. Citizens report local infrastructure issues, vote on priorities, and receive transparent status updates from the municipality — all logged with a simulated blockchain for transparency.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11 + Django 4.2 + Django REST Framework |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Frontend | Django Templates + Tailwind CSS CDN + Vanilla JS |
| Maps | Leaflet.js + OpenStreetMap (centered on Kapan) |
| Auth | JWT (SimpleJWT) + Django session auth |
| Blockchain | SHA-256 vote chain (hashlib simulation) |
| Async | Celery + Redis (optional) |

---

## Quick Setup

### 1. Prerequisites
- Python 3.11+
- pip

### 2. Clone / Open folder
```bash
cd Kapantsi
```

### 3. Create virtual environment
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### 4. Install dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure environment
```bash
copy .env .env.local   # Windows
# or: cp .env .env.local
# Edit .env if needed (SQLite is used by default)
```

### 6. Run migrations
```bash
python manage.py migrate
```

### 7. Seed sample data
```bash
python manage.py seed_data
```

### 8. Start the server
```bash
python manage.py runserver
```

Open: **http://127.0.0.1:8000**

---

## Default Credentials

| Role | Username | Password |
|---|---|---|
| Admin | `admin_kapan` | `admin123` |
| Admin | `admin_municipality` | `admin123` |
| Citizen | `hayk_sargsyan` | `citizen123` |
| Citizen | `ani_petrosyan` | `citizen123` |
| Citizen | `david_grigoryan` | `citizen123` |
| (8 more citizens) | `*_*` | `citizen123` |

---

## URL Map

| URL | Description |
|---|---|
| `/` | Landing page (stats, recent issues, features) |
| `/issues/` | Issue feed with filters |
| `/issues/new/` | Report a new issue (login required) |
| `/issues/<id>/` | Issue detail, vote, comment, timeline |
| `/map/` | Interactive Leaflet map of Kapan |
| `/dashboard/` | Citizen personal dashboard |
| `/admin-dashboard/` | Admin panel (staff only) |
| `/register/` | Register account |
| `/login/` | Login |
| `/admin/` | Django admin |

## API Endpoints

| Method | URL | Description |
|---|---|---|
| POST | `/api/auth/register/` | Register user |
| POST | `/api/auth/login/` | Get JWT tokens |
| GET/POST | `/api/issues/` | List / create issues |
| GET/PATCH | `/api/issues/<id>/` | Detail / admin status update |
| POST/DELETE | `/api/issues/<id>/vote/` | Cast / remove vote |
| GET | `/api/issues/<id>/votes/` | Blockchain vote log |
| GET | `/api/notifications/` | User notifications |
| GET | `/api/dashboard/stats/` | Admin statistics |

---

## Map — Kapan Region

The map is centered on **Kapan city (39.2067, 46.4058)** and includes pins for surrounding villages:
- Geghanush, Davit Bek, Tatev, Shinuhayr, Syunik village

Marker colors: Pending | Under Review | In Progress | Completed | Rejected

---

## Features

- Bilingual interface: Armenian (hy) + English (en)
- Role-based access: citizen / admin
- National ID verification simulation (8-digit unique)
- One vote per verified citizen per issue (DB-enforced)
- SHA-256 blockchain vote chain
- Issue status lifecycle with history + notifications
- Interactive map with category/status/area filters
- Admin dashboard with Chart.js charts
- Image upload for issues
- Comment system
- JWT API + Django session auth

---

© 2026 Kapantsi — Kapan Municipality 
