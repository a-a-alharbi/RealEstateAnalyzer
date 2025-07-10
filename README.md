# RealEstateAnalyzer

RealEstateAnalyzer is a Flask-based application for evaluating real estate investment opportunities. It calculates common metrics such as ROI, IRR, cash flow and payback period to help investors make informed decisions.

## Features

- REST API powered by Flask
- Interactive dashboard built with HTML, Bootstrap and Plotly
- Excel and PDF report export with embedded charts (PDFs generated via WeasyPrint)
- Scenario analysis (conservative, base and optimistic)

## Installation

1. Clone the repository
2. Install Python 3.11 or newer
3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```
4. Start the server
   ```bash
   python main.py
   ```

The application will be available at `http://localhost:5000`.

## Project Structure

- `flask_app.py` – main Flask application and routes
- `financial_calculator.py` – core calculation engine
- `utils.py` – helpers for formatting, metrics and exporting
- `templates/` and `static/` – HTML templates, CSS and JavaScript
- `requirements.txt` – list of dependencies

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to this project.

### Rent Growth

The **Rent Growth % (optional)** field allows you to model annual rent escalation.
Enter a yearly percentage (e.g., `3` for 3% growth). If left at `0`, rents remain
flat. When a rate is provided, rents compound each year and all cash flow metrics,
ROI, IRR, payback period and charts will reflect the increasing income.
