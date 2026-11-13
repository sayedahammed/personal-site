# Project Knowledge Base

## Overview
This repository contains a Django-based personal portfolio website for Md. Sayed Ahammed. It includes a landing page, career timeline, project highlights, contact form, and downloadable resume PDF.

## Project Structure

- `manage.py` — Django project entry point.
- `portfolio/` — application logic and models.
- `portfolio_site/` — Django project settings and URL configuration.
- `templates/` — HTML templates used by the site.
- `static/` — CSS and JavaScript assets.
- `MD_SAYED_AHAMMED_RESUME.pdf` — downloadable resume PDF stored at project root.
- `docker-compose.yml` — production deployment setup with Django, Nginx, and Certbot.
- `README.md` — project setup and deployment instructions.

## Core Django Components

### `portfolio/views.py`
Defines the main views:

- `home(request)`
  - Renders `home.html` with an empty contact form.
- `contact(request)`
  - Accepts POST requests.
  - Validates `ContactForm`.
  - Saves the submission to the database.
  - Shows a success message and redirects back to the contact section.
- `download_resume(request)`
  - Opens the PDF file from `BASE_DIR` and serves it as a downloadable attachment.

### `portfolio/models.py`
Model definition:

- `ContactMessage`
  - `name` — `CharField(max_length=120)`
  - `email` — `EmailField()`
  - `subject` — `CharField(max_length=180)`
  - `message` — `TextField()`
  - `submitted_at` — `DateTimeField(auto_now_add=True)`
  - Meta ordering: newest first

### `portfolio/forms.py`
`ContactForm` is a `ModelForm` for `ContactMessage`.

It configures the HTML field widgets with labels and input placeholders such as:

- `name`
- `email`
- `subject`
- `message`

### `portfolio/admin.py`
Registers `ContactMessage` for Django admin management.

Admin configuration includes:

- list display: name, email, subject, submitted_at
- filtering by submitted date
- search across name, email, subject, message
- readonly submitted_at field

## Routing
Defined in `portfolio_site/urls.py`:

- `""` → homepage (`views.home`)
- `"contact/"` → `views.contact`
- `"resume/"` → `views.download_resume`
- `"admin/"` → Django admin UI

## Templates

### `templates/base.html`
Shared HTML skeleton that includes:

- page metadata
- Google Fonts
- CSS stylesheet from `static/css/site.css`
- JS script from `static/js/site.js`
- placeholder for content blocks

### `templates/home.html`
Main portfolio landing page containing:

- site header and navigation
- hero section with SVG illustration
- About section
- Work / Career Journey timeline
- Project cards
- Expertise section
- Impact stats
- Education section
- Contact section with form
- social links and email

## Static Assets

### `static/css/site.css`
Contains the styling for the portfolio design: layout, typography, cards, buttons, responsive navigation, forms, and visual sections.

### `static/js/site.js`
Handles front-end interactions such as navigation toggling and client-side behavior.

## Settings and Environment
Configuration file: `portfolio_site/settings.py`

Key settings:

- `BASE_DIR` points to project root
- `DEBUG` reads from `DJANGO_DEBUG` environment variable
- `SECRET_KEY` reads from `DJANGO_SECRET_KEY`, with a safe fallback only for local development
- `ALLOWED_HOSTS` is loaded from `DJANGO_ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS` is loaded from `DJANGO_CSRF_TRUSTED_ORIGINS`
- Database defaults to SQLite at `db.sqlite3` or `DJANGO_DATABASE_PATH`
- Static files are served from `static/` and collected to `staticfiles/`
- `TIME_ZONE` is set to `Asia/Dhaka`
- `SECURE_SSL_REDIRECT` is enabled when `DEBUG` is `False`

## Database
The project uses SQLite by default:

- database file: `db.sqlite3`
- Docker deployment stores the database in a persistent Docker volume (`portfolio_db`)

## Deployment Overview
The `docker-compose.yml` file defines a production stack with:

- `web` service
  - Django app container
  - runs with `DJANGO_DEBUG=0`
  - mounts persistent volume for SQLite
  - mounts static file volume
- `nginx` service
  - serves the app and static files
  - exposes ports `80` and `443`
- `certbot` service
  - renews TLS certificates using webroot validation

## Local Development
From `README.md`:

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver
```

To create an admin user:

```bash
.venv/bin/python manage.py createsuperuser
```

## Production Notes
- The site expects `DJANGO_SECRET_KEY` to be set before running in production mode.
- The deployment uses Let’s Encrypt and redirects HTTP to HTTPS.
- Nginx redirects `www` to the apex domain and handles TLS renewal updates.
- Static files are collected in `staticfiles`.

## Contact Submission Flow
1. User submits the form from `home.html`.
2. Form posts to `/contact/`.
3. `views.contact()` validates the data.
4. If valid, the model instance is saved.
5. Success message is added via Django messages.
6. Browser redirects back to the homepage contact section.

## Useful Commands

### Run migrations
```bash
python manage.py migrate
```

### Start development server
```bash
python manage.py runserver
```

### Create admin user
```bash
python manage.py createsuperuser
```

For the Docker deployment, create the admin user inside the running web container:

```bash
docker compose exec web python manage.py createsuperuser
```

### Check project status in Docker
```bash
docker compose up -d --build
docker compose logs -f web nginx certbot
```

## Notes for Future Work
- The portfolio content lives mostly in `templates/home.html`.
- Styling changes are centralized in `static/css/site.css`.
- The application is intentionally lightweight; no major service architecture beyond Django is used.
- The site is well suited for content updates by editing the HTML template and static assets rather than Python logic.

## Summary
This project is a compact, Django-powered professional portfolio with a custom design, a contact form backed by SQLite, downloadable resume support, and Docker-based production deployment. It is easy to extend for future portfolio content updates or deployment enhancements.
