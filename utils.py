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
                'Conservative Cash Flow': scenarios['conservative']['cash_flow_schedule'][year-1],
                'Base Cash Flow': base_scenario['cash_flow_schedule'][year-1],
                'Optimistic Cash Flow': scenarios['optimistic']['cash_flow_schedule'][year-1],
                'Cumulative Conservative': sum(scenarios['conservative']['cash_flow_schedule'][:year]),
                'Cumulative Base': sum(base_scenario['cash_flow_schedule'][:year]),
                'Cumulative Optimistic': sum(scenarios['optimistic']['cash_flow_schedule'][:year])
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

def calculate_payback_period(total_initial_investment: float, annual_cash_flow: 'Union[float, list]') -> float:
    """Calculate payback period in years.
    Supports constant or variable annual cash flow.
    """
    from typing import Union

    if isinstance(annual_cash_flow, list):
        cumulative = 0.0
        for idx, cf in enumerate(annual_cash_flow, start=1):
            cumulative += cf
            if cumulative >= total_initial_investment:
                prev = cumulative - cf
                fraction = (total_initial_investment - prev) / cf if cf else 0
                return min(idx - 1 + fraction, 999.0)
        if not annual_cash_flow:
            return 999.0
        last_cf = annual_cash_flow[-1]
        if last_cf <= 0:
            return 999.0
        remaining = total_initial_investment - cumulative
        return min(len(annual_cash_flow) + remaining / last_cf, 999.0)
    else:
        if annual_cash_flow <= 0:
            return 999.0
        payback = total_initial_investment / annual_cash_flow
        return min(payback, 999.0)

def get_advanced_metrics(calculator) -> Dict[str, Any]:
    """
    Calculate advanced financial metrics for the investment.
    """
    base_scenario = calculator.get_scenario_analysis()['base']
    
    # Calculate metrics
    annual_debt_service = calculator.get_monthly_payment() * 12
    net_income_schedule = base_scenario['net_income_schedule']
    cash_flow_schedule = base_scenario['cash_flow_schedule']
    total_initial_investment = calculator.get_total_initial_investment()

    annual_net_income = net_income_schedule[0] if net_income_schedule else 0
    avg_cash_flow = sum(cash_flow_schedule) / len(cash_flow_schedule) if cash_flow_schedule else 0

    dscr = calculate_debt_service_coverage_ratio(annual_net_income, annual_debt_service)
    cash_on_cash = calculate_cash_on_cash_return(avg_cash_flow, total_initial_investment)
    payback_period = calculate_payback_period(total_initial_investment, cash_flow_schedule)
    cap_rate = calculate_cap_rate(annual_net_income, calculator.property_price)
    
    return {
        'dscr': dscr,
        'cash_on_cash_return': cash_on_cash,
        'payback_period': payback_period,
        'cap_rate': cap_rate,
        'annual_debt_service': annual_debt_service,
        'total_initial_investment': total_initial_investment
    }

