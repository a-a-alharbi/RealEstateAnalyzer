import os
from datetime import datetime
from typing import Dict, Any

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML
import matplotlib.pyplot as plt

from financial_calculator import FinancialCalculator
from helpers import (
    format_currency,
    format_percentage,
)


def _generate_charts(calc: FinancialCalculator, scenarios: Dict[str, Any], img_dir: str) -> list:
    os.makedirs(img_dir, exist_ok=True)
    charts = []
    years = list(range(1, calc.holding_period + 1))
    cumulative = {
        'Conservative': [scenarios['conservative']['annual_cash_flow'] * y for y in years],
        'Base': [scenarios['base']['annual_cash_flow'] * y for y in years],
        'Optimistic': [scenarios['optimistic']['annual_cash_flow'] * y for y in years],
    }

    fig, ax = plt.subplots(figsize=(6, 3))
    for name, values in cumulative.items():
        ax.plot(years, values, marker='o', label=name)
    ax.axhline(calc.get_total_initial_investment(), color='orange', linestyle='--', label='Break-even')
    ax.set_xlabel('Year')
    ax.set_ylabel('Cumulative Cash Flow (SAR)')
    ax.legend()
    path_cf = os.path.join(img_dir, 'cumulative_cash_flow.png')
    fig.tight_layout()
    fig.savefig(path_cf)
    plt.close(fig)
    charts.append(path_cf)

    fig, ax = plt.subplots(figsize=(4, 3))
    labels = ['Down Payment', 'Enhancement Costs', 'Loan Amount']
    values = [calc.down_payment, calc.enhancement_costs, calc.get_loan_amount()]
    colors_pie = ['#4285F4', '#34A853', '#FBBC04']
    ax.pie(values, labels=labels, colors=colors_pie, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    path_pie = os.path.join(img_dir, 'investment_breakdown.png')
    fig.tight_layout()
    fig.savefig(path_pie)
    plt.close(fig)
    charts.append(path_pie)

    fig, ax = plt.subplots(figsize=(4, 3))
    labels_bar = ['Conservative', 'Base', 'Optimistic']
    roi_values = [scenarios['conservative']['roi'], scenarios['base']['roi'], scenarios['optimistic']['roi']]
    colors_bar = ['#6C757D', '#4285F4', '#34A853']
    ax.bar(labels_bar, roi_values, color=colors_bar)
    ax.set_ylabel('ROI (%)')
    path_bar = os.path.join(img_dir, 'roi_comparison.png')
    fig.tight_layout()
    fig.savefig(path_bar)
    plt.close(fig)
    charts.append(path_bar)

    return charts


def generate_pdf_report(data: Dict[str, Any], output_path: str) -> str:
    """Generate a PDF report using HTML and WeasyPrint."""
    calc: FinancialCalculator = data['calculator']
    scenarios = data['scenarios']
    advanced = data['advanced_metrics']

    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_dir = os.path.join(base_dir, 'templates')
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(['html'])
    )
    template = env.get_template('report.html')

    img_dir = os.path.join(base_dir, 'static', 'report_images')
    charts = _generate_charts(calc, scenarios, img_dir)

    inv_summary = [
        {'label': 'Property Price', 'value': format_currency(calc.property_price)},
        {'label': 'Down Payment', 'value': format_currency(calc.down_payment)},
        {'label': 'Loan Amount', 'value': format_currency(calc.get_loan_amount())},
        {'label': 'Interest Rate', 'value': f"{calc.interest_rate:.2f}%"},
        {'label': 'Loan Term', 'value': f"{calc.loan_term} years"},
        {'label': 'Total Initial Investment', 'value': format_currency(calc.get_total_initial_investment())},
    ]

    adv_metrics = [
        {'label': 'DSCR', 'value': f"{advanced['dscr']:.2f}" if advanced['dscr'] != float('inf') else 'N/A'},
        {'label': 'Cash-on-Cash Return', 'value': format_percentage(advanced['cash_on_cash_return'])},
        {'label': 'Payback Period', 'value': f"{advanced['payback_period']:.1f} years" if advanced['payback_period'] != float('inf') else 'Never'},
        {'label': 'Cap Rate', 'value': format_percentage(advanced['cap_rate'])},
    ]

    scenario_rows = []
    for key, name in [('conservative', 'Conservative'), ('base', 'Base'), ('optimistic', 'Optimistic')]:
        s = scenarios[key]
        scenario_rows.append({
            'name': name,
            'monthly_rent': format_currency(s['monthly_rent']),
            'annual_cash_flow': format_currency(s['annual_cash_flow']),
            'roi': format_percentage(s['roi']),
            'irr': format_percentage(s['irr']) if s['irr'] is not None else 'N/A',
        })

    html_content = template.render(
        title='Real Estate Investment Analysis Report',
        date=datetime.now().strftime('%Y-%m-%d'),
        logo=None,
        investment_summary=inv_summary,
        advanced_metrics=adv_metrics,
        scenarios=scenario_rows,
        charts=[os.path.relpath(c, base_dir) for c in charts],
        css_path=os.path.relpath(os.path.join(base_dir, 'static', 'css', 'report.css'), base_dir)
    )

    HTML(string=html_content, base_url=base_dir).write_pdf(output_path)
    return output_path
