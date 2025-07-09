import io
from typing import Dict, Any
from financial_calculator import FinancialCalculator
from helpers import (
    format_currency,
    format_currency_with_color,
    format_percentage,
    format_percentage_with_color,
    format_number,
    format_number_with_unit,
)

# Heavy third-party libraries are imported lazily inside the functions that
# require them. This allows basic utilities to be used in environments where
# optional dependencies like pandas or reportlab are not installed.


def export_to_excel(calculator: FinancialCalculator, scenarios: Dict, scenario_df: 'pd.DataFrame') -> io.BytesIO:
    """
    Export the investment analysis to an Excel file.
    Returns a BytesIO buffer containing the Excel file.
    """
    # Import pandas lazily so that this module can be imported without the
    # dependency installed.  The export functions will raise an informative
    # error if pandas is unavailable.
    try:
        import pandas as pd  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dependency
        raise ImportError("pandas is required for export_to_excel") from exc

    buffer = io.BytesIO()
    
    # Type ignore to suppress the LSP warning - this is a known working pattern
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:  # type: ignore
        # Investment Summary Sheet
        summary = calculator.get_investment_summary()
        summary_data = {
            'Metric': [],
            'Value': []
        }
        
        # Property Information
        summary_data['Metric'].extend([
            'Property Price',
            'Down Payment',
            'Enhancement Costs',
            'Total Initial Investment',
            'Loan Amount',
            'Loan Term (Years)',
            'Interest Rate (%)',
            'Monthly Payment'
        ])
        
        summary_data['Value'].extend([
            format_currency(summary['property_price']),
            format_currency(summary['down_payment']),
            format_currency(calculator.enhancement_costs),
            format_currency(summary['total_initial_investment']),
            format_currency(summary['loan_amount']),
            str(calculator.loan_term),
            f"{calculator.interest_rate:.2f}%",
            format_currency(summary['monthly_payment'])
        ])
        
        # Rental Information
        summary_data['Metric'].extend([
            '',  # Empty row
            'Base Annual Rent',
            'Base Monthly Rent',
            'Occupancy Rate (%)',
            'Effective Monthly Rent',
            'Annual HOA Fees',
            'Monthly Cash Flow',
            'Annual Cash Flow'
        ])
        
        summary_data['Value'].extend([
            '',
            format_currency(summary['base_monthly_rent'] * 12),
            format_currency(summary['base_monthly_rent']),
            f"{calculator.occupancy_rate}%",
            format_currency(summary['effective_monthly_rent']),
            format_currency(calculator.hoa_fees_annual),
            format_currency(summary['monthly_cash_flow']),
            format_currency(summary['annual_cash_flow'])
        ])
        
        # Investment Returns
        summary_data['Metric'].extend([
            '',  # Empty row
            'Annual ROI (%)',
            'IRR (%)',
            'Holding Period (Years)',
            'Expected Resale Value',
            'Expected Capital Gain',
            'Total Interest Paid'
        ])
        
        summary_data['Value'].extend([
            '',
            format_percentage(summary['roi']),
            format_percentage(summary['irr']) if summary['irr'] is not None else 'N/A',
            str(summary['holding_period']),
            format_currency(summary['expected_resale_value']),
            format_currency(summary['expected_capital_gain']),
            format_currency(summary['total_interest'])
        ])
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Investment Summary', index=False)
        
        # Scenario Analysis Sheet
        scenario_df.to_excel(writer, sheet_name='Scenario Analysis', index=False)
        
        # Detailed Scenario Data
        detailed_scenarios = []
        for scenario_name, scenario_data in scenarios.items():
            detailed_scenarios.append({
                'Scenario': scenario_name.title(),
                'Monthly Rent': scenario_data['monthly_rent'],
                'Effective Monthly Rent': scenario_data['effective_monthly_rent'],
                'Monthly Cash Flow': scenario_data['monthly_cash_flow'],
                'Annual Net Income': scenario_data['annual_net_income'],
                'Annual Cash Flow': scenario_data['annual_cash_flow'],
                'ROI (%)': scenario_data['roi'],
                'IRR (%)': scenario_data['irr'] if scenario_data['irr'] is not None else 'N/A'
            })
        
        detailed_df = pd.DataFrame(detailed_scenarios)
        detailed_df.to_excel(writer, sheet_name='Detailed Scenarios', index=False)
        
        # Amortization Schedule (first 5 years)
        amortization = calculator.get_amortization_schedule(60)  # 5 years = 60 months
        amort_df = pd.DataFrame(amortization)
        
        # Format the amortization schedule
        if not amort_df.empty:
            amort_df['payment'] = amort_df['payment'].apply(lambda x: f"{x:.2f}")
            amort_df['principal'] = amort_df['principal'].apply(lambda x: f"{x:.2f}")
            amort_df['interest'] = amort_df['interest'].apply(lambda x: f"{x:.2f}")
            amort_df['balance'] = amort_df['balance'].apply(lambda x: f"{x:.2f}")
            
            # Rename columns for better readability
            amort_df.columns = ['Period', 'Payment ($)', 'Principal ($)', 'Interest ($)', 'Remaining Balance ($)']
            amort_df.to_excel(writer, sheet_name='Amortization (5 Years)', index=False)
        
        # Cash Flow Projections
        cash_flow_data = []
        for year in range(1, calculator.holding_period + 1):
            base_scenario = scenarios['base']
            cash_flow_data.append({
                'Year': year,
                'Conservative Cash Flow': scenarios['conservative']['annual_cash_flow'],
                'Base Cash Flow': base_scenario['annual_cash_flow'],
                'Optimistic Cash Flow': scenarios['optimistic']['annual_cash_flow'],
                'Cumulative Conservative': scenarios['conservative']['annual_cash_flow'] * year,
                'Cumulative Base': base_scenario['annual_cash_flow'] * year,
                'Cumulative Optimistic': scenarios['optimistic']['annual_cash_flow'] * year
            })
        
        cash_flow_df = pd.DataFrame(cash_flow_data)
        cash_flow_df.to_excel(writer, sheet_name='Cash Flow Projections', index=False)
    
    buffer.seek(0)
    return buffer

