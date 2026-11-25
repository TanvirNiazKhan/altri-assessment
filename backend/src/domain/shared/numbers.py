from decimal import ROUND_HALF_UP, Decimal


def round_half_up(value: Decimal, places: int = 0) -> Decimal:
    """Commercial rounding. Never use round(): it is banker's rounding (8.25 -> 8.2)."""
    return value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
