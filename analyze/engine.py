import asyncio
import sqlite3

import logging
import time

from common.data_types import SymbolAction
from common.config import Config
from analyze.roc import roc_indicator_suggestion
from analyze.stoch import stoch_indicator_suggestion
import pandas as pd  # type: ignore

df = pd.DataFrame()  # Empty DataFrame


class Analysis:
    def __init__(self, logger: logging.Logger, config: Config):
        self.volume_df: pd.DataFrame = pd.DataFrame()
        self.close_price_df: pd.DataFrame = pd.DataFrame()
        self.low_price_df: pd.DataFrame = pd.DataFrame()
        self.high_price_df: pd.DataFrame = pd.DataFrame()
        self.open_price_df: pd.DataFrame = pd.DataFrame()
        self.logger = logger
        self.config = config
        self.num_records: int = 0

    async def market_data_loader(self) -> None:

        con = sqlite3.connect(self.config.DatabaseFile)
        logger = self.logger

        while True:
            logger.info("fetching new trading data...")
            df_trading_data = pd.read_sql_query("SELECT * from main.ohlcv_data ORDER BY open_time ASC", con)
            self.num_records = len(df_trading_data)

            # Verify that result of SQL query is stored in the dataframe
            df_trading_data["open_time"] = pd.to_datetime(df_trading_data["open_time"], unit='ms')
            df_trading_data.set_index(pd.DatetimeIndex(df_trading_data["open_time"]), inplace=True)

            # Calculate Returns and append to the df DataFrame
            self.open_price_df = df_trading_data.sort_values(by='close_time')["open_price"]
            self.high_price_df = df_trading_data.sort_values(by='close_time')["high_price"]
            self.low_price_df = df_trading_data.sort_values(by='close_time')["low_price"]
            self.close_price_df = df_trading_data.sort_values(by='close_time')["close_price"]
            self.volume_df = df_trading_data.sort_values(by='close_time')["volume"]

            logger.info(f"trading data fetched: {self.num_records} records")
            await asyncio.sleep(30)  # type: ignore

    def suggested_buy_action(self) -> SymbolAction:
        logger = self.logger

        advice: SymbolAction = SymbolAction.HOLD

        while self.num_records < 300000:
            logger.warning(f"still fetching data records (currently: {self.num_records})...")
            time.sleep(1)

        logger = self.logger

        advice = roc_indicator_suggestion(logger=logger,
                                          close_price_df=self.close_price_df,
                                          df_limit=10,
                                          model_length_param=9)

        logger.info(f"Analysis Engine (step=1): suggested action is: {advice}")

        if advice is SymbolAction.HOLD:
            return SymbolAction.HOLD

        advice = stoch_indicator_suggestion(logger=logger,
                                            high_price_df=self.high_price_df,
                                            low_price_df=self.low_price_df,
                                            close_price_df=self.close_price_df,
                                            df_limit=30,
                                            trend_limit=3)

        logger.info(f"Analysis Engine (step=2): suggested action is: {advice}")

        return advice
