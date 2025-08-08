# Frontend Overhaul: The Data Company Branding & UX

## Summary
This PR replaces the existing Flask UI with a modern, branded frontend:
- New **landing page** (`/`)
- New **analyzer form** (`/analyzer`) to collect inputs
- New **dashboard** (`/dashboard`) to display KPIs, charts, and table
- Shared **base layout** with dark mode toggle and Bootstrap 5

## What changed
- Added `templates/base.html`, `templates/landing.html`, `templates/analyzer_form.html`, `templates/dashboard.html`
- Added `static/css/tdc.css` (brand styling)
- Added `flask_app.py` with routes and wiring to existing compute/export functions

## Notes
- Backend compute is not changed; `flask_app.py` first tries your real functions (e.g., `financial_calculator.calculate_metrics`) and falls back to demo math if not found.
- Export endpoints remain `/export/pdf` and `/export/excel`. They call your `report_generator` when available; otherwise return simple placeholders.

## How to test
1. `pip install -r requirements.txt` (ensure Flask and Plotly)
2. `python flask_app.py` (or integrate into your main entrypoint)
3. Visit `/` → Launch Analyzer → Submit form → View dashboard
4. Try PDF/Excel export

## Follow-ups (optional)
- Plug brand colors & logo into `static/css/tdc.css`
- Wire the analyzer form fields to the exact calculator parameters
- Replace fallback export code with real `report_generator` implementation

