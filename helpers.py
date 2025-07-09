"""Utility helper functions."""


def format_currency(amount: float) -> str:
    """Format a number as currency with proper comma separation in Saudi Riyals."""
    if amount < 0:
        return f"SAR ({abs(amount):,.0f})"
    return f"SAR {amount:,.0f}"


def format_currency_with_color(amount: float) -> str:
    """Format currency with red color for negative values using HTML."""
    if amount < 0:
        return f"<span class='text-danger'>SAR ({abs(amount):,.0f})</span>"
    return f"SAR {amount:,.0f}"


def format_percentage(percentage: float) -> str:
    """Format a number as percentage with 2 decimal places."""
    if percentage < 0:
        return f"({abs(percentage):.2f}%)"
    return f"{percentage:.2f}%"


def format_percentage_with_color(percentage: float) -> str:
    """Format percentage with red color for negative values using HTML."""
    if percentage < 0:
        return f"<span class='text-danger'>({abs(percentage):.2f}%)</span>"
    return f"{percentage:.2f}%"


def format_number(number: float, decimals: int = 0) -> str:
    """Format a number with proper comma separation."""
    if decimals == 0:
        return f"{number:,.0f}"
    else:
        return f"{number:,.{decimals}f}"


def format_number_with_unit(number: float, unit: str = "", decimals: int = 0) -> str:
    """Format a number with proper comma separation and unit."""
    formatted_number = format_number(number, decimals)
    return f"{formatted_number} {unit}".strip()
