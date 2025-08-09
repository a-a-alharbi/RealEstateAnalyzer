from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.utils
import json
import math
import io
import os
import tempfile
from financial_calculator import FinancialCalculator
from utils import (
    format_currency, format_percentage, format_currency_with_color,
    format_percentage_with_color, export_to_excel, get_advanced_metrics
)
from report_generator import generate_pdf_report

app = Flask(__name__)

def sanitize_json_data(data):
    """
    Recursively sanitize data to handle infinity and NaN values for JSON serialization
    """
    if isinstance(data, dict):
        return {key: sanitize_json_data(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_json_data(item) for item in data]
    elif isinstance(data, float):
        if math.isnan(data) or math.isinf(data):
            return None
        return data
    else:
        return data

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

def clean_numeric_input(value):
    """Clean numeric input by removing commas and converting to float"""
    if isinstance(value, str):
        return float(value.replace(',', ''))
    return float(value)

@app.route('/calculate', methods=['POST'])
def calculate():
    """Process calculation and return results"""
    try:
        # Get form data
        data = request.get_json()
        print(f"Received data: {data}")  # Debug logging
        
        # Extract and clean parameters
        property_price = clean_numeric_input(data.get('property_price', 0))
        down_payment = clean_numeric_input(data.get('down_payment', 0))
        loan_term = int(data.get('loan_term', 30))
        interest_rate = clean_numeric_input(data.get('interest_rate', 0))
        interest_type = data.get('interest_type', 'apr')
        annual_rental_income = clean_numeric_input(data.get('base_monthly_rent', 0))  # This is actually annual income
        base_monthly_rent = annual_rental_income / 12  # Convert to monthly
        occupancy_rate = clean_numeric_input(data.get('occupancy_rate', 95))
        rent_growth = clean_numeric_input(data.get('rent_growth', 0))
        enhancement_costs = clean_numeric_input(data.get('enhancement_costs', 0))
        hoa_fees_annual = clean_numeric_input(data.get('hoa_fees_annual', 0))
        holding_period = int(data.get('holding_period', 10))
        resale_value = clean_numeric_input(data.get('resale_value', 0))
        
        print(f"Processed values: price={property_price}, down={down_payment}, annual_rent={annual_rental_income}, monthly_rent={base_monthly_rent}")  # Debug logging
        
        # Create calculator instance
        calc = FinancialCalculator(
            property_price=property_price,
            down_payment=down_payment,
            loan_term=loan_term,
            interest_rate=interest_rate,
            interest_type=interest_type,
            base_monthly_rent=base_monthly_rent,
            occupancy_rate=occupancy_rate,
            rent_growth=rent_growth,
            enhancement_costs=enhancement_costs,
            hoa_fees_annual=hoa_fees_annual,
            holding_period=holding_period,
            resale_value=resale_value
        )
        
        # Get scenario analysis
        scenarios = calc.get_scenario_analysis()
        
        # Get advanced metrics
        advanced_metrics = get_advanced_metrics(calc)
        
        # Prepare charts data
        charts_data = prepare_charts_data(calc, scenarios, advanced_metrics)
        
        # Format response
        response = {
            'success': True,
            'scenarios': scenarios,
            'advanced_metrics': advanced_metrics,
            'charts': charts_data,
            'calculator_data': {
                'total_investment': calc.get_total_initial_investment(),
                'loan_amount': calc.get_loan_amount(),
                'monthly_payment': calc.get_monthly_payment(),
                'total_interest': calc.get_total_interest(),
                'break_even_years': advanced_metrics['payback_period'],
                'occupancy_rate': calc.occupancy_rate,
                'hoa_fees_annual': calc.hoa_fees_annual
            }
        }
        
        # Sanitize the response to handle infinity and NaN values
        sanitized_response = sanitize_json_data(response)
        
        return jsonify(sanitized_response)
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in calculation: {str(e)}")
        print(f"Full traceback:\n{error_trace}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

def prepare_charts_data(calc, scenarios, advanced_metrics):
    """Prepare chart data for frontend"""
    
    # KPI Cards data
    kpi_data = {
        'monthly_cash_flow': scenarios['base']['monthly_cash_flow'],
        'annual_roi': scenarios['base']['roi'],
        'total_investment': calc.get_total_initial_investment(),
        'break_even_years': advanced_metrics['payback_period']
    }
    
    # Cash Flow Performance Chart (Area Chart)
    years = list(range(1, calc.holding_period + 1))
    cash_flow_data = {
        'years': years,
        'scenarios': {}
    }
    
    for scenario_key, scenario_name in [('conservative', 'Conservative'), ('base', 'Base'), ('optimistic', 'Optimistic')]:
        schedule = scenarios[scenario_key]['cash_flow_schedule']
        cumulative = []
        total = 0
        for cf in schedule:
            total += cf
            cumulative.append(total)
        cash_flow_data['scenarios'][scenario_name] = cumulative
    
    # Investment Breakdown (Donut Chart)
    investment_breakdown = {
        'labels': ['Down Payment', 'Enhancement Costs', 'Loan Amount'],
        'values': [calc.down_payment, calc.enhancement_costs, calc.get_loan_amount()],
        'colors': ['#4285F4', '#34A853', '#FBBC04']
    }
    
    # ROI Comparison (Bar Chart)
    roi_comparison = {
        'labels': ['Conservative', 'Base', 'Optimistic'],
        'values': [scenarios['conservative']['roi'], scenarios['base']['roi'], scenarios['optimistic']['roi']],
        'colors': ['#6C757D', '#4285F4', '#34A853']
    }
    
    return {
        'kpi_data': kpi_data,
        'cash_flow_data': cash_flow_data,
        'investment_breakdown': investment_breakdown,
        'roi_comparison': roi_comparison,
        'break_even_amount': calc.get_total_initial_investment()
    }

@app.route('/export_excel', methods=['POST'])
def export_excel():
    """Export analysis to Excel"""
    try:
        data = request.get_json()
        
        # Recreate calculator from data
        calc = create_calculator_from_data(data)
        scenarios = calc.get_scenario_analysis()
        
        # Create scenario DataFrame
        scenario_data = []
        for scenario_key, scenario_name in [('conservative', 'Conservative'), ('base', 'Base'), ('optimistic', 'Optimistic')]:
            scenario_data.append({
                'Scenario': scenario_name,
                'Monthly Cash Flow': format_currency(scenarios[scenario_key]['monthly_cash_flow']),
                'Annual Cash Flow': format_currency(scenarios[scenario_key]['annual_cash_flow']),
                'Annual ROI': format_percentage(scenarios[scenario_key]['roi']),
                'Monthly Rent': format_currency(scenarios[scenario_key]['monthly_rent']),
                'IRR': format_percentage(scenarios[scenario_key]['irr']) if scenarios[scenario_key]['irr'] else 'N/A'
            })
        
        scenario_df = pd.DataFrame(scenario_data)
        
        # Export to Excel
        excel_buffer = export_to_excel(calc, scenarios, scenario_df)
        
        return send_file(
            excel_buffer,
            as_attachment=True,
            download_name='investment_analysis.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/export_pdf', methods=['POST'])
def export_pdf():
    """Export analysis to PDF"""
    try:
        data = request.get_json()
        
        # Recreate calculator from data
        calc = create_calculator_from_data(data)
        scenarios = calc.get_scenario_analysis()
        advanced_metrics = get_advanced_metrics(calc)
        
        # Export to PDF using HTML + WeasyPrint
        tmp_dir = tempfile.gettempdir()
        pdf_path = os.path.join(tmp_dir, 'investment_analysis.pdf')
        generate_pdf_report({
            'calculator': calc,
            'scenarios': scenarios,
            'advanced_metrics': advanced_metrics
        }, pdf_path)

        return send_file(
            pdf_path,
            as_attachment=True,
            download_name='investment_analysis.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

def create_calculator_from_data(data):
    """Helper function to recreate calculator from form data"""
    # The form field 'base_monthly_rent' actually contains ANNUAL rental income
    # despite its misleading name (legacy from when it was monthly)
    annual_rental_income = clean_numeric_input(data.get('base_monthly_rent', 0))
    base_monthly_rent = annual_rental_income / 12  # Convert annual to monthly
    
    return FinancialCalculator(
        property_price=clean_numeric_input(data.get('property_price', 0)),
        down_payment=clean_numeric_input(data.get('down_payment', 0)),
        loan_term=int(data.get('loan_term', 30)),
        interest_rate=clean_numeric_input(data.get('interest_rate', 0)),
        interest_type=data.get('interest_type', 'apr'),
        base_monthly_rent=base_monthly_rent,  # This is now correctly monthly
        occupancy_rate=clean_numeric_input(data.get('occupancy_rate', 95)),
        rent_growth=clean_numeric_input(data.get('rent_growth', 0)),
        enhancement_costs=clean_numeric_input(data.get('enhancement_costs', 0)),
        hoa_fees_annual=clean_numeric_input(data.get('hoa_fees_annual', 0)),
        holding_period=int(data.get('holding_period', 10)),
        resale_value=clean_numeric_input(data.get('resale_value', 0))
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)