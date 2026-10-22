# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

A small Flask marketing/brochure website for SETEC (setec-cr.com), a Costa Rican industrial equipment company. Single-file Flask app (`setec/app.py`) that renders static Jinja templates and handles one dynamic feature: a contact form that emails leads via Microsoft 365 SMTP.

## Commands

The repo is worked on from both Windows and macOS, and each has its own venv. Always call the venv's interpreter by path. Don't rely on `activate` or a bare `python`/`pip`.

| | Windows | macOS |
|---|---|---|
| Venv | `env/` (Python 3.14, deps installed) | `.venv_mac/` |
| Interpreter, from `setec/` | `..\env\Scripts\python.exe` | `../.venv_mac/bin/python` |

```powershell
# from setec/ (the app package root); Windows paths shown, swap in the macOS interpreter on the Mac
..\env\Scripts\python.exe -m pip install -r requirements.txt
..\env\Scripts\python.exe -m flask --app app run --port 5000 --debug   # http://127.0.0.1:5000/
```

- **Windows:** in the Git Bash tool, `python` on PATH is MSYS2's (`/c/msys64/mingw64/bin/python`, 3.12), which has none of the deps installed. Use `env\Scripts\python.exe`.
- **macOS:** `env/` is a Windows venv and won't run there. `.venv_mac/` was created under `~/Downloads/` and later moved, so its `activate` script and `bin/flask` shebang point to a path that no longer exists. Calling its interpreter by path still works. macOS AirPlay also listens on `*:5000`, but Flask on `127.0.0.1:5000` still works. "Address already in use" usually means a stale dev server is still running: find it with `lsof -nP -iTCP:5000 -sTCP:LISTEN`.
- `.venv_mac/` and `.DS_Store` files aren't covered by `.gitignore` (`env/` is), so don't commit them.
- gunicorn (production server) only runs on Linux/macOS, never on Windows. It runs from the repo root, because `--chdir setec` does the `cd`: `gunicorn --bind=0.0.0.0:8000 --chdir setec app:app`.
- No test suite, linter, or build step exists. To smoke-check that every canonical page still renders (for example after editing `base.html` or adding a route), run this from `setec/` with the platform's interpreter:
  ```bash
  ..\env\Scripts\python.exe -c "from app import app; c=app.test_client(); bad=[(r.rule,c.get(r.rule).status_code) for r in app.url_map.iter_rules() if r.rule.endswith('/') and '<' not in r.rule and c.get(r.rule).status_code!=200]; print(bad or 'all OK')"
  ```
- The git repo root is this directory, not the folder above it. That outer folder is synced through OneDrive (Windows) or `~/Documents/setec_flask/` (Mac). It holds sync leftovers you can ignore: `__setec_flask/` (a partial copy of `env/`) and `___All_Errors.txt` (a sync log of files that failed to download). On Windows it also holds several sibling clones of this same repo (`setec_flask`, `setec_flask (1)`, `setec_flask (2)`), each at a different commit. Before starting work, check `git log -1` and `git status` to confirm you're in the copy the user means.
- Config is via `.env` (see `setec/.env.example` for required keys: `SECRET_KEY`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `FLASK_DEBUG`, `DEST_EMAIL`). Never commit a real `.env`.
- Deployment target is Azure App Service; `Procfile` (repo root) and `setec/startup.txt` both run `gunicorn --chdir setec app:app` (`Procfile` binds `$PORT`, `startup.txt` binds `8000`). The `--chdir` is required because `app.py` lives inside `setec/`, not the repo root.
- `requirements.txt` is duplicated at the repo root and in `setec/` (identical contents) — update both when changing dependencies.
- `.env` files exist both at the repo root and in `setec/`. `load_dotenv()` looks for one starting from `app.py`'s directory, so `setec/.env` wins. In production, Azure App Settings supply these values instead (see `.env.example`).
- `SECRET_KEY` falls back to a random per-process value when it's unset. With several gunicorn workers, or after a restart, each process then has a different key, so session-stored CSRF tokens stop matching and the contact form returns 403. Always set `SECRET_KEY` when deploying. Similarly, the rate limiter uses `memory://` storage, so its limits apply per worker process.
- `setec/README.md` is partly out of date: debug mode comes from the `FLASK_DEBUG` env var, not a hardcoded `debug=True`.

