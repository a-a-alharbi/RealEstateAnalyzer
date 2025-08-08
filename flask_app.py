from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Tuple

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    send_file,
    session,
    flash,
)

import io

# ----- Optional, use real implementations if available -----
try:
    import utils as U  # your helper utilities
except Exception:
    U = None  # type: ignore

try:
    import financial_calculator as FC  # your compute engine
except Exception:
    FC = None  # type: ignore

try:
    import report_generator as RG  # PDF/Excel
except Exception:
    RG = None  # type: ignore
# -----------------------------------------------------------

app = Flask(__name__)
app.secret_key = "change-me"  # needed for session to keep last results


def _currency_symbol(code: str) -> str:
    if U and hasattr(U, "currency_symbol_for"):
        try:
            return U.currency_symbol_for(code)  # type: ignore[attr-defined]
        except Exception:
            pass
    return {"SAR": "﷼", "USD": "$", "EUR": "€", "GBP": "£"}.get(code.upper(), "")


def _to_float(v: Any, default: float = 0.0) -> float:
    try:
        if v is None or v == "":
            return default
        return float(v)
    except Exception:
        return default


def _compute_with_repo(payload: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    # Try your own compute functions first
    if FC:
        if hasattr(FC, "calculate_metrics"):
            res = FC.calculate_metrics(payload)  # type: ignore[attr-defined]
            if isinstance(res, tuple) and len(res) == 2:
                return res  # type: ignore[return-value]
            if isinstance(res, dict):
                return res["metrics"], res["yearly"]  # type: ignore[index]
        if hasattr(FC, "run"):
            out = FC.run(payload)  # type: ignore[attr-defined]
            return out["metrics"], out["yearly"]  # type: ignore[index]

    # Fallback demo compute (UI always renders)
    years = list(range(1, int(payload.get("exit_year", 10)) + 1))
    annual_rent = float(payload.get("annual_rent", 0))
    rent_g = float(payload.get("rent_growth", 0))
    opex_pct = float(payload.get("opex_percent", 0))
    insurance = float(payload.get("insurance", 0))
    hoa = float(payload.get("hoa", 0))
    debt_service = 50_000.0

    rents = [annual_rent * ((1 + rent_g) ** (y - 1)) for y in years]
    expenses = [r * opex_pct + insurance + hoa for r in rents]
    cashflows = [r - e - debt_service for r, e in zip(rents, expenses)]
    monthly_cf = (sum(cashflows) / len(cashflows) / 12) if cashflows else 0.0
    metrics = {
        "monthly_cash_flow": monthly_cf,
        "annual_cash_flow": monthly_cf * 12,
        "cash_on_cash": 0.12,
        "irr": 0.11,
        "cap_rate": 0.065,
        "dscr": 1.25,
        "payback_years": 8.4,
        "total_roi": 0.82,
        "noi_y1": (rents[0] - expenses[0]) if rents else 0.0,
    }
    yearly = [
        {
            "year": y,
            "rent": rents[y - 1],
            "expenses": expenses[y - 1],
            "noi": rents[y - 1] - expenses[y - 1],
            "debt_service": debt_service,
            "cash_flow": cashflows[y - 1],
            "equity": 100_000 + 20_000 * (y - 1),
        }
        for y in years
    ]
    return metrics, yearly


@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/analyzer", methods=["GET"])
def analyzer():
    return render_template("analyzer_form.html")


@app.route("/dashboard", methods=["POST"])
def dashboard():
    form = request.form

    payload = dict(
        currency=form.get("currency", "SAR"),
        purchase_price=_to_float(form.get("purchase_price")),
        down_payment=_to_float(form.get("down_payment")),
        interest_rate=_to_float(form.get("interest_rate")) / 100.0,
        loan_years=int(_to_float(form.get("loan_years"), 0)) or 0,
        annual_rent=_to_float(form.get("annual_rent")),
        exit_year=10,
    )

    metrics, yearly = _compute_with_repo(payload)
    if "annual_cash_flow" not in metrics and "monthly_cash_flow" in metrics:
        metrics["annual_cash_flow"] = metrics["monthly_cash_flow"] * 12

    years = [row.get("year") for row in yearly]
    rents = [float(row.get("rent", 0)) for row in yearly]
    expenses = [float(row.get("expenses", 0)) for row in yearly]
    cashflows = [float(row.get("cash_flow", 0)) for row in yearly]

    results = dict(
        as_of=date.today().isoformat(),
        currency_symbol=_currency_symbol(payload["currency"]),
        metrics=metrics,
        yearly=yearly,
        years=years,
        rents=rents,
        expenses=expenses,
        cashflows=cashflows,
        payload=payload,
    )

    session["last_results"] = results
    return render_template(
        "dashboard.html",
        as_of=results["as_of"],
        currency_symbol=results["currency_symbol"],
        metrics=results["metrics"],
        yearly=results["yearly"],
        years=results["years"],
        rents=results["rents"],
        expenses=results["expenses"],
        cashflows=results["cashflows"],
    )


@app.route("/export/pdf")
def export_pdf():
    results = session.get("last_results")
    if not results:
        flash("Run an analysis first.")
        return redirect(url_for("landing"))

    if RG and hasattr(RG, "generate_pdf"):
        try:
            pdf_bytes = RG.generate_pdf(results)  # type: ignore[attr-defined]
            return send_file(
                io.BytesIO(pdf_bytes),
                mimetype="application/pdf",
                as_attachment=True,
                download_name="RealEstateAnalyzer.pdf",
            )
        except Exception as e:
            flash(f"PDF export failed: {e}")
            return redirect(url_for("landing"))

    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.drawString(72, 800, "Real Estate Analyzer — PDF export placeholder")
    c.drawString(72, 780, f"As of: {results['as_of']}")
    c.drawString(72, 760, f"Cash-on-Cash: {results['metrics'].get('cash_on_cash', 0):.2%}")
    c.save()
    buf.seek(0)
    return send_file(buf, mimetype="application/pdf", as_attachment=True, download_name="RealEstateAnalyzer.pdf")


@app.route("/export/excel")
def export_excel():
    results = session.get("last_results")
    if not results:
        flash("Run an analysis first.")
        return redirect(url_for("landing"))

    if RG and hasattr(RG, "generate_excel"):
        try:
            xlsx_bytes = RG.generate_excel(results)  # type: ignore[attr-defined]
            return send_file(
                io.BytesIO(xlsx_bytes),
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                as_attachment=True,
                download_name="RealEstateAnalyzer.xlsx",
            )
        except Exception as e:
            flash(f"Excel export failed: {e}")
            return redirect(url_for("landing"))

    import csv

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Year", "Rent", "Expenses", "NOI", "Debt Service", "Cash Flow", "Equity"])
    for r in results["yearly"]:
        writer.writerow([r["year"], r["rent"], r["expenses"], r["noi"], r["debt_service"], r["cash_flow"], r["equity"]])
    data = io.BytesIO(buf.getvalue().encode("utf-8"))
    return send_file(data, mimetype="text/csv", as_attachment=True, download_name="RealEstateAnalyzer.csv")


if __name__ == "__main__":
    app.run(debug=True)
