from decimal import Decimal
from typing import List


class Config:
    def __init__(self,
                 api_key: str,
                 api_secret: str,
                 log_level: str,
                 symbol: str,
                 main_coins_list: List[str],
                 database_file: str,
                 database_update_delay_secs: int,
                 database_update_start_record: int,
                 main_coin_amount_to_use: Decimal,
                 market_analyse_delay: int,
                 market_depth: int,
                 sell_when_percent_drop: Decimal,
                 rise_watch_percent_level: Decimal):
        self.ApiKey = api_key
        self.ApiSecret = api_secret
        self.LogLevel = log_level
        self.Symbol = symbol
        self.MainCoins = main_coins_list
        self.DatabaseFile = database_file
        self.DatabaseUpdateDelay = database_update_delay_secs
        self.DatabaseUpdateStartRecord = database_update_start_record
        self.MainCoinAmountToUse = main_coin_amount_to_use
        self.MarketAnalyseDelay = market_analyse_delay
        self.MarketDepth = market_depth
        self.SellWhenPercentDrop = sell_when_percent_drop
        self.RiseWatchPercentLevel = rise_watch_percent_level
