# Project Knowledge Base

## Overview
This repository contains a Django-based personal portfolio website for Md. Sayed Ahammed. It includes a landing page, career timeline, project highlights, contact form, and downloadable resume PDF.

## Project Structure

- `manage.py` — Django project entry point.
- `portfolio/` — application logic, models, and time/weather MCP server.
- `portfolio_site/` — Django project settings and URL configuration.
- `templates/` — HTML templates used by the site.
- `static/` — CSS and JavaScript assets.
- `MD_SAYED_AHAMMED_RESUME.pdf` — downloadable resume PDF stored at project root.
- `docker-compose.yml` — production deployment setup with Django, MCP tools,
  Nginx, and Certbot.
- `README.md` — project setup and deployment instructions.
- `KNOWLEDGE_BASE.md` — project architecture and operational notes.

## Core Django Components

### `portfolio/views.py`
Defines the main views:

- `home(request)`
  - Renders `home.html` with an empty contact form.
- `smalltalk_chat(request)`
  - Validates and rate-limits a single current user message.
  - Routes current time/weather requests to MCP tools.
  - Sends the system prompt and current message to Ollama and streams the reply.
- `contact(request)`
  - Accepts POST requests.
  - Validates `ContactForm`.
  - Saves the submission to the database.
  - Shows a success message and redirects back to the contact section.
- `download_resume(request)`
  - Opens the PDF file from `BASE_DIR` and serves it as a downloadable attachment.

### `portfolio/mcp_server.py`
Defines the internal Streamable HTTP MCP server and its read-only tools:

- `get_current_time(timezone="Asia/Dhaka")`
  - Returns current local time using Python `datetime` and IANA `zoneinfo`.
- `get_current_weather(city="Dhaka")`
  - Resolves the city with Open-Meteo Geocoding, then returns current conditions
    from the Open-Meteo Forecast API.
  - Requires outbound network access from the MCP service; no API key is used.

The web application is the MCP client. The MCP service is internal to Docker
Compose and is not published on a host port.

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
- `"smalltalk/chat/"` → `views.smalltalk_chat`
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
Handles navigation toggling and the AI assistant chat client. Chat requests are
sent with `fetch`; streamed Server-Sent Events are decoded and appended to the
transcript using text content.

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
- `OLLAMA_HOST` and `OLLAMA_MODEL` configure the Ollama API and model
- `MCP_SERVER_URL` selects the MCP service URL outside debug mode
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
- `mcp-tools` service
  - Internal Streamable HTTP MCP server for time and weather
  - Not exposed on a host port
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

With the default debug settings, time/weather tools run through the in-process
MCP server. The weather tool needs outbound internet access to Open-Meteo.

To create an admin user:

```bash
.venv/bin/python manage.py createsuperuser
```

## Production Notes
- The site expects `DJANGO_SECRET_KEY` to be set before running in production mode.
- The deployment uses Let’s Encrypt and redirects HTTP to HTTPS.
- Nginx redirects `www` to the apex domain and handles TLS renewal updates.
- Static files are collected in `staticfiles`.

## AI Assistant Request Flow

The AI assistant is stateless: the visible transcript remains in the browser,
but previous turns are not sent to Ollama.

1. The user submits the assistant form in `templates/home.html`.
2. `static/js/site.js` sends a CSRF-protected `POST` to `/smalltalk/chat/` with
   only the current user message.
3. `portfolio.views.smalltalk_chat()` enforces 10 requests per minute per client
   IP and rejects malformed messages, chat history, or messages over 1,000
   characters.
4. `portfolio.views._personal_assistant_prompt()` reads `data/profile.json` and
   builds the system prompt that constrains profile answers to that data.
5. `portfolio.views._requested_mcp_calls()` checks the current message for
   time/weather terms. Weather requests call `get_current_weather`; an explicit
   location is extracted and the default is Dhaka. Time requests call
   `get_current_time`; an explicit IANA timezone is used when present, otherwise
   the timezone defaults to `Asia/Dhaka`.
6. `portfolio.views._execute_mcp_tool()` uses the MCP Python SDK client to call
   the selected tool. With `DEBUG=True`, the MCP client connects to the server
   object in-process, so local development needs no separate service. With
   `DEBUG=False`, it connects to `MCP_SERVER_URL`.
7. Successful MCP results are added to the system prompt under
   `VERIFIED_LIVE_MCP_DATA`. The Ollama model receives that system prompt and
   the one current user message. The application performs time/weather routing
   before asking the model; it does not rely on the model to decide whether to
   call an MCP tool.
8. Ollama generates a streamed response. Django encodes each text chunk into an
   SSE event; the browser decodes the chunks and updates the assistant message.
   Ollama and MCP failures are logged and surfaced as an HTTP error or SSE error.

### MCP deployment

- Docker Compose runs `mcp-tools` from `python -m portfolio.mcp_server` on the
  internal Docker network at `http://mcp-tools:8001/mcp`.
- The `web` service waits for the MCP service health check before starting.
- The MCP server uses Streamable HTTP, is configured statelessly, and exposes
  only the current-time and current-weather tools.
- Install the `mcp` package through `requirements.txt` when building the
  application image or preparing a local virtual environment.
- Keep the MCP port private; it is not intended for public access.

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
docker compose logs -f web mcp-tools nginx certbot
```

## Notes for Future Work
- The portfolio content lives mostly in `templates/home.html`.
- Styling changes are centralized in `static/css/site.css`.
- Keep time/weather intent routing and MCP tool names aligned with
  `portfolio/mcp_server.py`.
- Production Django expects the private `mcp-tools` service configured by
  Docker Compose; keep that service off public ports.
- The site is well suited for content updates by editing the HTML template and static assets rather than Python logic.

## Summary
This project is a Django-powered professional portfolio with a SQLite-backed
contact form, downloadable resume, and Docker deployment. Its stateless AI
assistant uses Ollama for responses and a private MCP server for current time
and weather data.
