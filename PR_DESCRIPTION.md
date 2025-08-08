# Frontend Overhaul: The Data Company Branding & UX

## Summary
- Introduces a modern, branded frontend (landing page, analyzer form, dashboard)
- Restores `flask_app.py` from `main` to keep full backend calculation/export features

## What changed
- Added `templates/base.html`, `templates/landing.html`, `templates/analyzer_form.html`, `templates/dashboard.html`
- Added `static/css/tdc.css` for styling
- Reverted backend to original implementation (`flask_app.py` from `main`)

## Notes
- Frontend templates can be wired to the restored backend endpoints (`/calculate`, `/export/pdf`, `/export/excel`)

## How to test
1. `pip install -r requirements.txt`
2. `python flask_app.py`
3. Use the legacy `index.html` or adapt the new templates to call `/calculate`
