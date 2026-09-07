from flask_app import app, create_calculator_from_data


def test_calculate_rejects_missing_json_body():
    client = app.test_client()

    response = client.post('/calculate')

    assert response.status_code == 400
    assert response.get_json() == {
        'success': False,
        'error': 'A JSON request body is required',
    }


def test_calculate_includes_operating_expenses():
    client = app.test_client()
    response = client.post('/calculate', json={
        'property_price': 100000,
        'down_payment': 20000,
        'loan_term': 30,
        'interest_rate': 0,
        'base_monthly_rent': 12000,
        'occupancy_rate': 100,
        'operating_expenses_annual': 1200,
        'holding_period': 10,
        'resale_value': 120000,
    })

    assert response.status_code == 200
    payload = response.get_json()
    assert payload['success'] is True
    assert payload['calculator_data']['operating_expenses_annual'] == 1200
    assert payload['scenarios']['base']['annual_net_income'] == 10800


def test_export_calculator_derives_down_payment_from_percentage():
    calc = create_calculator_from_data({
        'property_price': '100,000',
        'down_payment_percentage': 20,
        'base_monthly_rent': 12000,
    })

    assert calc.down_payment == 20000
