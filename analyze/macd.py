from logging import Logger

import pandas as pd  # type: ignore
import pandas_ta as ta  # type: ignore
from common.data_types import SymbolAction

"""
A general interpretation of MACD is that when MACD is positive and the histogram value is increasing,
then upside momentum is increasing. When MACD is negative and the histogram value is decreasing,
then downside momentum is increasing.

https://www.tradingview.com/support/solutions/43000502344-macd-moving-average-convergence-divergence/
"""


def macd_indicator_suggestion(logger: Logger, close_price_df: pd.DataFrame, limit: int) -> SymbolAction:
    if limit == 0:
        """ 17280 minutes is 12 days for short term default value """
        limit = 17280

    tail_limit: int = 10

    results = ta.macd(close_price_df).tail(limit)

    macd_pd: pd.DataFrame = results["MACD_12_26_9"]
    histogram_pd: pd.Series = results["MACDh_12_26_9"]
    # signal_pd: pd.DataFrame = results["MACDs_12_26_9"]

    positive_values_count: int = 0
    negative_values_count: int = 0
    for row in macd_pd.tail(tail_limit):
        if row > 0:
            positive_values_count = positive_values_count + 1
        if row < 0:
            negative_values_count = negative_values_count + 1

    logger.info(f"[MACD] last_macd_values (10): {macd_pd.tail(tail_limit)}")
    logger.info(f"[MACD] last_histogram_pd values (10): {histogram_pd.tail(tail_limit)}")

    if positive_values_count == tail_limit:
        """ macd is positive """
        logger.info("[MACD] is positive")

        if histogram_pd.is_monotonic_increasing:
            logger.info("[MACD] trend is rising (is_monotonic_increasing=True)")
            """ histogram value is rising - more bullish trend is expected so BUY now! """
            return SymbolAction.BUY

    if negative_values_count == tail_limit:
        logger.info("[MACD] is -NEGATIVE")

        if histogram_pd.is_monotonic_decreasing:
            logger.info("[MACD] trend is falling (is_monotonic_increasing=False)")
            """ histogram value is falling - bearish trend so sell if you have """
            return SymbolAction.SELL

    """ default: no conclusion mate or bearish trend so wait """
    return SymbolAction.HOLD
