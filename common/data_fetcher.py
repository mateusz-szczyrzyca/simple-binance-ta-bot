import asyncio
import logging
import sqlite3
from logging import Logger
from sqlite3 import Connection

from datetime import datetime
from exchange.interface import Exchange


class PairDataUpdater:
    # queue?
    def __init__(self,
                 logger: Logger,
                 sqlite_connection: Connection,
                 exchange_client: Exchange,
                 symbol_name: str,
                 start_record: int,
                 fetch_delay_secs: int):
        self.fetch_delay = fetch_delay_secs
        self.exchange_interface = exchange_client
        self.logger = logger,
        self.sqlite_connection = sqlite_connection
        self.symbol_name = symbol_name
        self.start_record = start_record

    async def update_ohlcv_data(self) -> None:
        cursor = self.sqlite_connection.cursor()
        cursor.execute("SELECT last_open_time FROM ohlcv_stats WHERE name = ?", (self.symbol_name,))
        exchange_interface = self.exchange_interface
        logger: logging.Logger = self.logger[0]

        row = cursor.fetchone()

        try:
            last_record = row[0]
        except (IndexError, TypeError):
            last_record = self.start_record

        if last_record == 0:
            last_record = self.start_record

        while True:

            klines_data = exchange_interface.get_klines(symbol_name=self.symbol_name,
                                                        interval='1m',  # it's intentional
                                                        limit=720,  # intentional
                                                        start_time=last_record)

            start_date: datetime = datetime.now()
            end_date: datetime = datetime.now()

            for idx, data in enumerate(klines_data):
                data_open_time = data[0]
                data_open_price = data[1]
                data_high_price = data[2]
                data_low_price = data[3]
                data_close_price = data[4]
                data_volume = data[5]
                data_close_time = data[6]
                data_quote_asset_volume = data[7]
                data_number_of_trades = data[8]

                last_record = data_open_time
                date = datetime.fromtimestamp(int(data_open_time) // 1000)

                if idx == 0:
                    start_date = date
                end_date = date

                logger.debug(f"inserting data from {data}...")

                params = (data_open_time,
                          data_close_time,
                          self.symbol_name,
                          data_open_price,
                          data_high_price,
                          data_low_price,
                          data_close_price,
                          data_volume,
                          data_quote_asset_volume,
                          data_number_of_trades)

                try:
                    cursor.execute("INSERT INTO ohlcv_data VALUES (?,?,?,?,?,?,?,?,?,?)", params)
                except sqlite3.IntegrityError:
                    pass

            cursor.execute("UPDATE ohlcv_stats SET last_open_time = ? WHERE name = ?", (last_record, self.symbol_name))
            self.sqlite_connection.commit()

            logger.info(f"[{self.symbol_name}] data updater: took period between {start_date} and {end_date}, delay: "
                        f"{self.fetch_delay}")

            await asyncio.sleep(self.fetch_delay)