def calculate_cap_rate(annual_net_income: float, property_price: float) -> float:
    """
    Calculate capitalization rate (cap rate).
    Cap Rate = Annual Net Operating Income / Property Price
    """
    if property_price <= 0:
        return 0
    return (annual_net_income / property_price) * 100

def calculate_cash_on_cash_return(annual_cash_flow: float, total_cash_invested: float) -> float:
    """
    Calculate cash-on-cash return.
    Cash-on-Cash Return = Annual Pre-Tax Cash Flow / Total Cash Invested
    """
    if total_cash_invested <= 0:
        return 0
    return (annual_cash_flow / total_cash_invested) * 100

def calculate_debt_service_coverage_ratio(annual_net_income: float, annual_debt_service: float) -> float:
    """
    Calculate debt service coverage ratio.
    DSCR = Annual Net Operating Income / Annual Debt Service
    """
    if annual_debt_service <= 0:
        return float('inf') if annual_net_income > 0 else 0
    return annual_net_income / annual_debt_service

def get_risk_assessment(calculator: FinancialCalculator, scenarios: Dict) -> Dict[str, Any]:
    """
    Provide a risk assessment based on the investment metrics.
    """
    base_scenario = scenarios['base']
    conservative_scenario = scenarios['conservative']
    
    risk_factors = []
    risk_level = "Low"
    
    # Check cash flow
    if base_scenario['monthly_cash_flow'] < 0:
        risk_factors.append("Negative cash flow in base scenario")
        risk_level = "High"
    elif base_scenario['monthly_cash_flow'] < 200:
        risk_factors.append("Low cash flow margin")
        if risk_level == "Low":
            risk_level = "Medium"
    
    # Check conservative scenario
    if conservative_scenario['monthly_cash_flow'] < 0:
        risk_factors.append("Negative cash flow in conservative scenario")
        risk_level = "High"
    
    # Check ROI
    if base_scenario['roi'] < 5:
        risk_factors.append("Low ROI compared to market alternatives")
        if risk_level == "Low":
            risk_level = "Medium"
    
    # Check down payment ratio
    down_payment_ratio = (calculator.down_payment / calculator.property_price) * 100
    if down_payment_ratio < 15:
        risk_factors.append("Low down payment increases leverage risk")
        if risk_level == "Low":
            risk_level = "Medium"
    
    # Check occupancy rate sensitivity
    if calculator.occupancy_rate < 90:
        risk_factors.append("Low occupancy rate assumption increases vacancy risk")
        if risk_level == "Low":
            risk_level = "Medium"
    
    return {
        'risk_level': risk_level,
        'risk_factors': risk_factors,
        'recommendations': get_recommendations(calculator, scenarios, risk_level)
    }

