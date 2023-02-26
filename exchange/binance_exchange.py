import time
from logging import Logger
from sqlite3 import Connection
from typing import Any, Tuple, Optional
from decimal import Decimal

from binance.error import ClientError  # type: ignore
from binance.spot import Spot  # type: ignore
from exchange.filters import BinanceFilter
from common.data_types import SymbolAction
from common.config import Config
from common.pricing import truncate_price_or_qty

from exchange.interface import Exchange


class Binance(Exchange):
    def __init__(self, logger: Logger, config: Config):
        self.binance_client = Spot(key=config.ApiKey, secret=config.ApiSecret)

        self.symbol_name = config.Symbol
        self.logger = logger
        self.main_coins = config.MainCoins
        self.exchange_info = self.binance_client.exchange_info(symbol=self.symbol_name)
        self._fetch_filters()

    def _fetch_filters(self) -> None:
        logger = self.logger

        """ fasthack """
        self._filter_step_size_to_num: dict[str, int] = {
            "1.00000000": 0,
            "0.10000000": 1,
            "0.01000000": 2,
            "0.00100000": 3,
            "0.00010000": 4,
            "0.00001000": 5,
            "0.00000100": 6,
            "0.00000010": 7,
            "0.00000001": 8,
        }

        logger.info("fetching filters...")
        for filter_data in self.exchange_info["symbols"][0]["filters"]:
            if filter_data["filterType"] == "PRICE_FILTER":
                self._filter_price = BinanceFilter(name=filter_data["filterType"],
                                                   minValue=Decimal(filter_data["minPrice"]),
                                                   maxValue=Decimal(filter_data["maxPrice"]),
                                                   confValue=Decimal(filter_data["tickSize"]))

            if filter_data["filterType"] == "PERCENT_PRICE":
                self._filter_percent_price = BinanceFilter(name=filter_data["filterType"],
                                                           minValue=Decimal(filter_data["multiplierUp"]),
                                                           maxValue=Decimal(filter_data["multiplierDown"]),
                                                           confValue=Decimal(filter_data["avgPriceMins"]))

            if filter_data["filterType"] == "LOT_SIZE":
                self._filter_lot_size = BinanceFilter(name=filter_data["filterType"],
                                                      minValue=Decimal(filter_data["minQty"]),
                                                      maxValue=Decimal(filter_data["maxQty"]),
                                                      confValue=Decimal(filter_data["stepSize"]))

            if filter_data["filterType"] == "MIN_NOTIONAL":
                filter_value: Decimal = Decimal(0)
                if filter_data["applyToMarket"]:
                    filter_value = Decimal(1)
                self._filter_min_notional = BinanceFilter(name=filter_data["filterType"],
                                                          minValue=Decimal(filter_data["minNotional"]),
                                                          maxValue=filter_value,
                                                          confValue=Decimal(filter_data["avgPriceMins"]))

            if filter_data["filterType"] == "MARKET_LOT_SIZE":
                self._filter_market_lot_size = BinanceFilter(name=filter_data["filterType"],
                                                             minValue=Decimal(filter_data["minQty"]),
                                                             maxValue=Decimal(filter_data["maxQty"]),
                                                             confValue=Decimal(filter_data["stepSize"]))

            logger.info("filters fetched.")

    def get_klines(self, symbol_name: str, interval: str, limit: int, start_time: int) -> Any:
        return self.binance_client.klines(symbol=self.symbol_name,
                                          interval=interval,
                                          limit=limit,
                                          startTime=start_time)

    def show_current_limits(self) -> dict:
        from binance.spot import Spot as Client
        return dict(Client(show_limit_usage=True).time()['limit_usage'])

    def get_market_depth(self, limit: int) -> dict:
        self.logger.info(f"[{self.symbol_name}] exchange: getting market depth...")
        return dict(self.binance_client.depth(symbol=self.symbol_name, limit=limit))

    def determine_my_asset(self) -> Tuple[Decimal, SymbolAction]:
        """ determine current asset and possbility potential action (sell/buy) """
        exchange = self.binance_client
        result: dict = exchange.account()
        symbol_action = SymbolAction.SELL
        logger = self.logger

        decimal_zero = Decimal(0)

        for b in result['balances']:
            asset = b['asset']
            free: Decimal = Decimal(b['free'])
            locked: Decimal = Decimal(b['locked'])
            if asset in self.symbol_name:
                logger.info(f"asset: {asset}, free: {free}, locked: {locked}")
                """ only we find something from our single symbol, rest are ignored """
                if asset in self.main_coins:
                    """ this is a stable coin so we should buy target """
                    symbol_action = SymbolAction.BUY

                if locked == decimal_zero and free > decimal_zero:
                    """ we have some bought goods so we should sell it """
                    return free, symbol_action

        return decimal_zero, SymbolAction.HOLD

    def buy_target_asset(self, quantity: Decimal, price: Decimal, db_connection: Connection) -> None:
        logger = self.logger
        client = self.binance_client

        logger.info(f"ACTION request, price: {price}, qty: {quantity}")

        normalized_price = truncate_price_or_qty(price, self._filter_step_size_to_num.get(
            str(self._filter_price.confValue), 0))

        normalized_qty = truncate_price_or_qty(quantity, self._filter_step_size_to_num.get(
            str(self._filter_price.confValue), 0))

        logger.info(f"ACTION to execute: price: {normalized_price}, qty: {normalized_qty}")

        if self._filter_price.minValue < normalized_price < self._filter_price.maxValue:
            try:
                response = client.new_order(symbol=self.symbol_name,
                                            side="BUY",
                                            type="LIMIT",
                                            timeInForce="GTC",
                                            quantity=float(normalized_qty),
                                            price=float(normalized_price))
                logger.info(response)

                params = (round(time.time() * 1000), "BUY", 0, str(normalized_price), 0, str(normalized_qty))
                cursor = db_connection.cursor()
                cursor.execute("INSERT INTO main.exchange_actions VALUES (?,?,?,?,?,?)", params)
                db_connection.commit()

            except ClientError as error:
                logger.error(
                    "Found error. status: {}, error code: {}, error message: {}".format(
                        error.status_code, error.error_code, error.error_message
                    )
                )


def message_handler(message):
    print(message)
