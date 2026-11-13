# Tech Stack Overview

This portfolio site is built as a lightweight Django application with a static front-end and a production-ready Docker deployment.

## Core Stack

- Python 3
- Django
- SQLite
- HTML5
- CSS3
- JavaScript
- Docker
- Nginx
- Certbot / Let's Encrypt

## What each part is used for

- Django: application framework, routing, views, forms, and admin management
- SQLite: local database for storing contact form submissions
- HTML/CSS/JS: portfolio layout, styling, and interactive UI behavior
- Docker: containerized deployment and environment consistency
- Nginx: reverse proxy and static asset serving
- Certbot: automatic HTTPS certificate issuance and renewal

## Project Structure Highlights

- `portfolio/` — Django app logic
- `portfolio_site/` — project settings and URL config
- `templates/` — page templates
- `static/` — CSS and JavaScript assets
- `docker-compose.yml` — production stack definition

## Run Locally

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver
```

## Production Deployment

The app is deployed with Docker Compose using:

- Django web container
- Nginx reverse proxy
- Certbot for TLS certificates

On first startup, Certbot requests a certificate after Nginx is serving the HTTP challenge. Nginx enables HTTPS when the certificate is available, and Certbot renews it automatically. Set `DJANGO_SECRET_KEY` and `CERTBOT_EMAIL` in `.env`, point both domain records to the server, and allow inbound ports 80 and 443.

Check the public HTTPS endpoint with:

```bash
curl -I https://sayedahammed.com/
```

If curl reports error 7, the TCP connection to port 443 was refused or unreachable; verify the DNS A/AAAA records, server firewall, provider firewall, and that the Compose `nginx` service is running with port 443 published.

## Summary

The site combines a Python-based backend with a modern front-end presentation, making it a simple yet robust personal portfolio stack for deployment and maintenance.
