import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
from financial_calculator import FinancialCalculator
from utils import format_currency, format_percentage, format_currency_with_color, format_percentage_with_color, export_to_excel, get_advanced_metrics, export_to_pdf

# Page configuration
st.set_page_config(
    page_title="Real Estate Investment Evaluator",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Modern CSS styling
st.markdown("""
<style>
    /* Main container styling */
    .main {
        background-color: #f8f9fa;
    }
    
    /* Modern header */
    .hero-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 3rem 2rem;
        border-radius: 20px;
        margin: -1rem -1rem 2rem -1rem;
        text-align: center;
        box-shadow: 0 10px 40px rgba(0,0,0,0.15);
    }
    
    .hero-section h1 {
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 1rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    
    .hero-section p {
        font-size: 1.2rem;
        opacity: 0.95;
        max-width: 600px;
        margin: 0 auto;
    }
    
    /* Modern cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.08);
        border: 1px solid rgba(255,255,255,0.3);
        margin-bottom: 1.5rem;
    }
    
    /* Metric tiles redesign */
    .metric-tile {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        border: 1px solid rgba(0,0,0,0.05);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .metric-tile::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 4px;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    
    .metric-tile.positive-tile::after {
        background: linear-gradient(90deg, #48bb78 0%, #38a169 100%);
    }
    
    .metric-tile.negative-tile::after {
        background: linear-gradient(90deg, #f56565 0%, #e53e3e 100%);
    }
    
    .metric-tile.warning-tile::after {
        background: linear-gradient(90deg, #ed8936 0%, #dd6b20 100%);
    }
    
    .metric-tile:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 24px rgba(0,0,0,0.15);
    }
    
    .metric-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1a202c;
        margin-bottom: 0.5rem;
        font-family: 'Inter', sans-serif;
    }
    
    .metric-label {
        font-size: 0.875rem;
        color: #718096;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 600;
    }
    
    /* Chart styling */
    .chart-tile {
        background: white;
        border-radius: 20px;
        padding: 1.5rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        margin-bottom: 1.5rem;
    }
    
    .chart-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #2d3748;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .chart-title::before {
        content: '';
        width: 4px;
        height: 24px;
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
        border-radius: 2px;
    }
    
    /* Section headers */
    .section-divider {
        margin: 3rem 0 2rem 0;
        text-align: center;
        position: relative;
    }
    
    .section-divider h2 {
        font-size: 1.875rem;
        font-weight: 700;
        color: #2d3748;
        background: white;
        display: inline-block;
        padding: 0 2rem;
        position: relative;
        z-index: 1;
    }
    
    .section-divider::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, #e2e8f0, transparent);
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #2d3748 0%, #1a202c 100%);
    }
    
    /* Sidebar text - but not radio buttons */
    section[data-testid="stSidebar"] > div > div > div > div:not(.stRadio) label,
    section[data-testid="stSidebar"] > div > div > div > div:not(.stRadio) p,
    section[data-testid="stSidebar"] > div > div > div > div:not(.stRadio) span,
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #f7fafc !important;
    }
    
    section[data-testid="stSidebar"] .stTextInput label,
    section[data-testid="stSidebar"] .stNumberInput label,
    section[data-testid="stSidebar"] .stSlider label,
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] div[class*="stMarkdown"] {
        color: #f7fafc !important;
        font-weight: 500;
    }
    
    /* Sidebar subheaders */
    section[data-testid="stSidebar"] h2 {
        color: #ffffff !important;
        font-size: 1.25rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid rgba(255,255,255,0.2);
    }
    
    /* Radio button styling */
    section[data-testid="stSidebar"] .stRadio > div > label {
        color: #f7fafc !important;
    }
    
    /* Radio button specific styling */
    section[data-testid="stSidebar"] .stRadio > label {
        color: #f7fafc !important;
    }
    
    /* Radio button options */
    section[data-testid="stSidebar"] [data-baseweb="radio"] p,
    section[data-testid="stSidebar"] [data-baseweb="radio"] span {
        color: #94a3b8 !important;
    }
    
    section[data-testid="stSidebar"] [data-baseweb="radio"][aria-checked="true"] p,
    section[data-testid="stSidebar"] [data-baseweb="radio"][aria-checked="true"] span {
        color: #ffffff !important;
        font-weight: 600;
    }
    
    /* Radio button hover state */
    section[data-testid="stSidebar"] [data-baseweb="radio"]:hover p,
    section[data-testid="stSidebar"] [data-baseweb="radio"]:hover span {
        color: #cbd5e0 !important;
    }
    

    
    /* Input field styling in sidebar */
    section[data-testid="stSidebar"] input {
        background-color: white !important;
        color: #2d3748 !important;
    }
    
    /* Select box styling in sidebar */
    section[data-testid="stSidebar"] select {
        background-color: white !important;
        color: #2d3748 !important;
    }
    
    /* Specific fix for radio button text - excluding them from white text override */
    [data-testid="stSidebar"] .stRadio [role="radio"] p {
        color: #cbd5e0 !important;
    }
    
    [data-testid="stSidebar"] .stRadio [role="radio"][aria-checked="true"] p {
        color: #ffffff !important;
        font-weight: 600;
    }
    
    /* Fix for BaseWeb radio components - most specific targeting */
    [data-testid="stSidebar"] [data-baseweb="radio"] > div:last-child {
        color: #94a3b8 !important;
    }
    
    [data-testid="stSidebar"] [data-baseweb="radio"][aria-checked="true"] > div:last-child {
        color: #ffffff !important;
        font-weight: 600;
    }
    
    /* Additional targeting for radio text */
    section[data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] p {
        color: #94a3b8 !important;
    }
    
    section[data-testid="stSidebar"] .stRadio [aria-checked="true"] [data-testid="stMarkdownContainer"] p {
        color: #ffffff !important;
        font-weight: 600;
    }
    
    /* Input fields */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {
        border-radius: 10px;
        border: 2px solid #e2e8f0;
        padding: 0.75rem 1rem;
        font-size: 1rem;
        transition: all 0.3s ease;
        background: white;
    }
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        outline: none;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
    }
    
    /* Download buttons */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
        color: white;
        border: none;
        border-radius: 10px;
        font-weight: 600;
        padding: 0.75rem 1.5rem;
    }
    
    .stDownloadButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(72, 187, 120, 0.3);
    }
    
    /* Info boxes */
    .info-box {
        background: linear-gradient(135deg, #e6f7ff 0%, #bae7ff 100%);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #1890ff;
    }
    
    .warning-box {
        background: linear-gradient(135deg, #fff7e6 0%, #ffe7ba 100%);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #fa8c16;
    }
    
    .success-box {
        background: linear-gradient(135deg, #f6ffed 0%, #d9f7be 100%);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #52c41a;
    }
    
    /* Tables */
    .dataframe {
        border: none !important;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    }
    
    .dataframe thead tr th {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.875rem;
        letter-spacing: 0.5px;
        padding: 1rem !important;
    }
    
    .dataframe tbody tr {
        border-bottom: 1px solid #e2e8f0;
    }
    
    .dataframe tbody tr:hover {
        background-color: #f7fafc;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .viewerBadge_container__1QSob {display: none;}
    
    /* Responsive */
    @media (max-width: 768px) {
        .hero-section h1 {
            font-size: 2rem;
        }
        
        .metric-value {
            font-size: 1.5rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'calculator' not in st.session_state:
    st.session_state.calculator = None

# Modern hero section
st.markdown("""
<div class="hero-section">
    <h1>🏠 Real Estate Investment Evaluator</h1>
    <p>Make informed property investment decisions with advanced financial analytics and scenario modeling</p>
</div>
""", unsafe_allow_html=True)

# Modern Sidebar
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <h2 style="color: white; margin: 0;">Property Details</h2>
        <p style="color: #cbd5e0; font-size: 0.9rem; margin-top: 0.5rem;">Enter your investment parameters</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Property Information
    st.subheader("Property Information")
    property_price = st.number_input(
        "Property Price (SAR)",
        min_value=1000,
        value=1875000,  # Approximately 500k USD in SAR
        step=5000,
        help="Total purchase price of the property in Saudi Riyals",
        format="%d"
    )
    st.caption(f"Property Price: SAR {property_price:,}")
    
    enhancement_costs = st.number_input(
        "Property Enhancement Costs (SAR)",
        min_value=0,
        value=37500,  # Approximately 10k USD in SAR
        step=2500,
        help="One-time renovation, improvement, or enhancement costs",
        format="%d"
    )
    if enhancement_costs > 0:
        st.caption(f"Enhancement Costs: SAR {enhancement_costs:,}")
    
    hoa_fees_annual = st.number_input(
        "Annual HOA Fees (SAR)",
        min_value=0,
        value=0,
        step=500,
        help="Homeowners Association fees per year (can be zero)",
        format="%d"
    )
    if hoa_fees_annual > 0:
        st.caption(f"Annual HOA Fees: SAR {hoa_fees_annual:,}")
    
    # Financing Details
    st.subheader("Financing Details")
    down_payment_type = st.radio(
        "Down Payment Type",
        ["Percentage", "Fixed Amount"]
    )
    
    if down_payment_type == "Percentage":
        down_payment_pct = st.slider(
            "Down Payment (%)",
            min_value=5,
            max_value=50,
            value=20,
            step=1
        )
        down_payment = property_price * (down_payment_pct / 100)
        st.caption(f"Down Payment: SAR {down_payment:,.0f} ({down_payment_pct}%)")
    else:
        down_payment = st.number_input(
            "Down Payment (SAR)",
            min_value=1000,
            value=375000,  # Approximately 100k USD in SAR
            step=5000,
            format="%d"
        )
        st.caption(f"Down Payment: SAR {down_payment:,}")
        down_payment_pct = (down_payment / property_price) * 100
    
    loan_term = st.selectbox(
        "Loan Term (Years)",
        [15, 20, 25, 30],
        index=3
    )
    
    interest_rate = st.number_input(
        "Annual Interest Rate (%)",
        min_value=0.1,
        max_value=15.0,
        value=6.5,
        step=0.1,
        format="%.2f"
    )
    
    # Rental Information
    st.subheader("Rental Information")
    base_annual_rent = st.number_input(
        "Base Annual Rent (SAR)",
        min_value=1000,
        value=135000,  # Approximately 36k USD in SAR (3k monthly)
        step=2500,
        help="Expected annual rental income",
        format="%d"
    )
    st.caption(f"Annual Rent: SAR {base_annual_rent:,} (Monthly: SAR {base_annual_rent/12:,.0f})")
    
    # Convert to monthly for internal calculations
    base_monthly_rent = base_annual_rent / 12
    
    occupancy_rate = st.slider(
        "Occupancy Rate (%)",
        min_value=50,
        max_value=100,
        value=95,
        step=1,
        help="Expected percentage of time property will be occupied"
    )
    
    # Investment Horizon
    st.subheader("Investment Horizon")
    holding_period = st.number_input(
        "Holding Period (Years)",
        min_value=1,
        max_value=30,
        value=10,
        step=1,
        help="How long you plan to hold the property"
    )
    
    resale_value = st.number_input(
        "Expected Resale Value (SAR)",
        min_value=1000,
        value=int(property_price * 1.3),
        step=5000,
        help="Expected property value when selling",
        format="%d"
    )
    st.caption(f"Expected Resale Value: SAR {resale_value:,}")

# Calculate button
if st.sidebar.button("Calculate Investment Metrics", type="primary"):
    # Create calculator instance
    calc = FinancialCalculator(
        property_price=property_price,
        down_payment=down_payment,
        loan_term=loan_term,
        interest_rate=interest_rate,
        base_monthly_rent=base_monthly_rent,
        occupancy_rate=occupancy_rate,
        enhancement_costs=enhancement_costs,
        hoa_fees_annual=hoa_fees_annual,
        holding_period=holding_period,
        resale_value=resale_value
    )
    
    st.session_state.calculator = calc

# Display results if calculator exists
if st.session_state.calculator:
    calc = st.session_state.calculator
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:

        
        # Basic loan information
        loan_amount = calc.get_loan_amount()
        monthly_payment = calc.get_monthly_payment()
        total_interest = calc.get_total_interest()
        total_initial_investment = calc.get_total_initial_investment()
        
        # Add Property Details alongside Investment Overview
        prop_col1, prop_col2 = st.columns(2)
        
        with prop_col1:
            # Investment Overview (existing metrics)
            st.markdown("""
            <div class="section-divider" style="margin: 0 0 1rem 0;">
                <h2>💰 Investment Overview</h2>
            </div>
            """, unsafe_allow_html=True)
            
            metric_col1, metric_col2 = st.columns(2)
            metric_col3, metric_col4 = st.columns(2)
            
            with metric_col1:
                st.markdown(f"""
                <div class="metric-tile">
                    <div class="metric-value">{format_currency(loan_amount)}</div>
                    <div class="metric-label">Loan Amount</div>
                </div>
                """, unsafe_allow_html=True)
            
            with metric_col2:
                st.markdown(f"""
                <div class="metric-tile">
                    <div class="metric-value">{format_currency(monthly_payment)}</div>
                    <div class="metric-label">Monthly Payment</div>
                </div>
                """, unsafe_allow_html=True)
            
            with metric_col3:
                st.markdown(f"""
                <div class="metric-tile warning-tile">
                    <div class="metric-value">{format_currency(total_interest)}</div>
                    <div class="metric-label">Total Interest</div>
                </div>
                """, unsafe_allow_html=True)
            
            with metric_col4:
                st.markdown(f"""
                <div class="metric-tile">
                    <div class="metric-value">{format_currency(total_initial_investment)}</div>
                    <div class="metric-label">Initial Investment</div>
                </div>
                """, unsafe_allow_html=True)
        
        with prop_col2:
            # Property Details
            st.markdown("""
            <div class="section-divider" style="margin: 0 0 1rem 0;">
                <h2>📋 Property Details</h2>
            </div>
            """, unsafe_allow_html=True)
            
            base_scenario = calc.get_scenario_analysis()['base']
            
            st.markdown(f"""
            <div class="glass-card" style="padding: 1.5rem;">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                    <div>
                        <div style="color: #718096; font-size: 0.875rem; margin-bottom: 4px;">Property Price</div>
                        <div style="font-size: 1.125rem; font-weight: 600; color: #2d3748;">{format_currency(calc.property_price)}</div>
                    </div>
                    <div>
                        <div style="color: #718096; font-size: 0.875rem; margin-bottom: 4px;">Down Payment</div>
                        <div style="font-size: 1.125rem; font-weight: 600; color: #2d3748;">{format_currency(calc.down_payment)} ({down_payment_pct:.0f}%)</div>
                    </div>
                    <div>
                        <div style="color: #718096; font-size: 0.875rem; margin-bottom: 4px;">Loan Amount</div>
                        <div style="font-size: 1.125rem; font-weight: 600; color: #2d3748;">{format_currency(loan_amount)}</div>
                    </div>
                    <div>
                        <div style="color: #718096; font-size: 0.875rem; margin-bottom: 4px;">Monthly Payment</div>
                        <div style="font-size: 1.125rem; font-weight: 600; color: #2d3748;">{format_currency(monthly_payment)}</div>
                    </div>
                    <div>
                        <div style="color: #718096; font-size: 0.875rem; margin-bottom: 4px;">Annual Rent</div>
                        <div style="font-size: 1.125rem; font-weight: 600; color: #2d3748;">{format_currency(base_scenario['monthly_rent'] * 12)}</div>
                    </div>
                    <div>
                        <div style="color: #718096; font-size: 0.875rem; margin-bottom: 4px;">Holding Period</div>
                        <div style="font-size: 1.125rem; font-weight: 600; color: #2d3748;">{calc.holding_period} years</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Modern Scenario Analysis Section
        st.markdown("""
        <div class="section-divider">
            <h2>🎯 Scenario Analysis</h2>
        </div>
        """, unsafe_allow_html=True)
        
        scenarios = calc.get_scenario_analysis()
        
        # Create modern scenario tiles
        scenario_col1, scenario_col2, scenario_col3 = st.columns(3)
        
        scenario_configs = [
            ('conservative', 'Conservative', scenario_col1, '#e74c3c'),
            ('base', 'Base', scenario_col2, '#3498db'),
            ('optimistic', 'Optimistic', scenario_col3, '#27ae60')
        ]
        
        for scenario_key, scenario_name, col, color in scenario_configs:
            scenario = scenarios[scenario_key]
            cash_flow_class = "positive-tile" if scenario['monthly_cash_flow'] >= 0 else "negative-tile"
            
            with col:
                st.markdown(f"""
                <div class="metric-tile {cash_flow_class}" style="border-left-color: {color};">
                    <div style="text-align: center; margin-bottom: 15px;">
                        <h4 style="margin: 0; color: {color};">{scenario_name}</h4>
                    </div>
                    <div style="margin-bottom: 10px;">
                        <div style="font-size: 16px; font-weight: bold; color: #2c3e50;">
                            {format_currency(scenario['monthly_cash_flow'])}
                        </div>
                        <div style="font-size: 12px; color: #7f8c8d;">Monthly Cash Flow</div>
                    </div>
                    <div style="margin-bottom: 10px;">
                        <div style="font-size: 16px; font-weight: bold; color: #2c3e50;">
                            {format_currency(scenario['annual_cash_flow'])}
                        </div>
                        <div style="font-size: 12px; color: #7f8c8d;">Annual Cash Flow</div>
                    </div>
                    <div style="margin-bottom: 10px;">
                        <div style="font-size: 16px; font-weight: bold; color: #2c3e50;">
                            {format_percentage(scenario['roi'])}
                        </div>
                        <div style="font-size: 12px; color: #7f8c8d;">Annual ROI</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # Detailed comparison table (smaller, below tiles)
        st.subheader("📋 Detailed Comparison")
        scenario_data = {
            'Scenario': ['Conservative', 'Base', 'Optimistic'],
            'Annual Rent': [format_currency(s['monthly_rent'] * 12) for s in scenarios.values()],
            'Annual Cash Flow': [format_currency(s['annual_cash_flow']) for s in scenarios.values()],
            'ROI (%)': [format_percentage(s['roi']) for s in scenarios.values()],
            'IRR (%)': [format_percentage(s['irr']) if s['irr'] is not None else 'N/A' for s in scenarios.values()]
        }
        
        scenario_df = pd.DataFrame(scenario_data)
        
        # Function to style negative values in red with parentheses
        def style_negative_values(val):
            if isinstance(val, str):
                if 'SAR (' in val:  # Check if it's already formatted as negative
                    return 'color: red'
                elif 'SAR ' in val and val.replace('SAR ', '').replace(',', '').replace('-', '').isdigit():
                    # Check if the numeric part is negative
                    num_str = val.replace('SAR ', '').replace(',', '')
                    if num_str.startswith('-'):
                        return 'color: red'
            return ''
        
        # Apply styling to the dataframe
        styled_df = scenario_df.style.map(style_negative_values)
        
        st.dataframe(styled_df, use_container_width=True)
        
        # Enhanced Financial Dashboard Section
        st.markdown("""
        <div class="section-divider">
            <h2>📈 Financial Analysis Dashboard</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Create separate charts for better clarity
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            # Annual Cash Flow Chart
            st.markdown("""
            <div class="chart-tile">
                <div class="chart-title">💰 Annual Cash Flow by Scenario</div>
            """, unsafe_allow_html=True)
            cash_flow_data = {
                'Scenario': ['Conservative', 'Base', 'Optimistic'],
                'Annual Cash Flow': [scenarios[s]['annual_cash_flow'] for s in ['conservative', 'base', 'optimistic']]
            }
            cash_flow_df = pd.DataFrame(cash_flow_data)
            
            # Create a more informative bar chart
            fig_cash = px.bar(
                cash_flow_df, 
                x='Scenario', 
                y='Annual Cash Flow',
                title="",
                color='Annual Cash Flow',
                color_continuous_scale=['red', 'yellow', 'green'],
                text='Annual Cash Flow'
            )
            
            # Format text on bars - remove decimals
            fig_cash.update_traces(
                texttemplate='SAR %{text:,.0f}',
                textposition='outside'
            )
            
            fig_cash.update_layout(
                showlegend=False,
                yaxis_title="Annual Cash Flow (SAR)",
                xaxis_title="Investment Scenario",
                height=400,
                margin=dict(t=20)
            )
            
            # Format y-axis to show values without decimals
            fig_cash.update_yaxes(tickformat=",.0f")
            
            # Add zero line for reference
            fig_cash.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.5)
            
            st.plotly_chart(fig_cash, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col_chart2:
            # ROI Comparison Chart
            st.markdown("""
            <div class="chart-tile">
                <div class="chart-title">📊 Return on Investment Comparison</div>
            """, unsafe_allow_html=True)
            roi_data = {
                'Scenario': ['Conservative', 'Base', 'Optimistic'],
                'ROI (%)': [scenarios[s]['roi'] for s in ['conservative', 'base', 'optimistic']]
            }
            roi_df = pd.DataFrame(roi_data)
            
            fig_roi = px.bar(
                roi_df,
                x='Scenario',
                y='ROI (%)',
                title="",
                color='ROI (%)',
                color_continuous_scale=['red', 'yellow', 'green'],
                text='ROI (%)'
            )
            
            fig_roi.update_traces(
                texttemplate='%{text:.0f}%',
                textposition='outside'
            )
            
            fig_roi.update_layout(
                showlegend=False,
                yaxis_title="Return on Investment (%)",
                xaxis_title="Investment Scenario",
                height=400,
                margin=dict(t=20)
            )
            
            # Format y-axis to show percentages without decimals
            fig_roi.update_yaxes(tickformat=".0f")
            
            # Add benchmark lines
            fig_roi.add_hline(y=5, line_dash="dot", line_color="orange", 
                             annotation_text="Market Benchmark (5%)", annotation_position="top right")
            fig_roi.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.5)
            
            st.plotly_chart(fig_roi, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Cumulative Cash Flow Analysis
        st.markdown("""
        <div class="chart-tile">
            <div class="chart-title">📈 Long-term Cash Flow Projections</div>
        """, unsafe_allow_html=True)
        
        # Create cumulative cash flow chart
        years = list(range(1, calc.holding_period + 1))
        cumulative_data = []
        
        for year in years:
            for scenario_key, scenario_name in [('conservative', 'Conservative'), ('base', 'Base'), ('optimistic', 'Optimistic')]:
                cumulative_cash_flow = scenarios[scenario_key]['annual_cash_flow'] * year
                cumulative_data.append({
                    'Year': year,
                    'Scenario': scenario_name,
                    'Cumulative Cash Flow': cumulative_cash_flow
                })
        
        cumulative_df = pd.DataFrame(cumulative_data)
        
        fig_cumulative = px.line(
            cumulative_df,
            x='Year',
            y='Cumulative Cash Flow',
            color='Scenario',
            title=f"Cumulative Cash Flow Over {calc.holding_period} Years",
            markers=True,
            line_shape='linear'
        )
        
        fig_cumulative.update_layout(
            yaxis_title="Cumulative Cash Flow (SAR)",
            xaxis_title="Investment Year",
            height=450,
            hovermode='x unified'
        )
        
        # Format y-axis to show values without decimals
        fig_cumulative.update_yaxes(tickformat=",.0f")
        
        # Add zero line
        fig_cumulative.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.5)
        
        # Add break-even amount horizontal line
        break_even_amount = calc.get_total_initial_investment()
        fig_cumulative.add_hline(
            y=break_even_amount, 
            line_dash="dot", 
            line_color="orange", 
            opacity=0.7,
            annotation_text=f"Break-Even: {format_currency(break_even_amount)}",
            annotation_position="top right"
        )
        
        st.plotly_chart(fig_cumulative, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Investment Breakdown Chart with Tiles
        col_breakdown1, col_breakdown2 = st.columns(2)
        
        with col_breakdown1:
            st.markdown("""
            <div class="chart-tile">
                <div class="chart-title">💰 Investment Breakdown</div>
            """, unsafe_allow_html=True)
            
            # Create pie chart for initial investment
            investment_breakdown = {
                'Component': ['Down Payment', 'Enhancement Costs', 'Loan Amount'],
                'Amount': [calc.down_payment, calc.enhancement_costs, calc.get_loan_amount()]
            }
            investment_df = pd.DataFrame(investment_breakdown)
            
            fig_pie = px.pie(
                investment_df,
                values='Amount',
                names='Component',
                title="",
                color_discrete_sequence=['#ff9999', '#66b3ff', '#99ff99']
            )
            
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            fig_pie.update_layout(height=400, margin=dict(t=20))
            
            st.plotly_chart(fig_pie, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col_breakdown2:
            st.markdown("""
            <div class="chart-tile">
                <div class="chart-title">📈 Monthly Income vs Expenses</div>
            """, unsafe_allow_html=True)
            
            base_scenario = scenarios['base']
            monthly_breakdown = {
                'Category': ['Rental Income', 'Mortgage Payment', 'HOA Fees', 'Net Cash Flow'],
                'Amount': [
                    base_scenario['monthly_rent'] * (calc.occupancy_rate/100),
                    -calc.get_monthly_payment(),
                    -calc.hoa_fees_annual/12 if calc.hoa_fees_annual > 0 else 0,
                    base_scenario['monthly_cash_flow']
                ],
                'Type': ['Income', 'Expense', 'Expense', 'Net Result']
            }
            monthly_df = pd.DataFrame(monthly_breakdown)
            
            # Create waterfall-style chart
            fig_monthly = px.bar(
                monthly_df,
                x='Category',
                y='Amount',
                color='Type',
                title="",
                color_discrete_map={
                    'Income': '#2ca02c',
                    'Expense': '#d62728',
                    'Net Result': '#1f77b4'
                }
            )
            
            fig_monthly.update_layout(
                yaxis_title="Monthly Amount (SAR)",
                height=400,
                showlegend=True,
                margin=dict(t=20)
            )
            
            # Format y-axis to show values without decimals
            fig_monthly.update_yaxes(tickformat=",.0f")
            
            # Add zero line
            fig_monthly.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.5)
            
            st.plotly_chart(fig_monthly, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
    
    # Performance Metrics Summary
    with col2:
        st.header("📋 Performance Summary")
        
        # Key performance indicators
        st.subheader("📊 Key Metrics (Base Scenario)")
        
        # Create metrics comparison
        metrics_data = []
        for scenario_key, scenario_name in [('conservative', 'Conservative'), ('base', 'Base'), ('optimistic', 'Optimistic')]:
            scenario = scenarios[scenario_key]
            metrics_data.append({
                'Scenario': scenario_name,
                'Monthly Cash Flow': scenario['monthly_cash_flow'],
                'Annual ROI': scenario['roi'],
                'IRR': scenario['irr'] if scenario['irr'] is not None else 0,
                'Break-even Years': round(calc.get_total_initial_investment() / max(scenario['annual_cash_flow'], 1), 1) if scenario['annual_cash_flow'] > 0 else 'N/A'
            })
        
        metrics_df = pd.DataFrame(metrics_data)
        
        # Display key metrics for base scenario directly
        base_scenario = scenarios['base']
        st.markdown("**Base Scenario Performance:**")
        st.markdown(f"• Monthly Cash Flow: {format_currency_with_color(base_scenario['monthly_cash_flow'])}")
        st.markdown(f"• Annual ROI: {format_percentage_with_color(base_scenario['roi'])}")
        if base_scenario['irr'] is not None:
            st.markdown(f"• IRR: {format_percentage_with_color(base_scenario['irr'])}")
        
        # Calculate break-even years
        if base_scenario['annual_cash_flow'] > 0:
            breakeven_years = calc.get_total_initial_investment() / base_scenario['annual_cash_flow']
            if breakeven_years <= calc.holding_period:
                st.markdown(f"• Break-even: :green[{breakeven_years:.1f} years]")
            else:
                st.markdown(f"• Break-even: :orange[{breakeven_years:.1f} years]")
        else:
            st.markdown("• Break-even: :red[No break-even (negative cash flow)]")
    
    with col2:
        # Modern Investment Summary Section
        st.markdown("""
        <div class="glass-card">
            <h2 style="color: #2d3748; font-size: 1.5rem; margin-bottom: 1rem;">💼 Investment Summary</h2>
        """, unsafe_allow_html=True)
        
        base_scenario = scenarios['base']
        capital_gain = calc.resale_value - calc.property_price
        total_return = (base_scenario['annual_cash_flow'] * calc.holding_period) + capital_gain
        
        # Calculate advanced metrics
        advanced_metrics = get_advanced_metrics(calc)
        
        # Key Performance Tiles
        st.markdown(f"""
        <div class="metric-tile {'positive-tile' if base_scenario['monthly_cash_flow'] >= 0 else 'negative-tile'}">
            <div class="metric-value">{format_currency(base_scenario['monthly_cash_flow'])}</div>
            <div class="metric-label">Monthly Cash Flow</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="metric-tile {'positive-tile' if base_scenario['roi'] >= 5 else 'warning-tile' if base_scenario['roi'] >= 0 else 'negative-tile'}">
            <div class="metric-value">{format_percentage(base_scenario['roi'])}</div>
            <div class="metric-label">Annual ROI</div>
        </div>
        """, unsafe_allow_html=True)
        
        if base_scenario['irr'] is not None:
            st.markdown(f"""
            <div class="metric-tile {'positive-tile' if base_scenario['irr'] >= 5 else 'warning-tile' if base_scenario['irr'] >= 0 else 'negative-tile'}">
                <div class="metric-value">{format_percentage(base_scenario['irr'])}</div>
                <div class="metric-label">IRR</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="metric-tile {'positive-tile' if total_return >= 0 else 'negative-tile'}">
            <div class="metric-value">{format_currency(total_return)}</div>
            <div class="metric-label">Total Expected Return</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Advanced Metrics Section
        st.subheader("📊 Advanced Metrics")
        
        # DSCR Tile
        dscr_color = "positive-tile" if advanced_metrics['dscr'] >= 1.25 else "warning-tile" if advanced_metrics['dscr'] >= 1.0 else "negative-tile"
        dscr_value = f"{advanced_metrics['dscr']:.2f}" if advanced_metrics['dscr'] != float('inf') else "N/A"
        
        st.markdown(f"""
        <div class="metric-tile {dscr_color}">
            <div class="metric-value">{dscr_value}</div>
            <div class="metric-label">DSCR (Debt Service Coverage)</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Cash-on-Cash Return Tile
        coc_color = "positive-tile" if advanced_metrics['cash_on_cash_return'] >= 8 else "warning-tile" if advanced_metrics['cash_on_cash_return'] >= 5 else "negative-tile"
        
        st.markdown(f"""
        <div class="metric-tile {coc_color}">
            <div class="metric-value">{format_percentage(advanced_metrics['cash_on_cash_return'])}</div>
            <div class="metric-label">Cash-on-Cash Return</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Payback Period Tile
        payback_color = "positive-tile" if advanced_metrics['payback_period'] <= 10 else "warning-tile" if advanced_metrics['payback_period'] <= 15 else "negative-tile"
        payback_value = f"{advanced_metrics['payback_period']:.1f} years" if advanced_metrics['payback_period'] != float('inf') else "Never"
        
        st.markdown(f"""
        <div class="metric-tile {payback_color}">
            <div class="metric-value">{payback_value}</div>
            <div class="metric-label">Payback Period</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Cap Rate Tile
        cap_color = "positive-tile" if advanced_metrics['cap_rate'] >= 6 else "warning-tile" if advanced_metrics['cap_rate'] >= 4 else "negative-tile"
        
        st.markdown(f"""
        <div class="metric-tile {cap_color}">
            <div class="metric-value">{format_percentage(advanced_metrics['cap_rate'])}</div>
            <div class="metric-label">Capitalization Rate</div>
        </div>
        """, unsafe_allow_html=True)
        

        
        # Export functionality
        st.subheader("📥 Export Reports")
        
        col_export1, col_export2 = st.columns(2)
        
        with col_export1:
            # Excel Export
            excel_buffer = export_to_excel(calc, scenarios, scenario_df)
            st.download_button(
                label="📊 Excel Report",
                data=excel_buffer.getvalue(),
                file_name=f"investment_analysis_{property_price/1000:.0f}k.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        
        with col_export2:
            # PDF Export
            pdf_buffer = export_to_pdf(calc, scenarios, advanced_metrics)
            st.download_button(
                label="📄 PDF Report",
                data=pdf_buffer.getvalue(),
                file_name=f"investment_report_{property_price/1000:.0f}k.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        
        st.markdown("</div>", unsafe_allow_html=True)  # Close glass-card
        
        # Risk Analysis
        st.subheader("⚠️ Risk Considerations")
        
        # Calculate some risk metrics
        conservative_roi = scenarios['conservative']['roi']
        optimistic_roi = scenarios['optimistic']['roi']
        roi_range = optimistic_roi - conservative_roi
        
        if base_scenario['monthly_cash_flow'] < 0:
            st.error(f"⚠️ Negative cash flow in base scenario: {format_currency_with_color(base_scenario['monthly_cash_flow'])}")
        elif base_scenario['monthly_cash_flow'] < 200:
            st.warning(f"⚠️ Low cash flow margin: {format_currency(base_scenario['monthly_cash_flow'])}")
        else:
            st.success(f"✅ Positive cash flow projected: {format_currency(base_scenario['monthly_cash_flow'])}")
        
        if base_scenario['roi'] < 5:
            st.warning("⚠️ Low ROI - consider other investments")
        elif base_scenario['roi'] > 15:
            st.success("✅ Strong ROI potential")
        else:
            st.info("ℹ️ Moderate ROI - acceptable returns")
        
        st.write(f"**ROI Range:** {format_percentage(roi_range)}")
        if roi_range > 10:
            st.warning("High ROI volatility across scenarios")

else:
    # Welcome screen
    st.header("Welcome to Real Estate Investment Evaluator")
    st.markdown("""
    This tool helps you analyze the financial viability of rental property investments by calculating:
    
    - **Loan calculations** (monthly payments, total interest)
    - **Cash flow analysis** (monthly and annual projections)
    - **Return metrics** (ROI, IRR)
    - **Scenario comparisons** (Conservative, Base, Optimistic)
    - **Risk assessment** and investment summaries
    
    ### How to use:
    1. Fill in the property details in the sidebar
    2. Enter your financing terms
    3. Set rental income expectations
    4. Click "Calculate Investment Metrics"
    5. Review the comprehensive analysis and export results
    
    **Note:** This tool assumes a tax-free region and does not include utilities, insurance, or property taxes in the calculations.
    """)
    
    # Sample calculation for demonstration
    st.subheader("Example Analysis")
    st.markdown("""
    For a **SAR 1,875,000** property with **20% down**, **6.5% interest**, and **SAR 135,000/year rent**:
    - Monthly payment: ~SAR 9,480
    - Monthly cash flow: ~SAR 1,208 (after 95% occupancy)
    - Annual ROI: ~7.4%
    """)

# Footer
st.markdown("---")
st.markdown("*Real Estate Investment Evaluator - Built with Streamlit*")
