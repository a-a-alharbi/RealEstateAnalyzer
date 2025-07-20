import os
from datetime import datetime
from typing import Dict, Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

# 🔧 Set headless backend before importing pyplot
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from weasyprint import HTML
from financial_calculator import FinancialCalculator
from helpers import (
    format_currency,
    format_percentage,
)
from utils import get_risk_assessment


def _interpret_metric(label: str, value: float) -> str:
    """Return a simple interpretation for advanced metrics."""
    if label == 'DSCR':
        if value == float('inf'):
            return 'No debt service'
        if value < 1:
            return 'Below breakeven'
        elif value < 1.25:
            return 'Tight coverage'
        elif value < 1.5:
            return 'Healthy'
        else:
            return 'Strong'
    if label == 'Cash-on-Cash Return':
        if value < 5:
            return 'Low'
        elif value < 10:
            return 'Average'
        elif value < 15:
            return 'Good'
        else:
            return 'Excellent'
    if label == 'Payback Period':
        if value == float('inf'):
            return 'No payback'
        if value < 5:
            return 'Fast'
        elif value < 10:
            return 'Moderate'
        elif value < 20:
            return 'Slow'
        else:
            return 'Very slow'
    if label == 'Cap Rate':
        if value < 4:
            return 'Low yield'
        elif value < 6:
            return 'Moderate yield'
        else:
            return 'High yield'
    return ''


def _generate_charts(calc: FinancialCalculator, scenarios: Dict[str, Any], img_dir: str) -> list:
    os.makedirs(img_dir, exist_ok=True)
    charts = []
    years = list(range(1, calc.holding_period + 1))
    cumulative = {}
    for key, name in [('conservative', 'Conservative'), ('base', 'Base'), ('optimistic', 'Optimistic')]:
        total = 0
        cumulative[name] = []
        for cf in scenarios[key]['cash_flow_schedule']:
            total += cf
            cumulative[name].append(total)
        # pad to full length if needed
        if len(cumulative[name]) < len(years):
            cumulative[name].extend([total] * (len(years) - len(cumulative[name])))

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
        {'label': 'Interest Rate', 'value': f"{calc.interest_rate:.2f}% ({calc.interest_type.title()})"},
        {'label': 'Loan Term', 'value': f"{calc.loan_term} years"},
        {'label': 'Total Initial Investment', 'value': format_currency(calc.get_total_initial_investment())},
    ]

    adv_metrics = [
        {
            'label': 'DSCR',
            'value': f"{advanced['dscr']:.2f}" if advanced['dscr'] != float('inf') else 'N/A',
            'interpretation': _interpret_metric('DSCR', advanced['dscr']),
        },
        {
            'label': 'Cash-on-Cash Return',
            'value': format_percentage(advanced['cash_on_cash_return']),
            'interpretation': _interpret_metric('Cash-on-Cash Return', advanced['cash_on_cash_return']),
        },
        {
            'label': 'Payback Period',
            'value': f"{advanced['payback_period']:.1f} years" if advanced['payback_period'] != float('inf') else 'Never',
            'interpretation': _interpret_metric('Payback Period', advanced['payback_period']),
        },
        {
            'label': 'Cap Rate',
            'value': format_percentage(advanced['cap_rate']),
            'interpretation': _interpret_metric('Cap Rate', advanced['cap_rate']),
        },
    ]

    risk_assessment = get_risk_assessment(calc, scenarios)

    scenario_rows = []
    for key, name in [('conservative', 'Conservative'), ('base', 'Base'), ('optimistic', 'Optimistic')]:
        s = scenarios[key]
        scenario_rows.append({
            'name': name,
            'annual_rent': format_currency(s['monthly_rent'] * 12),
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
        risk_level=risk_assessment['risk_level'],
        risk_factors=risk_assessment['risk_factors'],
        recommendations=risk_assessment['recommendations'],
        css_path=os.path.relpath(os.path.join(base_dir, 'static', 'css', 'report.css'), base_dir)
    )

    HTML(string=html_content, base_url=base_dir).write_pdf(output_path)
    return output_path