## Architecture

- **Everything user-facing is in Spanish**: page copy, URL slugs (`/sobre-nosotros/`, `/contacto/`), code comments, and log messages. Keep new content and comments in Spanish to match.
- **Everything is one Flask app** (`setec/app.py`) — routes, security headers, CSRF, rate limiting, and mail sending all live in this single file. There's no blueprint/package split, no ORM, no database.
- **Routing convention**: every content route is registered twice — once as the canonical path with a trailing slash (e.g. `/sobre-nosotros/`), and once without a trailing slash purely to 301-redirect into the canonical form. The no-slash variants are all stacked as `@app.route` decorators on a single shared `redirect_no_slash` view at the bottom of `app.py` (not a wildcard) — when adding a new page, add both the real route/view and a matching `@app.route('/new-path')` line on that stack.
- **Templates mirror routes 1:1** under `setec/templates/`, all extending `base.html`. The `instrumentacion_analitica/` subdirectory holds a product-line's landing page plus per-brand pages (Mettler Toledo, Memmert, Scilogex, otras marcas).
- **`base.html` hardcodes the nav dropdown and footer link columns** with `url_for('<endpoint>')` calls to every page — adding a new route/template also means adding it to the nav and/or footer in `base.html`, or it won't be reachable from the site UI.
- **Contact form (`/contacto/`) is the only stateful logic**:
  - CSRF token is generated per-session (`generate_csrf`/`validate_csrf` in `app.py`) and rendered via `csrf_token()` (a Jinja global) into a hidden form field — this is a hand-rolled CSRF implementation, not Flask-WTF.
  - A honeypot field (`website`) silently "succeeds" for bots that fill it in.
  - Rate limited via Flask-Limiter: `5 per minute; 20 per hour` on POST only.
  - User input is escaped with `markupsafe.escape` before being interpolated into the outgoing HTML email body.
  - Mail is sent via Flask-Mail through Microsoft 365 SMTP (`smtp.office365.com:587`); recipients come from `DEST_EMAIL` in `.env`, comma-separated for multiple recipients (`DEST_EMAILS` list in `app.py`).
- **Security headers** (CSP, X-Frame-Options, etc.) are set globally in an `after_request` hook — if you add external scripts/styles/fonts/iframes/images, update the `Content-Security-Policy` string in `app.py` accordingly or they'll be blocked. Note `img-src` is `'self' data:` only, so hotlinked images from other sites won't load; download them into `setec/static/img/<page>/` instead. CSP `frame-src` already allows `https://www.youtube-nocookie.com` for embedding YouTube videos (see `calderas_bosch.html`'s `.video-embed` iframes).
- **Blog is a "Blog SETEC" nav dropdown over multiple sub-blogs, not a single CMS-backed list**: each sub-blog (e.g. "Biblioteca de Vapor SETEC" at `/blog/`, "Lavandería Industrial y Hospitalaria" at `/blog/lavanderia-industrial-hospitalaria/`) is its own hub template with a hero + `blog-grid`, listed as a `<li>` under the dropdown in `base.html`. Within a hub, each real article is its own template + route (e.g. `blog_fundamentos_calderas.html`), following the same double-registration (with/without trailing slash) convention as any other page, with a matching `blog-card` link added to the hub's `blog-grid`. (The lavandería hub's `blog-grid` is currently empty — no articles yet.) Article templates reuse the `.article-body`/`.article-figure`/`.article-callout`/`.article-flow` CSS classes and the `.faq-list` pattern from `calderas_bosch.html` (including a JSON-LD `FAQPage` schema in `extra_head`).
