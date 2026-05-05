# Restaurant Safety & Operations Management System (RSOMS)

> **A unified platform integrating restaurant operations with food safety compliance (FSSAI India).**

---

## Problem Statement

Existing restaurant management applications (Zomato, Swiggy, Petpooja, Posist) focus solely on billing, ordering, or delivery logistics. **None of them address kitchen hygiene tracking, FSSAI certificate management, or consumer-facing safety transparency.** FSSAI data shows 40% of restaurants on delivery platforms are unverified, and consumer complaints about food safety are rising.

**RSOMS bridges this critical gap** by combining operations + safety compliance into a single affordable platform.

---

## Key Innovations

1. **FSSAI Certificate Management** — Upload, track expiry, get automated alerts
2. **Digital Hygiene Checklist** — Daily/weekly staff checklists with scoring
3. **Auto-Generated Safety Score (0-100)** — Calculated from checklist compliance
4. **Public Safety Badge** — Gold / Silver / Bronze / Red visible to consumers
5. **Unified Dashboard** — Operations + safety analytics in one view
6. **Staff Training Tracker** — Hygiene training log with expiry dates
7. **Consumer Verification Page** — Public-facing kitchen safety profile

---

## Tech Stack

- **Frontend**: HTML5, CSS3, JavaScript (Vanilla), Chart.js
- **Backend**: Python 3.x, Flask
- **Database**: SQLite (development), PostgreSQL (production)
- **Auth**: Flask-Login, Werkzeug password hashing
- **Forms**: WTForms with CSRF protection
- **ORM**: SQLAlchemy

---

## Features

### For Restaurant Owners (Admin)
- Restaurant profile management
- FSSAI certificate upload with expiry alerts
- Digital menu management (CRUD)
- Order creation & real-time status tracking
- Unified dashboard with hygiene score + sales metrics
- Staff hygiene training records
- Analytics & trend reports

### For Staff
- Daily hygiene checklist submission
- View assigned orders (KDS)
- Training completion updates

### For Consumers (Public)
- Search restaurants by name
- View safety badge and hygiene score
- Verify FSSAI certificate status
- Submit feedback / complaints

---

## Security Features

- PBKDF2-SHA256 password hashing
- Session-based authentication with Flask-Login
- Role-based access control (Admin / Staff / Consumer)
- CSRF token protection on all forms
- SQL injection prevention via SQLAlchemy ORM
- XSS prevention via Jinja2 auto-escaping
- Secure file upload (extension whitelist, size limits)

---

## Installation & Setup

```bash
# 1. Clone the repository
git clone <repo-url>
cd restaurant-managementsyste

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python app.py

# 5. Open browser
http://localhost:5000
```

---

## Database Schema

See `PLAN.md` for full schema.

Key tables: `users`, `restaurants`, `menu_items`, `orders`, `order_items`, `hygiene_checklists`, `staff_training`, `feedback`.

---

## API Endpoints

RESTful API design. See `PLAN.md` for full endpoint list.

Key routes:
- `/api/auth/*` — Authentication
- `/api/restaurant/*` — Restaurant profile & FSSAI
- `/api/menu/*` — Menu management
- `/api/orders/*` — Order lifecycle
- `/api/hygiene/*` — Checklists & scores
- `/api/dashboard/stats` — Aggregated dashboard data
- `/api/public/*` — Consumer-facing read-only data

---

## Project Structure

```
restaurant-managementsyste/
├── app.py                  # Flask application entry point
├── models.py               # SQLAlchemy database models
├── forms.py                # WTForms validation classes
├── config.py               # Application configuration
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── PLAN.md                 # Project plan & architecture
├── Q&A.md                  # Interview Q&A for guide
├── static/
│   ├── css/
│   │   └── style.css       # Main stylesheet
│   ├── js/
│   │   ├── main.js         # Core frontend logic
│   │   └── charts.js       # Chart.js configurations
│   └── uploads/            # FSSAI certificate files
└── templates/
    ├── base.html           # Base layout template
    ├── index.html          # Landing page
    ├── login.html          # Login page
    ├── register.html       # Registration page
    ├── dashboard.html      # Admin unified dashboard
    ├── restaurant_profile.html
    ├── menu.html
    ├── orders.html
    ├── order_kds.html      # Kitchen Display System
    ├── hygiene_checklist.html
    ├── staff_training.html
    ├── analytics.html
    ├── public_restaurant.html  # Consumer safety page
    └── notifications.html
```

---

## Screenshots & Flows

*To be added after development.*

---

## Future Scope

- Mobile application (React Native / Flutter)
- IoT sensor integration for automatic temperature logging
- AI-based image recognition for hygiene audits
- Blockchain-verified FSSAI certificates
- SMS/email alerts for certificate expiry
- Multi-language support

---

## License

Academic Project — NTCC

---

## Author

Suraj — NTCC Project 2026
