import asyncio
import decimal
import logging
import os
import sqlite3
import sys
from decimal import Decimal
from sqlite3 import Connection
from typing import List

from pythonjsonlogger import jsonlogger  # type: ignore

from analyze.engine import Analysis
from analyze.market_depth import analyze_market_depth
from common.config import Config as Configuration
from common.data_fetcher import PairDataUpdater
from exchange.binance_exchange import Binance


async def main():  # type: ignore

    decimal.getcontext().prec = 8
    api_key: str = str(os.environ.get("BOT_API_KEY"))
    api_secret: str = str(os.environ.get("BOT_API_SECRET"))

    log_level: str = "INFO"
    main_coins_list: List[str] = ["USDT"]

    if len(str(os.environ.get("BOT_PYTHON_LOG_LEVEL"))) > 0:
        log_level = str(os.environ.get("BOT_PYTHON_LOG_LEVEL"))

    if len(str(os.environ.get("BOT_PYTHON_MAIN_COINS_LIST"))) > 0:
        main_coins_list = str(os.environ.get("BOT_PYTHON_MAIN_COINS_LIST")).split(",")

    symbol: str = str(os.environ.get("BOT_PYTHON_SYMBOL"))

    database_file: str = str(os.environ.get("BOT_PYTHON_DATABASE_FILE"))
    if len(database_file) < 5:
        print("no BOT_PYTHON_DATABASE_FILE env variable set")
        sys.exit(1)

    database_update_delay_secs: int = int(str(os.environ.get("BOT_PYTHON_DATABASE_UPDATE_DELAY_SECS")))
    if database_update_delay_secs < 0 or database_update_delay_secs > 500:
        print("BOT_PYTHON_DATABASE_UPDATE_DELAY_SECS invalid?")
        sys.exit(1)

    database_update_start_record: int = int(str(os.environ.get("BOT_PYTHON_DATABASE_UPDATE_START_RECORD")))
    if database_update_start_record < 0:
        print("BOT_PYTHON_DATABASE_UPDATE_START_RECORD invalid?")
        sys.exit(1)

    main_coin_amount_to_use: Decimal = Decimal(str(os.environ.get("BOT_PYTHON_MAIN_COIN_AMOUNT_TO_USE")))
    if main_coin_amount_to_use < 0 or main_coin_amount_to_use > 50000:
        print("BOT_PYTHON_MAIN_COIN_AMOUNT_TO_USE invalid?")
        sys.exit(1)

    market_analyse_delay: int = int(str(os.environ.get("BOT_PYTHON_MARKET_ANALYSE_DELAY")))
    if market_analyse_delay < 0 or market_analyse_delay > 120:
        print("BOT_PYTHON_MARKET_ANALYSE_DELAY invalid?")
        sys.exit(1)

    market_depth: int = int(str(os.environ.get("BOT_PYTHON_MARKET_DEPTH")))
    if market_depth < 0 or market_depth > 500:
        print("BOT_PYTHON_MARKET_DEPTH invalid?")
        sys.exit(1)

    sell_when_percent_drop: Decimal = Decimal(str(os.environ.get("BOT_PYTHON_SELL_WHEN_PERCENT_DROP")))
    if sell_when_percent_drop < 0 or sell_when_percent_drop > 10:
        print("BOT_PYTHON_SELL_WHEN_PERCENT_DROP invalid?")
        sys.exit(1)

    rise_watch_percent_level: Decimal = Decimal(str(os.environ.get("BOT_PYTHON_RISE_WATCH_PERCENT_LEVEL")))
    if rise_watch_percent_level < 0 or rise_watch_percent_level > 200:
        print("BOT_PYTHON_RISE_WATCH_PERCENT_LEVEL invalid?")
        sys.exit(1)

    opts = [opt for opt in sys.argv[1:] if opt.startswith("-")]
    args = [arg for arg in sys.argv[1:] if not arg.startswith("-")]

    if "--symbol" in opts:
        symbol = " ".join(arg for arg in args)

    if len(symbol) < 3:
        print("no BOT_PYTHON_SYMBOL or --symbol set")
        sys.exit(1)

    config = Configuration(
        api_key=api_key,
        api_secret=api_secret,
        log_level=log_level,
        symbol=symbol,
        main_coins_list=main_coins_list,
        database_file=database_file,
        database_update_delay_secs=database_update_delay_secs,
        database_update_start_record=database_update_start_record,
        main_coin_amount_to_use=main_coin_amount_to_use,
        market_analyse_delay=market_analyse_delay,
        market_depth=market_depth,
        sell_when_percent_drop=sell_when_percent_drop,
        rise_watch_percent_level=rise_watch_percent_level
    )

    """
    logger
    """
    logging.basicConfig(
        level=log_level,
    )
    logger = logging.getLogger()
    log_handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s')
    log_handler.setFormatter(formatter)
    logger.addHandler(log_handler)

    exchange_client = Binance(logger=logger, config=config)

    sqlite_connection: Connection = sqlite3.connect(config.DatabaseFile, isolation_level=None)

    data_updater = PairDataUpdater(logger=logger,
                                   sqlite_connection=sqlite_connection,
                                   exchange_client=exchange_client,
                                   symbol_name=config.Symbol,
                                   start_record=config.DatabaseUpdateStartRecord,
                                   fetch_delay_secs=config.DatabaseUpdateDelay)

    analysis_engine = Analysis(logger=logger, config=config)

    await asyncio.gather(
        asyncio.create_task(analysis_engine.market_data_loader()),
        asyncio.create_task(data_updater.update_ohlcv_data()),
        asyncio.create_task(analyze_market_depth(logger=logger,
                                                 exchange=exchange_client,
                                                 db_connection=sqlite_connection,
                                                 analysis=analysis_engine,
                                                 config=config))
    )


if __name__ == "__main__":
    asyncio.run(main())
