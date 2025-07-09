# Real Estate Investment Evaluator

## Overview

This is a Flask-based web application for analyzing real estate investment opportunities. The application provides comprehensive financial calculations and visualizations to help users evaluate the profitability and risk of rental property investments. It uses Python Flask for the backend API, Bootstrap for responsive UI, and Plotly for interactive data visualization.

## System Architecture

The application follows a modern web application architecture:

1. **Presentation Layer**: Bootstrap-based responsive web interface with sidebar inputs and dashboard
2. **API Layer**: Flask REST endpoints for calculations and data export
3. **Business Logic Layer**: Financial calculation engine with comprehensive real estate metrics
4. **Utility Layer**: Helper functions for formatting, data export, and common operations

### Technology Stack
- **Backend**: Flask (Python web framework)
- **Frontend**: Bootstrap 5, Custom CSS, JavaScript
- **Data Processing**: Pandas, NumPy
- **Financial Calculations**: NumPy Financial
- **Visualization**: Plotly Express and Plotly Graph Objects
- **Data Export**: Excel integration via openpyxl, PDF via ReportLab with embedded charts

## Key Components

### 1. Main Application (flask_app.py)
- **Purpose**: Flask web server with REST API endpoints
- **Features**: 
  - RESTful API for investment calculations
  - JSON data exchange with frontend
  - Excel and PDF export endpoints (PDF includes charts)
  - Real-time calculation processing
- **Architecture Decision**: Flask was chosen for better performance, scalability, and separation of concerns between frontend and backend

### 2. Financial Calculator (financial_calculator.py)
- **Purpose**: Core business logic for real estate investment calculations
- **Features**:
  - Comprehensive financial metrics (ROI, Cash-on-Cash return, etc.)
  - Input validation and error handling
  - Flexible parameter configuration
- **Architecture Decision**: Separated into dedicated class for maintainability and testability

### 3. Utilities Module (utils.py)
- **Purpose**: Common formatting and export functionality
- **Features**:
  - Currency and percentage formatting
  - Excel export capabilities
  - Data transformation helpers
- **Architecture Decision**: Centralized utility functions to avoid code duplication and ensure consistent formatting

## Data Flow

1. **Input Collection**: User enters property details, financial parameters, and investment assumptions through web form
2. **API Request**: JavaScript sends form data to Flask backend via AJAX
3. **Validation**: Financial calculator validates all inputs for logical consistency
4. **Calculation**: Core financial metrics are computed using numpy-financial functions
5. **Response**: Flask returns JSON data with calculations and chart data
6. **Visualization**: JavaScript renders interactive Plotly charts in the browser
7. **Export**: Users can download comprehensive Excel and PDF reports via dedicated endpoints

## External Dependencies

### Core Libraries
- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computing
- **numpy-financial**: Financial calculations (NPV, IRR, etc.)
- **plotly**: Interactive data visualization
- **openpyxl**: Excel file generation

### Rationale for Dependencies
- **NumPy Financial**: Provides industry-standard financial functions for accurate real estate calculations
- **Plotly**: Chosen over matplotlib for interactive charts that enhance user experience
- **Flask**: Provides RESTful API architecture and good performance
- **Bootstrap**: Ensures responsive design and professional UI components

## Deployment Strategy

The application is designed for deployment on Replit with the following considerations:

1. **Single File Deployment**: All dependencies are Python-based for easy package management
2. **No Database Required**: All calculations are performed in-memory
3. **Export Functionality**: Provides Excel downloads for data persistence

### Deployment Requirements
- Python 3.7+
- All dependencies installable via pip
- No external database or storage services required

## User Preferences

Preferred communication style: Simple, everyday language.

## Changelog

Changelog:
- July 04, 2025. Initial setup
- July 04, 2025. Updated currency to Saudi Riyals (SAR), changed rent input to annual basis, enhanced property enhancement costs visibility
- July 04, 2025. Added comma-separated number formatting for better readability in input fields and captions
- July 04, 2025. Enhanced negative number formatting with parentheses and red color for better visual clarity
- July 04, 2025. Redesigned dashboard with clearer visualizations: separate ROI and cash flow charts, cumulative projections, investment breakdown pie chart, and monthly income vs expenses analysis
- July 04, 2025. Modernized UI with tile-based design, custom CSS styling, color-coded tiles for different metrics, and removed decimal formatting from chart values for cleaner display
- July 04, 2025. Added modern tiles to all charts with styled headers, consistent borders, shadows, and improved visual hierarchy for professional dashboard appearance
- July 06, 2025. Enhanced with advanced financial metrics: DSCR, Cash-on-Cash Return, Payback Period, and Capitalization Rate with color-coded tile displays
- July 06, 2025. Added professional PDF export functionality with comprehensive investment analysis reports including risk assessment and recommendations
- July 06, 2025. Complete modern UI redesign with gradient hero section, glass-morphism cards, enhanced animations, and professional color scheme with purple/blue gradients
- July 06, 2025. Implemented sleek dashboard design with clean KPI cards, smooth area charts, modern donut charts, and professional statistics section matching contemporary dashboard aesthetics
- July 06, 2025. Complete rebuild using Flask framework with RESTful API architecture, Bootstrap responsive UI, JavaScript frontend interactions, and improved performance over the previous implementation
- July 06, 2025. Fixed critical PDF export bug where annual rental income was incorrectly treated as monthly rent, causing inflated ROI and cash flow calculations in reports- July 06, 2025. Enhanced KPIs with Cash-on-Cash Return and DSCR metrics, implemented intelligent color coding (green/yellow/red) based on performance thresholds, and added informative tooltips explaining each metric.
- July 06, 2025. Created main.py deployment entry point to ensure Flask app deploys correctly, added tile containers for KPI section matching Property Details design, and fixed color coding for all KPI metrics with performance-based thresholds.
- July 07, 2025. PDF reports now embed charts and include page numbers for easier navigation
