# SEO Insight Pro

A production-ready **Django 6** SEO analytics dashboard built from the *Precision SEO* design system.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 6.0 |
| Frontend | Tailwind CSS (CDN), Inter font, Material Symbols |
| Database | SQLite (dev) → PostgreSQL (prod) |
| Forms | django-crispy-forms + crispy-bootstrap5 |
| Images | Pillow |

---

## Quick Start

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd seo_insight_dashboard
```

### 2. Create & activate a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example env file and fill in your values:

```bash
cp .env.example .env
```

Key variables:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
DATABASE_URL=sqlite:///db.sqlite3
```

### 5. Run migrations

```bash
python manage.py migrate
```

### 6. Collect static files (production only)

```bash
python manage.py collectstatic
```

### 7. Start the development server

```bash
python manage.py runserver
```

Visit **http://127.0.0.1:8000/**

---

## Project Structure

```
seo_insight_dashboard/
├── core/                   # Project configuration
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── dashboard/              # Main application
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── admin.py
├── templates/              # HTML templates
│   ├── base.html           # Master layout (sidebar + header)
│   └── dashboard/
│       ├── dashboard.html
│       ├── seo_audit.html
│       ├── keywords.html
│       ├── backlinks.html
│       ├── competitors.html
│       ├── settings.html
│       ├── pricing.html
│       └── landing.html
├── static/
│   └── css/
│       └── main.css        # Precision SEO custom styles
├── theme/                  # Original static prototypes (reference only)
├── manage.py
├── requirements.txt
└── .gitignore
```

---

## Pages

| Page | URL |
|---|---|
| Landing | `/landing/` |
| Dashboard | `/` |
| SEO Audit | `/audit/` |
| Keywords | `/keywords/` |
| Backlinks | `/backlinks/` |
| Competitors | `/competitors/` |
| Settings | `/settings/` |
| Pricing | `/pricing/` |

---

## Development Roadmap

- [ ] Implement `dashboard/models.py` — `Project`, `Keyword`, `AuditResult`, `Backlink`
- [ ] Add Django authentication (login/logout/register)
- [ ] Replace hardcoded template data with database queries via view context
- [ ] Integrate Google Search Console & GA4 APIs
- [ ] Add Chart.js for dynamic chart rendering
- [ ] Configure PostgreSQL for production
- [ ] Deploy to Railway / Render / DigitalOcean

---

## License

MIT
