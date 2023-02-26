from logging import Logger

import pandas as pd  # type: ignore
import pandas_ta as ta  # type: ignore
from common.data_types import SymbolAction

"""
Rate of Change (ROC) is obviously closely tied to price. When prices are rising or advancing, ROC values remain above 
the Zero Line (positive) and when they are falling or declining, they remain below the Zero Line (negative).

https://www.tradingview.com/scripts/rateofchange/?solution=43000502343
"""

""" how many values need to be positive/negative from model lenght param """

REQUIRED_NEGATIVE_COUNT = 5
REQUIRED_POSITIVE_COUNT = 5


def roc_indicator_suggestion(logger: Logger, close_price_df: pd.DataFrame, df_limit: int, model_length_param: int) \
        -> SymbolAction:
    if model_length_param == 0:
        model_length_param = 9

    results: pd.Series = ta.roc(close=close_price_df, length=model_length_param).tail(df_limit)

    negatives_values_count: int = 0
    positive_values_count: int = 0
    results_len: int = len(results)

    for value in results:
        logger.info(f"[ROC] value: {value}")
        if value > 0:
            positive_values_count = positive_values_count + 1
        if value < 0:
            negatives_values_count = negatives_values_count + 1

    if positive_values_count == results_len:
        logger.info("[ROC] +positive+ values dominating, price is increasing, suggesting SELL")
        return SymbolAction.SELL

    if negatives_values_count == results_len:
        logger.info("[ROC] +positive+ values dominating, price is decreasing, suggesting BUY")
        return SymbolAction.BUY

    if positive_values_count >= REQUIRED_POSITIVE_COUNT:
        logger.info("[ROC] +positive+ values count threshold reached, price is increasing, suggesting SELL")
        return SymbolAction.SELL

    if negatives_values_count >= REQUIRED_NEGATIVE_COUNT:
        logger.info("[ROC] -negative- values count threshold reached, price is decreasing, suggesting BUY")
        return SymbolAction.BUY

    logger.info("[ROC] no conclusion - HOLD suggested.")
    return SymbolAction.HOLD
