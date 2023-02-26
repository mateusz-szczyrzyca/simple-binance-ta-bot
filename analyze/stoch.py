from decimal import Decimal
from logging import Logger

import pandas as pd  # type: ignore
import pandas_ta as ta  # type: ignore
from common.data_types import SymbolAction

"""
The basic understanding is that Stochastic uses closing prices to determine momentum. When prices close in the upper
half of the look-back period's high/low range, then the Stochasitc Oscillator (%K) rises also indicating an increase
in momentum or buying/selling pressure. When prices close in the lower half of the period's high/low range, %K falls,
indicating weakening momentum or buying/selling pressure.

20-80

Overbought conditions are when the Stochastic Oscillator crosses the upper threshold.
Oversold conditions are when the Stochastic Oscillator crosses the lower threshold.

Bullish Divergence occurs when price records a lower low, but Stochastic records a higher low.
Bearish Divergence occurs when price records a higher high, but Stochastic records a lower high.

Bull/Bear Setups are very similar to divergences however, they are an inversion.

A Bull Setup occurs when price records a lower high, but Stochastic records a higher high. The setup then results in a
dip in price which can be seen as a Bullish entry point before price rises.

A Bear Setup occurs when price records a higher low, but Stochastic records a lower low. The setup then results in a 
bounce in price which can be seen as a Bearish entry point before price falls.

https://www.tradingview.com/support/solutions/43000502332-stochastic-stoch/
"""

""" how many values need to be positive/negative from model lenght param """
TREND_LIMIT = 5
UPPER_BAND = 80
BOTTOM_BAND = 20


def stoch_indicator_suggestion(logger: Logger,
                               high_price_df: pd.DataFrame,
                               low_price_df: pd.DataFrame,
                               close_price_df: pd.DataFrame,
                               df_limit: int,
                               trend_limit: int) -> SymbolAction:
    if trend_limit == 0:
        trend_limit = TREND_LIMIT

    results: pd.Series = ta.stoch(high=high_price_df,
                                  low=low_price_df,
                                  close=close_price_df).tail(df_limit)

    k: pd.Series = results["STOCHk_14_3_3"]
    d: pd.Series = results["STOCHd_14_3_3"]

    logger.info(f"[STOCH] last 3 values k: {k.tail(3)}")
    logger.info(f"[STOCH] last 3 values d: {d.tail(3)}")

    if k.tail(1).item() > UPPER_BAND and d.tail(1).item() > UPPER_BAND:
        """ overbought, but let's check the trend... """
        if k.tail(trend_limit).is_monotonic_increasing or d.tail(trend_limit).is_monotonic_increasing:
            """ still increasing - SELL as it's overbought """
            return SymbolAction.SELL

    if k.tail(1).item() < BOTTOM_BAND and d.tail(1).item() < BOTTOM_BAND:
        """ oversold, check the trend """
        if k.tail(trend_limit).is_monotonic_decreasing or d.tail(trend_limit).is_monotonic_decreasing:
            """ BUY """
            return SymbolAction.BUY

    return SymbolAction.HOLD
