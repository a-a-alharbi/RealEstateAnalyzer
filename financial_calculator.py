"""Core financial calculations used throughout the application."""

from typing import Dict, Optional, Any
import math

# These packages are optional. They are only required for advanced
# calculations like IRR. Import them lazily so the module can still be
# imported even if the dependencies are missing (e.g. in constrained
# test environments).
try:
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    np = None  # type: ignore

try:
    import numpy_financial as npf  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    npf = None  # type: ignore

class FinancialCalculator:
    """
    A comprehensive financial calculator for real estate investment analysis.
    """
    
    def __init__(
        self,
        property_price: float,
        down_payment: float,
        loan_term: int,
        interest_rate: float,
        base_monthly_rent: float,
        occupancy_rate: float,
        rent_growth: float = 0,
        enhancement_costs: float = 0,
        hoa_fees_annual: float = 0,
        holding_period: int = 10,
        resale_value: Optional[float] = None
    ):
        self.property_price = property_price
        self.down_payment = down_payment
        self.loan_term = loan_term
        self.interest_rate = interest_rate
        self.base_monthly_rent = base_monthly_rent
        self.occupancy_rate = occupancy_rate
        self.rent_growth = rent_growth
        self.enhancement_costs = enhancement_costs
        self.hoa_fees_annual = hoa_fees_annual
        self.holding_period = holding_period
        self.resale_value = resale_value or property_price * 1.2
        
        # Validate inputs
        self._validate_inputs()
    
    def _validate_inputs(self):
        """Validate input parameters."""
        if self.property_price <= 0:
            raise ValueError("Property price must be positive")
        if self.down_payment < 0 or self.down_payment > self.property_price:
            raise ValueError("Down payment must be between 0 and property price")
        if self.loan_term <= 0:
            raise ValueError("Loan term must be positive")
        if self.interest_rate < 0:
            raise ValueError("Interest rate cannot be negative")
        if self.base_monthly_rent < 0:
            raise ValueError("Monthly rent cannot be negative")
        if not 0 <= self.occupancy_rate <= 100:
            raise ValueError("Occupancy rate must be between 0 and 100")
        if self.rent_growth < 0:
            raise ValueError("Rent growth cannot be negative")
    
    def get_loan_amount(self) -> float:
        """Calculate the loan amount."""
        return self.property_price - self.down_payment
    
    def get_monthly_payment(self) -> float:
        """Calculate monthly mortgage payment using PMT formula."""
        loan_amount = self.get_loan_amount()
        
        if loan_amount <= 0:
            return 0
        
        monthly_rate = self.interest_rate / 100 / 12
        num_payments = self.loan_term * 12
        
        if monthly_rate == 0:
            return loan_amount / num_payments
        
        # PMT formula: PMT = PV * (r * (1 + r)^n) / ((1 + r)^n - 1)
        payment = loan_amount * (monthly_rate * (1 + monthly_rate) ** num_payments) / \
                 ((1 + monthly_rate) ** num_payments - 1)
        
        return payment
    
    def get_total_interest(self) -> float:
        """Calculate total interest paid over the loan term."""
        monthly_payment = self.get_monthly_payment()
        total_payments = monthly_payment * self.loan_term * 12
        loan_amount = self.get_loan_amount()
        return total_payments - loan_amount
    
    def get_total_payback_amount(self) -> float:
        """Calculate total amount to be paid back over the loan term (principal + interest)."""
        return self.get_monthly_payment() * self.loan_term * 12
    
    def get_total_initial_investment(self) -> float:
        """Calculate total initial investment."""
        return self.down_payment + self.enhancement_costs
    
    def get_effective_monthly_rent(self, rent_multiplier: float = 1.0) -> float:
        """Calculate effective monthly rent considering occupancy rate."""
        gross_rent = self.base_monthly_rent * rent_multiplier
        return gross_rent * (self.occupancy_rate / 100)

    # ---- New methods supporting rent escalation ----

    def _rent_growth_factor(self, year: int) -> float:
        """Return compounded growth factor for a given year (1-indexed)."""
        return (1 + self.rent_growth / 100) ** (year - 1)

    def get_monthly_rent_for_year(self, year: int, rent_multiplier: float = 1.0) -> float:
        """Monthly rent for a specific year accounting for growth."""
        return self.base_monthly_rent * self._rent_growth_factor(year) * rent_multiplier

    def get_effective_monthly_rent_for_year(self, year: int, rent_multiplier: float = 1.0) -> float:
        gross = self.get_monthly_rent_for_year(year, rent_multiplier)
        return gross * (self.occupancy_rate / 100)

    def get_monthly_cash_flow_for_year(self, year: int, rent_multiplier: float = 1.0) -> float:
        effective_rent = self.get_effective_monthly_rent_for_year(year, rent_multiplier)
        monthly_payment = self.get_monthly_payment()
        monthly_hoa = self.hoa_fees_annual / 12
        return effective_rent - monthly_payment - monthly_hoa

    def get_annual_net_income_for_year(self, year: int, rent_multiplier: float = 1.0) -> float:
        effective_rent = self.get_effective_monthly_rent_for_year(year, rent_multiplier)
        return effective_rent * 12 - self.hoa_fees_annual

    def get_annual_cash_flow_for_year(self, year: int, rent_multiplier: float = 1.0) -> float:
        return self.get_monthly_cash_flow_for_year(year, rent_multiplier) * 12

    def get_net_income_schedule(self, rent_multiplier: float = 1.0) -> list:
        return [self.get_annual_net_income_for_year(y, rent_multiplier) for y in range(1, self.holding_period + 1)]

    def get_cash_flow_schedule(self, rent_multiplier: float = 1.0) -> list:
        return [self.get_annual_cash_flow_for_year(y, rent_multiplier) for y in range(1, self.holding_period + 1)]
    
    def get_monthly_cash_flow(self, rent_multiplier: float = 1.0) -> float:
        """Calculate monthly cash flow."""
        effective_rent = self.get_effective_monthly_rent(rent_multiplier)
        monthly_payment = self.get_monthly_payment()
        monthly_hoa = self.hoa_fees_annual / 12
        
        return effective_rent - monthly_payment - monthly_hoa
    
    def get_annual_net_income(self, rent_multiplier: float = 1.0) -> float:
        """Calculate annual net rental income (before mortgage)."""
        effective_rent = self.get_effective_monthly_rent(rent_multiplier)
        annual_rent = effective_rent * 12
        return annual_rent - self.hoa_fees_annual
    
    def get_annual_cash_flow(self, rent_multiplier: float = 1.0) -> float:
        """Calculate annual cash flow (after mortgage)."""
        return self.get_monthly_cash_flow(rent_multiplier) * 12

    def get_roi(self, rent_multiplier: float = 1.0) -> float:
        """Calculate Return on Investment (ROI) using average annual cash flow."""
        cash_flows = self.get_cash_flow_schedule(rent_multiplier)
        if not cash_flows:
            return 0
        avg_cash_flow = sum(cash_flows) / len(cash_flows)
        total_investment = self.get_total_initial_investment()
        if total_investment <= 0:
            return 0
        return (avg_cash_flow / total_investment) * 100
    
    def get_irr(self, rent_multiplier: float = 1.0) -> Optional[float]:
        """
        Calculate Internal Rate of Return (IRR) including resale value.
        Returns IRR as percentage or None if calculation fails.
        """
        # IRR relies on numpy-financial. If it's not available simply return
        # None so that basic functionality can still be tested without the
        # heavy dependency.
        if npf is None:
            return None

        try:
            # Initial investment (negative cash flow)
            initial_investment = -self.get_total_initial_investment()

            cash_flows = [self.get_annual_cash_flow_for_year(y, rent_multiplier) for y in range(1, self.holding_period + 1)]
            # Add resale proceeds in final year
            cash_flows[-1] += self.resale_value - self.property_price

            # Combine initial investment with cash flows
            all_cash_flows = [initial_investment] + cash_flows
            
            # Calculate IRR
            irr = npf.irr(all_cash_flows)

            # Return as percentage, handle NaN, infinity, or complex numbers
            if (
                irr is None
                or math.isnan(float(irr))
                or math.isinf(float(irr))
                or isinstance(irr, complex)
            ):
                return None

            # Convert to percentage and ensure it's a valid float
            irr_percentage = float(irr * 100)
            if math.isnan(irr_percentage) or math.isinf(irr_percentage):
                return None
                
            return irr_percentage
            
        except Exception:
            return None
    
    def get_scenario_analysis(self) -> Dict[str, Dict[str, Any]]:
        """
        Generate analysis for three scenarios: Conservative, Base, and Optimistic.
        Returns dictionary with scenario data.
        """
        scenarios = {
            'conservative': {'multiplier': 0.85, 'name': 'Conservative'},
            'base': {'multiplier': 1.0, 'name': 'Base'},
            'optimistic': {'multiplier': 1.15, 'name': 'Optimistic'}
        }
        
        results = {}
        
        for scenario_key, scenario_info in scenarios.items():
            multiplier = scenario_info['multiplier']
            monthly_rent = self.get_monthly_rent_for_year(1, multiplier)
            effective_monthly_rent = self.get_effective_monthly_rent_for_year(1, multiplier)

            net_income_schedule = self.get_net_income_schedule(multiplier)
            cash_flow_schedule = self.get_cash_flow_schedule(multiplier)

            avg_net_income = sum(net_income_schedule) / len(net_income_schedule)
            avg_cash_flow = sum(cash_flow_schedule) / len(cash_flow_schedule)

            roi = self.get_roi(multiplier)
            irr = self.get_irr(multiplier)

            results[scenario_key] = {
                'monthly_rent': monthly_rent,
                'effective_monthly_rent': effective_monthly_rent,
                'monthly_cash_flow': avg_cash_flow / 12,
                'annual_net_income': avg_net_income,
                'annual_cash_flow': avg_cash_flow,
                'roi': roi,
                'irr': irr,
                'net_income_schedule': net_income_schedule,
                'cash_flow_schedule': cash_flow_schedule
            }
        
        return results
    
    def get_amortization_schedule(self, num_periods: Optional[int] = None) -> Dict[str, list]:
        """
        Generate amortization schedule for the loan.
        Returns dictionary with period, payment, principal, interest, and balance.
        """
        if num_periods is None:
            num_periods = self.loan_term * 12
        
        loan_amount = self.get_loan_amount()
        monthly_payment = self.get_monthly_payment()
        monthly_rate = self.interest_rate / 100 / 12
        
        schedule = {
            'period': [],
            'payment': [],
            'principal': [],
            'interest': [],
            'balance': []
        }
        
        remaining_balance = loan_amount
        
        for period in range(1, min(num_periods + 1, self.loan_term * 12 + 1)):
            if remaining_balance <= 0:
                break
            
            # Calculate interest for this period
            interest_payment = remaining_balance * monthly_rate
            
            # Calculate principal payment
            principal_payment = min(monthly_payment - interest_payment, remaining_balance)
            
            # Update remaining balance
            remaining_balance -= principal_payment
            
            # Store values
            schedule['period'].append(period)
            schedule['payment'].append(monthly_payment)
            schedule['principal'].append(principal_payment)
            schedule['interest'].append(interest_payment)
            schedule['balance'].append(max(0, remaining_balance))
        
        return schedule
    
    def get_investment_summary(self) -> Dict[str, Any]:
        """
        Get a comprehensive investment summary.
        """
        base_scenario = self.get_scenario_analysis()['base']
        
        return {
            'property_price': self.property_price,
            'down_payment': self.down_payment,
            'loan_amount': self.get_loan_amount(),
            'monthly_payment': self.get_monthly_payment(),
            'total_interest': self.get_total_interest(),
            'total_initial_investment': self.get_total_initial_investment(),
            'base_monthly_rent': self.base_monthly_rent,
            'effective_monthly_rent': base_scenario['effective_monthly_rent'],
            'monthly_cash_flow': base_scenario['monthly_cash_flow'],
            'annual_cash_flow': base_scenario['annual_cash_flow'],
            'roi': base_scenario['roi'],
            'irr': base_scenario['irr'],
            'holding_period': self.holding_period,
            'expected_resale_value': self.resale_value,
            'expected_capital_gain': self.resale_value - self.property_price
        }