def get_recommendations(calculator: FinancialCalculator, scenarios: Dict, risk_level: str) -> list:
    """
    Generate recommendations based on the analysis.
    """
    recommendations = []
    base_scenario = scenarios['base']
    
    if risk_level == "High":
        recommendations.append("Consider increasing down payment to improve cash flow")
        recommendations.append("Negotiate a lower purchase price or higher rental income")
        recommendations.append("Explore properties in different markets with better rent-to-price ratios")
    
    if base_scenario['roi'] < 8:
        recommendations.append("Compare with other investment options (stocks, bonds, REITs)")
    
    if calculator.occupancy_rate < 95:
        recommendations.append("Research local rental market to validate occupancy assumptions")
    
    if base_scenario['monthly_cash_flow'] < 500:
        recommendations.append("Build a larger cash reserve for unexpected expenses and vacancies")
    
    # Always include general recommendations
    recommendations.extend([
        "Conduct thorough due diligence on the property and neighborhood",
        "Consider hiring a property management company if you lack experience",
        "Regularly review and adjust rent to market rates",
        "Maintain adequate insurance coverage for the property"
    ])
    
    return recommendations

def calculate_payback_period(total_initial_investment: float, annual_cash_flow: float) -> float:
    """
    Calculate payback period in years.
    Payback Period = Total Initial Investment / Annual Cash Flow
    """
    if annual_cash_flow <= 0:
        return 999.0  # Use a large number instead of infinity for JSON compatibility
    
    payback = total_initial_investment / annual_cash_flow
    # Cap at 999 years for extremely long payback periods
    return min(payback, 999.0)

def get_advanced_metrics(calculator) -> Dict[str, Any]:
    """
    Calculate advanced financial metrics for the investment.
    """
    base_scenario = calculator.get_scenario_analysis()['base']
    
    # Calculate metrics
    annual_debt_service = calculator.get_monthly_payment() * 12
    annual_net_income = base_scenario['annual_net_income']
    annual_cash_flow = base_scenario['annual_cash_flow']
    total_initial_investment = calculator.get_total_initial_investment()
    
    dscr = calculate_debt_service_coverage_ratio(annual_net_income, annual_debt_service)
    cash_on_cash = calculate_cash_on_cash_return(annual_cash_flow, total_initial_investment)
    payback_period = calculate_payback_period(total_initial_investment, annual_cash_flow)
    cap_rate = calculate_cap_rate(annual_net_income, calculator.property_price)
    
    return {
        'dscr': dscr,
        'cash_on_cash_return': cash_on_cash,
        'payback_period': payback_period,
        'cap_rate': cap_rate,
        'annual_debt_service': annual_debt_service,
        'total_initial_investment': total_initial_investment
    }

