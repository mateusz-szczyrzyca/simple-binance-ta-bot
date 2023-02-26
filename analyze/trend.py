from typing import List, Any

import numpy as np


def trend_value(index: List[Any], data: List[Any], order: int = 1) -> float:
    """ < 0 for dropping,  > 1 for rising, 0<x<1 for stabilization """
    coeffs = np.polyfit(index, list(data), order)
    slope = coeffs[-2]
    return float(slope)
