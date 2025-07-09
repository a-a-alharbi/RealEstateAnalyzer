import pytest
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
