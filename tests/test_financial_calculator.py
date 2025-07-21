import os
import sys
import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from financial_calculator import FinancialCalculator


def test_loan_amount():
    calc = FinancialCalculator(
        property_price=100000,
        down_payment=20000,
        loan_term=30,
        interest_rate=5.0,
        base_monthly_rent=1500,
        occupancy_rate=100,
    )
    assert calc.get_loan_amount() == 80000


def test_monthly_payment():
    calc = FinancialCalculator(100000, 20000, 30, 5.0, 1500, 100)
    payment = calc.get_monthly_payment()
    assert payment == pytest.approx(429.46, abs=0.1)


def test_monthly_payment_simple_interest():
    calc = FinancialCalculator(100000, 20000, 30, 5.0, 1500, 100, interest_type="simple")
    payment = calc.get_monthly_payment()
    assert payment == pytest.approx(555.56, abs=0.1)


def test_rent_growth_escalates_cash_flow():
    growth_calc = FinancialCalculator(
        property_price=100000,
        down_payment=20000,
        loan_term=30,
        interest_rate=5.0,
        base_monthly_rent=1000,
        occupancy_rate=100,
        holding_period=3,
        rent_growth=5
    )
    flat_calc = FinancialCalculator(
        property_price=100000,
        down_payment=20000,
        loan_term=30,
        interest_rate=5.0,
        base_monthly_rent=1000,
        occupancy_rate=100,
        holding_period=3,
        rent_growth=0
    )

    growth_schedule = growth_calc.get_cash_flow_schedule()
    flat_schedule = flat_calc.get_cash_flow_schedule()

    assert growth_schedule[1] > flat_schedule[1]
    assert growth_schedule[2] > growth_schedule[1]
