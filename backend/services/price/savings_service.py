def calculate_savings(
    current_price: float, alternative_price: float
) -> tuple[float | None, float | None]:
    """Returns (savings, savings_percentage). Both None if the current
    price is 0 or negative (percentage would be undefined), or the
    alternative isn't actually cheaper — Spendly never presents a
    "savings" figure that would mislead the user.
    """
    if current_price <= 0:
        return None, None

    savings = round(current_price - alternative_price, 2)
    if savings <= 0:
        return None, None

    savings_percentage = round((savings / current_price) * 100, 2)
    return savings, savings_percentage
