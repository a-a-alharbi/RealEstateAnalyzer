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