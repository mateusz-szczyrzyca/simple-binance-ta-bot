from typing import NamedTuple
from decimal import Decimal


class BinanceFilter(NamedTuple):
    name: str
    minValue: Decimal
    maxValue: Decimal
    confValue: Decimal
