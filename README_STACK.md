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
- Ollama: local Qwen3 responses for the profile-based personal assistant

## Personal assistant

The personal assistant uses the Ollama Python client and the `qwen3:0.6b`
model. It reads `data/profile.json` on the server and uses it as the source for
answers about professional background, experience, skills, projects, and
education. Brief greetings and polite small talk are allowed; factual answers
stay grounded in the profile. The profile is not served to the browser. Make sure
the profile file is present in the deployment image or securely mounted into the web container.
Inference is bounded to an 8-message history, a 4K-token context, and concise
replies to reduce latency.
The web application sends chat history to Ollama on the server; the browser
does not connect to Ollama directly. `OLLAMA_HOST` and `OLLAMA_MODEL` can be
set through environment variables. Docker Compose defaults the host to
`host.docker.internal:11434`, so the Ollama service must be reachable from the
web container. On Linux, configure the Ollama service to listen on an address
reachable through Docker's host gateway and firewall access to the local
containers. Nginx limits the chat endpoint to 5 requests per minute per client
IP with a burst of 2 and rejects request bodies larger than 128 KB. Do not
expose Ollama's API directly to the public internet. The limit uses Nginx's
direct peer address; if a trusted proxy is added in front of Nginx, configure
trusted client-IP handling rather than trusting arbitrary forwarded headers.

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

This setup supports secure HTTPS, static file handling, and persistent data storage.

## Summary

The site combines a Python-based backend with a modern front-end presentation, making it a simple yet robust personal portfolio stack for deployment and maintenance.
