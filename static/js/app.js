// Real Estate Investment Calculator - JavaScript
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('calculatorForm');
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    const welcome = document.getElementById('welcome');
    const occupancySlider = document.getElementById('occupancy_rate');
    const occupancyValue = document.getElementById('occupancy_value');
    const downPaymentSlider = document.getElementById('down_payment_percentage');
    const downPaymentPercentageValue = document.getElementById('down_payment_percentage_value');
    const downPaymentAmount = document.getElementById('down_payment_amount');
    const propertyPriceInput = document.getElementById('property_price');

    // Initialize currency input formatting
    initializeCurrencyInputs();

    // Update occupancy rate display
    occupancySlider.addEventListener('input', function() {
        occupancyValue.textContent = this.value + '%';
    });

    // Update down payment display
    function updateDownPayment() {
        const percentage = parseInt(downPaymentSlider.value);
        const propertyPrice = parseInt(propertyPriceInput.getAttribute('data-value') || '0');
        const amount = (propertyPrice * percentage) / 100;
        
        downPaymentPercentageValue.textContent = percentage + '%';
        downPaymentAmount.textContent = 'SAR ' + formatNumberWithCommas(amount);
        downPaymentSlider.setAttribute('data-amount', amount);
    }

    downPaymentSlider.addEventListener('input', updateDownPayment);
    
    // Update down payment when property price changes
    propertyPriceInput.addEventListener('blur', function() {
        updateDownPayment();
        updateResaleValue();
    });
    
    // Initialize down payment display
    updateDownPayment();
    
    // Update resale value when holding period changes
    const holdingPeriodSelect = document.getElementById('holding_period');
    const resaleValueInput = document.getElementById('resale_value');
    
    function updateResaleValue() {
        const propertyPrice = parseInt(propertyPriceInput.getAttribute('data-value') || '0');
        const holdingPeriod = parseInt(holdingPeriodSelect.value);
        
        // Conservative inflation rate of 2.5% per year
        const inflationRate = 0.025;
        const resaleValue = propertyPrice * Math.pow(1 + inflationRate, holdingPeriod);
        
        // Update the resale value input
        resaleValueInput.value = formatNumberWithCommas(Math.round(resaleValue));
        resaleValueInput.setAttribute('data-value', Math.round(resaleValue));
    }
    
    holdingPeriodSelect.addEventListener('change', updateResaleValue);
    
    // Initialize resale value
    updateResaleValue();

    function initializeCurrencyInputs() {
        const currencyInputs = document.querySelectorAll('.currency-input');
        
        currencyInputs.forEach(input => {
            // Format on input
            input.addEventListener('input', function(e) {
                let value = e.target.value.replace(/[^\d]/g, ''); // Remove non-digits
                let numericValue = parseInt(value) || 0;
                
                // Store the numeric value in data attribute
                e.target.setAttribute('data-value', numericValue);
                
                // Format with commas
                e.target.value = formatNumberWithCommas(numericValue);
            });

            // Handle focus to show clean number for editing
            input.addEventListener('focus', function(e) {
                let numericValue = e.target.getAttribute('data-value') || '0';
                if (numericValue === '0') {
                    e.target.value = '';
                } else {
                    e.target.value = numericValue;
                }
            });

            // Handle blur to restore formatted display
            input.addEventListener('blur', function(e) {
                let value = e.target.value.replace(/[^\d]/g, '');
                let numericValue = parseInt(value) || 0;
                e.target.setAttribute('data-value', numericValue);
                e.target.value = formatNumberWithCommas(numericValue);
            });
        });
    }

    function formatNumberWithCommas(number) {
        return new Intl.NumberFormat('en-US').format(number);
    }

    // Form submission
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        calculateInvestment();
    });

    // Export buttons
    document.getElementById('export-excel').addEventListener('click', function() {
        exportToExcel();
    });

    document.getElementById('export-pdf').addEventListener('click', function() {
        exportToPDF();
    });

    function calculateInvestment() {
        // Show loading, hide other sections
        loading.style.display = 'block';
        results.style.display = 'none';
        welcome.style.display = 'none';

        // Collect form data with proper numeric values for currency inputs
        const data = {};
        const formElements = form.elements;
        
        for (let element of formElements) {
            if (element.name) {
                if (element.classList.contains('currency-input')) {
                    // Use the numeric value from data attribute
                    data[element.name] = element.getAttribute('data-value') || '0';
                } else {
                    data[element.name] = element.value;
                }
            }
        }
        
        // Calculate down payment amount from percentage
        if (data.down_payment_percentage) {
            const propertyPrice = parseInt(data.property_price || '0');
            const percentage = parseInt(data.down_payment_percentage);
            data.down_payment = (propertyPrice * percentage / 100).toString();
        }

        // Send request to Flask backend
        fetch('/calculate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Backend response:', data);
            console.log('Data success field:', data.success);
            console.log('Data keys:', Object.keys(data));
            
            if (data.success) {
                try {
                    displayResults(data);
                } catch (displayError) {
                    console.error('Error in displayResults:', displayError);
                    showError(`Display error: ${displayError.message}`);
                }
            } else {
                console.error('Backend error:', data.error);
                showError(data.error || 'An error occurred during calculation.');
            }
        })
        .catch(error => {
            console.error('Fetch error:', error);
            showError(`Calculation failed: ${error.message}`);
        })
        .finally(() => {
            loading.style.display = 'none';
        });
    }

    function displayResults(data) {
        console.log('Received data:', data);
        
        // Show results section
        results.style.display = 'block';

        try {
            console.log('Step 1: Storing data for exports');
            // Store data for exports first
            window.currentData = data;

            console.log('Step 2: Updating KPI cards with:', data.charts?.kpi_data);
            // Update KPI cards
            updateKPICards(data.charts.kpi_data);

            console.log('Step 3: Creating cash flow chart');
            // Update charts
            createCashFlowChart(data.charts.cash_flow_data, data.charts.break_even_amount);
            
            console.log('Step 4: Creating investment breakdown chart');
            createInvestmentBreakdownChart(data.charts.investment_breakdown);
            
            console.log('Step 5: Creating ROI comparison chart');
            createROIComparisonChart(data.charts.roi_comparison);
            
            console.log('Step 6: Creating monthly analysis chart');
            createMonthlyAnalysisChart(data.scenarios);

            console.log('Step 7: Updating scenario table');
            // Update scenario table
            updateScenarioTable(data.scenarios);

            console.log('Step 8: Updating statistics');
            // Update statistics
            updateStatistics(data);

            console.log('Step 9: Updating property details');
            // Update property details
            updatePropertyDetails(data);
        } catch (error) {
            console.error('Error displaying results:', error);
            showError('Error displaying results: ' + error.message);
        }
    }

    function updateKPICards(kpiData) {
        console.log('Updating KPI cards with data:', kpiData);
        try {
            const advancedMetrics = window.currentData.advanced_metrics;
            
            // Update KPI values with color coding
            document.getElementById('kpi-monthly-cash-flow').innerHTML = formatCurrencyWithColor(kpiData.monthly_cash_flow);
            document.getElementById('kpi-annual-roi').innerHTML = formatROIWithColor(kpiData.annual_roi);
            document.getElementById('kpi-cash-on-cash').innerHTML = formatCashOnCashWithColor(advancedMetrics.cash_on_cash_return);
            document.getElementById('kpi-dscr').innerHTML = advancedMetrics.dscr < 1.0 ? `<span style="color: #dc3545; font-weight: 600;">${advancedMetrics.dscr.toFixed(2)}</span>` : advancedMetrics.dscr.toFixed(2);
            document.getElementById('kpi-total-investment').textContent = formatCurrency(kpiData.total_investment);
            
            // Format payback period with color
            const paybackYears = kpiData.break_even_years;
            let paybackFormatted = paybackYears.toFixed(1) + ' yrs';
            if (paybackYears > 15) {
                paybackFormatted = `<span style="color: #dc3545; font-weight: 600;">${paybackFormatted}</span>`;
            } else if (paybackYears > 10) {
                paybackFormatted = `<span style="color: #ffc107; font-weight: 600;">${paybackFormatted}</span>`;
            } else {
                paybackFormatted = `<span style="color: #28a745; font-weight: 600;">${paybackFormatted}</span>`;
            }
            document.getElementById('kpi-break-even').innerHTML = paybackFormatted;
            
            // Apply color coding
            applyKPIColorCoding(kpiData, advancedMetrics);
            
            // Initialize tooltips
            initializeTooltips();
            
        } catch (error) {
            console.error('Error in updateKPICards:', error);
            throw error;
        }
    }
    
    function applyKPIColorCoding(kpiData, advancedMetrics) {
        // Monthly Cash Flow
        const cashFlowCard = document.getElementById('kpi-card-cash-flow');
        if (kpiData.monthly_cash_flow > 0) {
            setKPICardClass(cashFlowCard, 'good');
        } else if (kpiData.monthly_cash_flow === 0) {
            setKPICardClass(cashFlowCard, 'warning');
        } else {
            setKPICardClass(cashFlowCard, 'poor');
        }
        
        // Annual ROI
        const roiCard = document.getElementById('kpi-card-roi');
        if (kpiData.annual_roi > 8) {
            setKPICardClass(roiCard, 'good');
        } else if (kpiData.annual_roi >= 5) {
            setKPICardClass(roiCard, 'warning');
        } else {
            setKPICardClass(roiCard, 'poor');
        }
        
        // Cash-on-Cash Return
        const cashOnCashCard = document.getElementById('kpi-card-cash-on-cash');
        if (advancedMetrics.cash_on_cash_return > 12) {
            setKPICardClass(cashOnCashCard, 'good');
        } else if (advancedMetrics.cash_on_cash_return >= 8) {
            setKPICardClass(cashOnCashCard, 'warning');
        } else {
            setKPICardClass(cashOnCashCard, 'poor');
        }
        
        // DSCR
        const dscrCard = document.getElementById('kpi-card-dscr');
        if (advancedMetrics.dscr > 1.25) {
            setKPICardClass(dscrCard, 'good');
        } else if (advancedMetrics.dscr >= 1.0) {
            setKPICardClass(dscrCard, 'warning');
        } else {
            setKPICardClass(dscrCard, 'poor');
        }
        
        // Payback Period
        const paybackCard = document.getElementById('kpi-card-payback');
        if (kpiData.break_even_years < 10) {
            setKPICardClass(paybackCard, 'good');
        } else if (kpiData.break_even_years <= 15) {
            setKPICardClass(paybackCard, 'warning');
        } else {
            setKPICardClass(paybackCard, 'poor');
        }
        
        // Total Investment (neutral - no color coding)
        const investmentCard = document.getElementById('kpi-card-investment');
        setKPICardClass(investmentCard, 'neutral');
    }
    
    function setKPICardClass(card, className) {
        // Remove all existing color classes
        card.classList.remove('good', 'warning', 'poor', 'neutral');
        // Add the new class
        card.classList.add(className);
    }
    
    function initializeTooltips() {
        // Initialize Bootstrap tooltips if Bootstrap is available
        if (typeof bootstrap !== 'undefined') {
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
        }
    }
    
    function initializeTooltips() {
        // Initialize Bootstrap tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    function createCashFlowChart(cashFlowData, breakEvenAmount) {
        const traces = [];
        const colors = {
            'Conservative': '#E8F0FE',
            'Base': '#4285F4',
            'Optimistic': '#34A853'
        };

        for (const [scenario, values] of Object.entries(cashFlowData.scenarios)) {
            traces.push({
                x: cashFlowData.years,
                y: values,
                type: 'scatter',
                mode: 'lines+markers',
                name: scenario,
                line: {
                    color: colors[scenario] === '#E8F0FE' ? '#6C757D' : colors[scenario],
                    width: 3
                },
                marker: {
                    size: 6
                }
            });
        }

        // Add break-even line
        traces.push({
            x: cashFlowData.years,
            y: Array(cashFlowData.years.length).fill(breakEvenAmount),
            type: 'scatter',
            mode: 'lines',
            name: 'Break-even',
            line: {
                color: '#FFC107',
                width: 2,
                dash: 'dash'
            },
            showlegend: false
        });

        const layout = {
            title: '',
            xaxis: {
                title: 'Years',
                showgrid: false,
                showline: false,
                zeroline: false
            },
            yaxis: {
                title: 'Cumulative Cash Flow (SAR)',
                showgrid: true,
                gridcolor: '#F8F9FA',
                showline: false,
                zeroline: false,
                tickformat: ',.0f'
            },
            plot_bgcolor: 'white',
            paper_bgcolor: 'white',
            font: {
                family: 'system-ui',
                size: 11,
                color: '#495057'
            },
            legend: {
                orientation: 'h',
                yanchor: 'bottom',
                y: -0.2,
                xanchor: 'center',
                x: 0.5
            },
            margin: {
                l: 50,
                r: 20,
                t: 20,
                b: 50
            },
            height: 300
        };

        Plotly.newPlot('cash-flow-chart', traces, layout, {responsive: true});
    }

    function createInvestmentBreakdownChart(breakdownData) {
        const data = [{
            values: breakdownData.values,
            labels: breakdownData.labels,
            type: 'pie',
            hole: 0.6,
            marker: {
                colors: breakdownData.colors,
                line: {
                    color: 'white',
                    width: 2
                }
            },
            textposition: 'outside',
            textinfo: 'percent',
            textfont: {
                size: 11
            }
        }];

        const layout = {
            title: '',
            showlegend: true,
            legend: {
                orientation: 'v',
                yanchor: 'middle',
                y: 0.5,
                xanchor: 'left',
                x: 1.1
            },
            font: {
                family: 'system-ui',
                size: 10,
                color: '#495057'
            },
            margin: {
                l: 20,
                r: 80,
                t: 20,
                b: 20
            },
            height: 300
        };

        Plotly.newPlot('investment-breakdown-chart', data, layout, {responsive: true});
    }

    function createROIComparisonChart(roiData) {
        const data = [{
            x: roiData.labels,
            y: roiData.values,
            type: 'bar',
            marker: {
                color: roiData.colors
            }
        }];

        const layout = {
            title: '',
            xaxis: {
                showgrid: false,
                showline: true,
                linecolor: '#E5E5E5'
            },
            yaxis: {
                title: 'ROI (%)',
                showgrid: true,
                gridcolor: '#F8F9FA',
                showline: true,
                linecolor: '#E5E5E5'
            },
            plot_bgcolor: 'white',
            paper_bgcolor: 'white',
            font: {
                family: 'system-ui',
                size: 11,
                color: '#495057'
            },
            margin: {
                l: 50,
                r: 20,
                t: 20,
                b: 40
            },
            height: 300
        };

        Plotly.newPlot('roi-comparison-chart', data, layout, {responsive: true});
    }

    function createMonthlyAnalysisChart(scenarios) {
        const baseScenario = scenarios.base;
        const occupancyRate = window.currentData && window.currentData.calculator_data ? 
                            window.currentData.calculator_data.occupancy_rate : 95;
        const effectiveRent = baseScenario.monthly_rent * occupancyRate / 100;
        const monthlyPayment = window.currentData && window.currentData.calculator_data ? 
                              window.currentData.calculator_data.monthly_payment : 0;
        const monthlyHOA = window.currentData && window.currentData.calculator_data ? 
                          (window.currentData.calculator_data.hoa_fees_annual || 0) / 12 : 0;
        
        const data = [{
            x: ['Rental Income', 'Mortgage Payment', 'HOA Fees', 'Net Cash Flow'],
            y: [effectiveRent, -monthlyPayment, -monthlyHOA, baseScenario.monthly_cash_flow],
            type: 'bar',
            marker: {
                color: ['#34A853', '#EA4335', '#FFA500', baseScenario.monthly_cash_flow >= 0 ? '#4285F4' : '#EA4335']
            }
        }];

        const layout = {
            title: '',
            xaxis: {
                showgrid: false,
                showline: true,
                linecolor: '#E5E5E5'
            },
            yaxis: {
                title: 'Amount (SAR)',
                showgrid: true,
                gridcolor: '#F8F9FA',
                showline: true,
                linecolor: '#E5E5E5',
                tickformat: ',.0f'
            },
            plot_bgcolor: 'white',
            paper_bgcolor: 'white',
            font: {
                family: 'system-ui',
                size: 11,
                color: '#495057'
            },
            margin: {
                l: 50,
                r: 20,
                t: 20,
                b: 40
            },
            height: 300
        };

        // Add zero line
        layout.shapes = [{
            type: 'line',
            x0: -0.5,
            x1: 1.5,
            y0: 0,
            y1: 0,
            line: {
                color: 'black',
                width: 1,
                dash: 'dash'
            }
        }];

        Plotly.newPlot('monthly-analysis-chart', data, layout, {responsive: true});
    }

    function updateScenarioTable(scenarios) {
        const tableBody = document.getElementById('scenario-table-body');
        tableBody.innerHTML = '';

        const scenarioNames = {
            'conservative': 'Conservative',
            'base': 'Base',
            'optimistic': 'Optimistic'
        };

        // Define the order: Conservative, Base, Optimistic
        const scenarioOrder = ['conservative', 'base', 'optimistic'];

        for (const key of scenarioOrder) {
            const scenario = scenarios[key];
            if (!scenario) continue;
            
            const row = document.createElement('tr');
            
            // Format values with red color for negatives
            const monthlyRent = formatCurrency(scenario.monthly_rent);
            const monthlyCashFlow = formatCurrencyWithColor(scenario.monthly_cash_flow);
            const annualCashFlow = formatCurrencyWithColor(scenario.annual_cash_flow);
            const roi = formatPercentageWithColor(scenario.roi);
            const irr = scenario.irr ? formatPercentageWithColor(scenario.irr) : 'N/A';
            
            row.innerHTML = `
                <td><strong>${scenarioNames[key]}</strong></td>
                <td>${monthlyRent}</td>
                <td>${monthlyCashFlow}</td>
                <td>${annualCashFlow}</td>
                <td>${roi}</td>
                <td>${irr}</td>
            `;
            tableBody.appendChild(row);
        }
    }

    function updateStatistics(data) {
        document.getElementById('stat-total-investment').textContent = formatCurrency(data.calculator_data.total_investment);
        document.getElementById('stat-total-returns').textContent = formatCurrency(data.scenarios.base.annual_cash_flow);
    }

    function updatePropertyDetails(data) {
        try {
            const propertyPriceElement = document.getElementById('property_price');
            const enhancementCostElement = document.getElementById('enhancement_costs');
            const interestRateElement = document.getElementById('interest_rate');
            
            const propertyPrice = propertyPriceElement ? (propertyPriceElement.getAttribute('data-value') || propertyPriceElement.value || '0') : '0';
            const enhancementCost = enhancementCostElement ? (enhancementCostElement.getAttribute('data-value') || enhancementCostElement.value || '0') : '0';
            const interestRate = interestRateElement ? interestRateElement.value : '0';
            
            // Calculate down payment from total investment minus enhancement costs
            const downPayment = data.calculator_data.total_investment - parseFloat(enhancementCost);
            
            document.getElementById('detail-property-price').textContent = formatCurrency(parseFloat(propertyPrice));
            document.getElementById('detail-down-payment').textContent = formatCurrency(downPayment);
            document.getElementById('detail-loan-amount').textContent = formatCurrency(data.calculator_data.loan_amount);
            document.getElementById('detail-enhancement-cost').textContent = formatCurrency(parseFloat(enhancementCost));
            document.getElementById('detail-monthly-payment').textContent = formatCurrency(data.calculator_data.monthly_payment);
            document.getElementById('detail-interest-rate').textContent = parseFloat(interestRate).toFixed(1) + '%';
        } catch (error) {
            console.error('Error updating property details:', error);
        }
    }

    function exportToExcel() {
        if (!window.currentData) {
            alert('Please calculate investment metrics first');
            return;
        }

        // Get form data with proper numeric values
        const data = {};
        const formElements = form.elements;
        
        for (let element of formElements) {
            if (element.name) {
                if (element.classList.contains('currency-input')) {
                    data[element.name] = element.getAttribute('data-value') || '0';
                } else {
                    data[element.name] = element.value;
                }
            }
        }

        fetch('/export_excel', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })
        .then(response => response.blob())
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = 'investment_analysis.xlsx';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error exporting to Excel');
        });
    }

    function exportToPDF() {
        if (!window.currentData) {
            alert('Please calculate investment metrics first');
            return;
        }

        // Get form data with proper numeric values
        const data = {};
        const formElements = form.elements;
        
        for (let element of formElements) {
            if (element.name) {
                if (element.classList.contains('currency-input')) {
                    data[element.name] = element.getAttribute('data-value') || '0';
                } else {
                    data[element.name] = element.value;
                }
            }
        }
        
        // Calculate down payment amount from percentage
        if (data.down_payment_percentage) {
            const propertyPrice = parseInt(data.property_price || '0');
            const percentage = parseInt(data.down_payment_percentage);
            data.down_payment = (propertyPrice * percentage / 100).toString();
        }

        fetch('/export_pdf', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })
        .then(response => response.blob())
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = 'investment_analysis.pdf';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error exporting to PDF');
        });
    }

    function showError(message) {
        alert('Error: ' + message);
        welcome.style.display = 'block';
    }

    function formatCurrency(amount) {
        return 'SAR ' + new Intl.NumberFormat('en-US').format(Math.round(amount));
    }

    function formatPercentage(percentage) {
        return percentage.toFixed(2) + '%';
    }
    
    function formatCurrencyWithColor(amount) {
        const formatted = formatCurrency(amount);
        if (amount < 0) {
            return `<span style="color: #dc3545; font-weight: 600;">${formatted}</span>`;
        } else if (amount > 0) {
            return `<span style="color: #28a745; font-weight: 600;">${formatted}</span>`;
        }
        return `<span style="color: #ffc107; font-weight: 600;">${formatted}</span>`;
    }
    
    function formatPercentageWithColor(percentage) {
        const formatted = formatPercentage(percentage);
        if (percentage < 0) {
            return `<span style="color: #dc3545; font-weight: 600;">${formatted}</span>`;
        }
        return formatted;
    }
    
    function formatROIWithColor(percentage) {
        const formatted = formatPercentage(percentage);
        if (percentage > 8) {
            return `<span style="color: #28a745; font-weight: 600;">${formatted}</span>`;
        } else if (percentage >= 5) {
            return `<span style="color: #ffc107; font-weight: 600;">${formatted}</span>`;
        } else {
            return `<span style="color: #dc3545; font-weight: 600;">${formatted}</span>`;
        }
    }
    
    function formatCashOnCashWithColor(percentage) {
        const formatted = formatPercentage(percentage);
        if (percentage > 10) {
            return `<span style="color: #28a745; font-weight: 600;">${formatted}</span>`;
        } else if (percentage >= 5) {
            return `<span style="color: #ffc107; font-weight: 600;">${formatted}</span>`;
        } else {
            return `<span style="color: #dc3545; font-weight: 600;">${formatted}</span>`;
        }
    }
});