def export_to_pdf(calculator: FinancialCalculator, scenarios: Dict, advanced_metrics: Dict) -> io.BytesIO:
    """
    Export the investment analysis to a professional PDF report.
    Returns a BytesIO buffer containing the PDF file.
    """
    # Import heavy PDF generation libraries lazily. This keeps the module
    # importable even when ReportLab or matplotlib are not installed.
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import (
            SimpleDocTemplate,
            Table,
            TableStyle,
            Paragraph,
            Spacer,
            Image,
        )
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.graphics.shapes import Drawing
        from reportlab.graphics.charts.barcharts import VerticalBarChart
        from reportlab.graphics.charts.piecharts import Pie
        from reportlab.lib.colors import HexColor
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('Agg')
    except Exception as exc:  # pragma: no cover - optional dependency
        raise ImportError("reportlab and matplotlib are required for export_to_pdf") from exc

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    # Build story content
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.darkblue,
        alignment=1  # Center alignment
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12,
        textColor=colors.darkblue
    )
    
    # Title
    story.append(Paragraph("Real Estate Investment Analysis Report", title_style))
    story.append(Spacer(1, 20))
    
    # Property Summary
    story.append(Paragraph("Property Investment Summary", heading_style))
    
    property_data = [
        ['Property Price', format_currency(calculator.property_price)],
        ['Down Payment', f"{format_currency(calculator.down_payment)} ({(calculator.down_payment/calculator.property_price)*100:.1f}%)"],
        ['Loan Amount', format_currency(calculator.get_loan_amount())],
        ['Interest Rate', f"{calculator.interest_rate:.2f}%"],
        ['Loan Term', f"{calculator.loan_term} years"],
        ['Monthly Payment', format_currency(calculator.get_monthly_payment())],
        ['Enhancement Costs', format_currency(calculator.enhancement_costs)],
        ['Total Initial Investment', format_currency(calculator.get_total_initial_investment())],
    ]
    
    property_table = Table(property_data, colWidths=[3*inch, 2*inch])
    property_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(property_table)
    story.append(Spacer(1, 20))
    
    # Advanced Metrics Section
    story.append(Paragraph("Advanced Financial Metrics", heading_style))
    
    metrics_data = [
        ['Metric', 'Value', 'Interpretation'],
        ['Debt Service Coverage Ratio (DSCR)', 
         f"{advanced_metrics['dscr']:.2f}" if advanced_metrics['dscr'] != float('inf') else "N/A",
         "Good: >1.25, Acceptable: >1.0"],
        ['Cash-on-Cash Return', 
         format_percentage(advanced_metrics['cash_on_cash_return']),
         "Target: >8-12% annually"],
        ['Payback Period', 
         f"{advanced_metrics['payback_period']:.1f} years" if advanced_metrics['payback_period'] != float('inf') else "Never",
         "Good: <10-15 years"],
        ['Capitalization Rate', 
         format_percentage(advanced_metrics['cap_rate']),
         "Market dependent: 4-12%"],
    ]
    
    metrics_table = Table(metrics_data, colWidths=[2.5*inch, 1.5*inch, 2*inch])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))
    
    story.append(metrics_table)
    story.append(Spacer(1, 20))
    
    # Scenario Analysis
    story.append(Paragraph("Scenario Analysis", heading_style))
    
    scenario_data = [
        ['Scenario', 'Monthly Rent', 'Annual Cash Flow', 'ROI (%)', 'IRR (%)'],
    ]
    
    for scenario_name, scenario in scenarios.items():
        scenario_data.append([
            scenario_name.title(),
            format_currency(scenario['monthly_rent']),
            format_currency(scenario['annual_cash_flow']),
            format_percentage(scenario['roi']),
            format_percentage(scenario['irr']) if scenario['irr'] is not None else 'N/A'
        ])
    
    scenario_table = Table(scenario_data, colWidths=[1.2*inch, 1.3*inch, 1.3*inch, 1*inch, 1*inch])
    scenario_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))
    
    story.append(scenario_table)
    story.append(Spacer(1, 20))
    
    # Investment Timeline
    story.append(Paragraph("Investment Timeline Analysis", heading_style))
    
    base_scenario = scenarios['base']
    timeline_data = [
        ['Year', 'Annual Cash Flow', 'Cumulative Cash Flow'],
    ]
    
    cumulative = 0
    for year in range(1, min(calculator.holding_period + 1, 11)):  # Max 10 years for table
        annual_cf = base_scenario['annual_cash_flow']
        cumulative += annual_cf
        timeline_data.append([
            str(year),
            format_currency(annual_cf),
            format_currency(cumulative)
        ])
    
    timeline_table = Table(timeline_data, colWidths=[1*inch, 2*inch, 2*inch])
    timeline_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkorange),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightyellow),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))
    
    story.append(timeline_table)
    story.append(Spacer(1, 20))
    
    # Risk Assessment
    risk_assessment = get_risk_assessment(calculator, scenarios)
    story.append(Paragraph("Risk Assessment", heading_style))
    
    risk_color = colors.green if risk_assessment['risk_level'] == 'Low' else \
                colors.orange if risk_assessment['risk_level'] == 'Medium' else colors.red
    
    story.append(Paragraph(f"<font color='{risk_color}'>Risk Level: {risk_assessment['risk_level']}</font>", 
                          styles['Normal']))
    story.append(Spacer(1, 10))
    
    if risk_assessment['risk_factors']:
        story.append(Paragraph("Risk Factors:", styles['Heading3']))
        for factor in risk_assessment['risk_factors']:
            story.append(Paragraph(f"• {factor}", styles['Normal']))
        story.append(Spacer(1, 10))
    
    # Recommendations
    story.append(Paragraph("Recommendations", heading_style))
    for i, recommendation in enumerate(risk_assessment['recommendations'][:6], 1):  # Limit to 6
        story.append(Paragraph(f"{i}. {recommendation}", styles['Normal']))
    
    story.append(Spacer(1, 20))
    
    # Footer
    story.append(Paragraph("Report generated by Real Estate Investment Evaluator", 
                          styles['Normal']))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer
