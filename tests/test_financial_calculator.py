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


def test_operating_expenses_reduce_noi_and_cash_flow():
    calc = FinancialCalculator(
        100000, 20000, 30, 5.0, 1500, 100,
        hoa_fees_annual=1200,
        operating_expenses_annual=2400,
    )

    assert calc.get_annual_net_income() == 14400
    assert calc.get_monthly_cash_flow() == pytest.approx(1500 - 300 - calc.get_monthly_payment())


def test_cash_flow_stops_charging_mortgage_after_loan_term():
    calc = FinancialCalculator(
        100000, 20000, 1, 0, 1000, 100,
        holding_period=2,
    )

    assert calc.get_annual_cash_flow_for_year(1) == pytest.approx(-68000)
    assert calc.get_annual_cash_flow_for_year(2) == pytest.approx(12000)


def test_remaining_balance_reaches_zero_at_end_of_term():
    calc = FinancialCalculator(100000, 20000, 30, 5.0, 1500, 100)

    assert calc.get_remaining_loan_balance(0) == 80000
    assert 0 < calc.get_remaining_loan_balance(120) < 80000
    assert calc.get_remaining_loan_balance(360) == 0


def test_irr_uses_sale_proceeds_after_mortgage_payoff(monkeypatch):
    captured = {}

    class FakeFinancial:
        @staticmethod
        def irr(cash_flows):
            captured['cash_flows'] = cash_flows
            return 0.1

    monkeypatch.setattr('financial_calculator.npf', FakeFinancial)
    calc = FinancialCalculator(
        100000, 20000, 30, 0, 0, 100,
        holding_period=1,
        resale_value=110000,
    )

    assert calc.get_irr() == pytest.approx(10)
    # The final flow includes rent operations plus sale proceeds, less the balance.
    assert captured['cash_flows'][-1] == pytest.approx(-2666.67 + 110000 - 77333.33, abs=0.02)


@pytest.mark.parametrize(
    ('kwargs', 'message'),
    [
        ({'operating_expenses_annual': -1}, 'Annual expenses'),
        ({'holding_period': 0}, 'Holding period'),
        ({'resale_value': -1}, 'Resale value'),
    ],
)
def test_rejects_invalid_investment_assumptions(kwargs, message):
    with pytest.raises(ValueError, match=message):
        FinancialCalculator(100000, 20000, 30, 5.0, 1500, 100, **kwargs)
