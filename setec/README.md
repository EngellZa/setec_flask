# Setec Flask Website

This is a small Flask application serving static pages for the Setec website.

## Setup

1. Create and activate a virtual environment.
   - Windows:
     ```powershell
     python -m venv venv
     .\\venv\\Scripts\\Activate.ps1
     ```
   - macOS / Linux:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python app.py
   ```

4. Open `http://127.0.0.1:5000/` in your browser.

## Project structure

- `app.py` - Flask application routes and redirect handling.
- `requirements.txt` - Flask dependency.
- `templates/` - HTML templates for pages.
- `static/` - CSS, JS, and image assets.

## Notes

- The app currently uses `debug=True` in `app.py` for local development.
- Remove or disable debug mode before deployment.
