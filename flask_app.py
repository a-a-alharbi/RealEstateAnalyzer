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
import tempfile

from helpers import format_currency, format_percentage
from financial_calculator import FinancialCalculator
from utils import get_advanced_metrics, export_to_excel
from report_generator import generate_pdf_report

app = Flask(__name__)
app.secret_key = "change-me"  # needed for session to keep last results


def _currency_symbol(code: str) -> str:
    return {"SAR": "﷼", "USD": "$", "EUR": "€", "GBP": "£"}.get(code.upper(), "")


def _to_float(v: Any, default: float = 0.0) -> float:
    try:
        if v is None or v == "":
            return default
        return float(v)
    except Exception:
        return default


def _compute_with_repo(payload: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Use the main branch's FinancialCalculator for analysis."""
    calc = FinancialCalculator(
        property_price=payload["purchase_price"],
        down_payment=payload["down_payment"],
        loan_term=payload["loan_years"],
        interest_rate=payload["interest_rate"] * 100,
        base_monthly_rent=payload["annual_rent"] / 12,
        occupancy_rate=(1 - payload["vacancy_rate"]) * 100,
        rent_growth=payload["rent_growth"] * 100,
        enhancement_costs=payload["rehab_cost"],
        hoa_fees_annual=payload["hoa"],
        holding_period=payload["exit_year"],
    )

    scenarios = calc.get_scenario_analysis()
    advanced = get_advanced_metrics(calc)

    annual_debt_service = calc.get_monthly_payment() * 12
    amort = calc.get_amortization_schedule(payload["exit_year"] * 12)
    principals = amort["principal"]

    equity = payload["down_payment"] + payload["rehab_cost"]
    yearly: List[Dict[str, Any]] = []
    for year in range(1, payload["exit_year"] + 1):
        rent = calc.get_effective_monthly_rent_for_year(year) * 12
        expenses = rent * payload["opex_percent"] + payload["insurance"] + payload["hoa"]
        noi = rent - expenses
        cash_flow = noi - annual_debt_service
        principal_paid = sum(principals[(year - 1) * 12 : year * 12])
        equity += principal_paid
        yearly.append(
            {
                "year": year,
                "rent": rent,
                "expenses": expenses,
                "noi": noi,
                "debt_service": annual_debt_service,
                "cash_flow": cash_flow,
                "equity": equity,
            }
        )

    base = scenarios["base"]
    metrics = {
        "monthly_cash_flow": base["monthly_cash_flow"],
        "annual_cash_flow": base["annual_cash_flow"],
        "cash_on_cash": advanced["cash_on_cash_return"] / 100,
        "irr": (base["irr"] or 0) / 100,
        "cap_rate": advanced["cap_rate"] / 100,
        "dscr": advanced["dscr"],
        "payback_years": advanced["payback_period"],
        "total_roi": base["roi"] / 100,
        "noi_y1": base["net_income_schedule"][0] if base["net_income_schedule"] else 0,
    }

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
        closing_costs=_to_float(form.get("closing_costs")),
        interest_rate=_to_float(form.get("interest_rate")) / 100.0,
        loan_years=int(_to_float(form.get("loan_years"), 0)) or 0,
        annual_rent=_to_float(form.get("annual_rent")),
        rent_growth=_to_float(form.get("rent_growth")) / 100.0,
        vacancy_rate=_to_float(form.get("vacancy_rate")) / 100.0,
        opex_percent=_to_float(form.get("opex_percent")) / 100.0,
        insurance=_to_float(form.get("insurance")),
        hoa=_to_float(form.get("hoa")),
        rehab_cost=_to_float(form.get("rehab_cost")),
        exit_year=int(_to_float(form.get("exit_year"), 10)) or 10,
        exit_cap_rate=_to_float(form.get("exit_cap_rate")) / 100.0,
    )

    metrics, yearly = _compute_with_repo(payload)

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

    payload = results["payload"]
    try:
        calc = FinancialCalculator(
            property_price=payload["purchase_price"],
            down_payment=payload["down_payment"],
            loan_term=payload["loan_years"],
            interest_rate=payload["interest_rate"] * 100,
            base_monthly_rent=payload["annual_rent"] / 12,
            occupancy_rate=(1 - payload["vacancy_rate"]) * 100,
            rent_growth=payload["rent_growth"] * 100,
            enhancement_costs=payload["rehab_cost"],
            hoa_fees_annual=payload["hoa"],
            holding_period=payload["exit_year"],
        )
        scenarios = calc.get_scenario_analysis()
        advanced = get_advanced_metrics(calc)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            generate_pdf_report(
                {
                    "calculator": calc,
                    "scenarios": scenarios,
                    "advanced_metrics": advanced,
                },
                tmp.name,
            )
            tmp.flush()
            return send_file(
                tmp.name,
                mimetype="application/pdf",
                as_attachment=True,
                download_name="RealEstateAnalyzer.pdf",
            )
    except Exception as e:
        flash(f"PDF export failed: {e}")
        return redirect(url_for("landing"))


@app.route("/export/excel")
def export_excel():
    results = session.get("last_results")
    if not results:
        flash("Run an analysis first.")
        return redirect(url_for("landing"))

    payload = results["payload"]
    try:
        import pandas as pd

        calc = FinancialCalculator(
            property_price=payload["purchase_price"],
            down_payment=payload["down_payment"],
            loan_term=payload["loan_years"],
            interest_rate=payload["interest_rate"] * 100,
            base_monthly_rent=payload["annual_rent"] / 12,
            occupancy_rate=(1 - payload["vacancy_rate"]) * 100,
            rent_growth=payload["rent_growth"] * 100,
            enhancement_costs=payload["rehab_cost"],
            hoa_fees_annual=payload["hoa"],
            holding_period=payload["exit_year"],
        )
        scenarios = calc.get_scenario_analysis()

        scenario_data = []
        for key, name in [
            ("conservative", "Conservative"),
            ("base", "Base"),
            ("optimistic", "Optimistic"),
        ]:
            s = scenarios[key]
            scenario_data.append(
                {
                    "Scenario": name,
                    "Monthly Cash Flow": format_currency(s["monthly_cash_flow"]),
                    "Annual Cash Flow": format_currency(s["annual_cash_flow"]),
                    "Annual ROI": format_percentage(s["roi"]),
                    "Monthly Rent": format_currency(s["monthly_rent"]),
                    "IRR": format_percentage(s["irr"]) if s["irr"] else "N/A",
                }
            )

        scenario_df = pd.DataFrame(scenario_data)
        buffer = export_to_excel(calc, scenarios, scenario_df)
        buffer.seek(0)
        return send_file(
            buffer,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name="RealEstateAnalyzer.xlsx",
        )
    except Exception as e:
        flash(f"Excel export failed: {e}")
        return redirect(url_for("landing"))


if __name__ == "__main__":
    app.run(debug=True)
