# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

A small Flask marketing/brochure website for SETEC (setec-cr.com), a Costa Rican industrial equipment company. Single-file Flask app (`setec/app.py`) that renders static Jinja templates and handles one dynamic feature: a contact form that emails leads via Microsoft 365 SMTP.

## Commands

All commands run from the `setec/` directory (the app package root), not the repo root.

```bash
cd setec

# Install dependencies
pip install -r requirements.txt

# Run locally (dev server)
python app.py

# Run with gunicorn (matches production/Procfile)
gunicorn --bind=0.0.0.0:8000 --chdir setec app:app   # run from repo root instead
```

- Local dev server: http://127.0.0.1:5000/
- No test suite, linter, or build step exists in this repo.
- Config is via `.env` (see `setec/.env.example` for required keys: `SECRET_KEY`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `FLASK_DEBUG`, `DEST_EMAIL`). Never commit a real `.env`.
- Deployment target is Azure App Service; `Procfile` (repo root) and `setec/startup.txt` both run `gunicorn --chdir setec app:app` — the `--chdir` is required because `app.py` lives inside `setec/`, not the repo root.

## Architecture

- **Everything is one Flask app** (`setec/app.py`) — routes, security headers, CSRF, rate limiting, and mail sending all live in this single file. There's no blueprint/package split, no ORM, no database.
- **Routing convention**: every content route is registered twice — once as the canonical path with a trailing slash (e.g. `/sobre-nosotros/`), and once without a trailing slash purely to 301-redirect into the canonical form. The no-slash variants are all stacked as `@app.route` decorators on a single shared `redirect_no_slash` view at the bottom of `app.py` (not a wildcard) — when adding a new page, add both the real route/view and a matching `@app.route('/new-path')` line on that stack.
- **Templates mirror routes 1:1** under `setec/templates/`, all extending `base.html`. The `instrumentacion_analitica/` subdirectory holds a product-line's landing page plus per-brand pages (Mettler Toledo, Memmert, Scilogex, otras marcas).
- **Contact form (`/contacto/`) is the only stateful logic**:
  - CSRF token is generated per-session (`generate_csrf`/`validate_csrf` in `app.py`) and rendered via `csrf_token()` (a Jinja global) into a hidden form field — this is a hand-rolled CSRF implementation, not Flask-WTF.
  - A honeypot field (`website`) silently "succeeds" for bots that fill it in.
  - Rate limited via Flask-Limiter: `5 per minute; 20 per hour` on POST only.
  - User input is escaped with `markupsafe.escape` before being interpolated into the outgoing HTML email body.
  - Mail is sent via Flask-Mail through Microsoft 365 SMTP (`smtp.office365.com:587`); recipients come from `DEST_EMAIL` in `.env`, comma-separated for multiple recipients (`DEST_EMAILS` list in `app.py`).
- **Security headers** (CSP, X-Frame-Options, etc.) are set globally in an `after_request` hook — if you add external scripts/styles/fonts/iframes, update the `Content-Security-Policy` string in `app.py` accordingly or they'll be blocked.
