from decimal import Decimal


def calculated_percent_diff(base_price: Decimal, new_price: Decimal) -> Decimal:
    """ 0 means price is lower or whatever """
    decimal_zero = Decimal(0)

    if base_price >= new_price:
        return decimal_zero

    diff = new_price - base_price

    return Decimal(diff * 100 / base_price)


def truncate_price_or_qty(number: Decimal, digits: int) -> Decimal:
    str_number = str(number)
    i = str_number.index(".")
    return Decimal(str_number[:i + digits + 1])
