import asyncio
import logging
import sys
from decimal import Decimal
from sqlite3 import Connection

from common.data_types import SymbolAction, get_symbol_action
from common.pricing import calculated_percent_diff
from common.config import Config as Configuration
from analyze.engine import Analysis

from exchange.interface import Exchange


async def analyze_market_depth(logger: logging.Logger,
                               exchange: Exchange,
                               db_connection: Connection,
                               analysis: Analysis,
                               config: Configuration) -> None:
    # take price when bought
    cursor = db_connection.cursor()

    db_data_fetched: bool = False
    next_symbol_action = SymbolAction.BUY
    previous_action_price: Decimal = Decimal(0)
    local_peak_price: Decimal = Decimal(0)
    current_record_time: int = 0
    bought: bool = False

    while True:
        """ this is playground only """
        # Sleep for the "sleep_for" seconds.

        # this is for limits
        limits = exchange.show_current_limits()
        logger.info(f"limits => {limits}")

        market_depth = exchange.get_market_depth(limit=config.MarketDepth)
        logger.debug(f"received market depth: {market_depth}")
        logger.info("determining my assets:")

        """ this is what we have now """
        asset_db_data_last_record = exchange.determine_my_asset()
        current_symbol_price: Decimal = Decimal(0)

        my_qty: Decimal = Decimal(0)

        if not db_data_fetched:

            """ taking the time, price and last seen highest price """
            """ we take this data from db to not overuse exchange limits """
            """ CAVEAT: DB has to be in pair with exchange wallet! """
            cursor.execute("SELECT time,action,qty,action_price,highest_price_seen_so_far,received FROM "
                           "exchange_actions ORDER BY time DESC LIMIT 1")

            database_rows = cursor.fetchall()

            if len(database_rows) > 0:
                try:
                    row = database_rows[0]
                    current_record_time = row[0]
                    last_exchange_action = get_symbol_action(row[1])
                    last_record_qty = Decimal(row[2])
                    """ we remember from db price when we bought/sell something and also highest price """
                    # FIXME:
                    """
                    
                      File "/Users/mateusz/python/binance-bot/analyze/market_depth.py", line 66, in analyze_market_depth
    previous_action_price = Decimal(round(Decimal(row[3]), 8))
                                    ^^^^^^^^^^^^^^^^^^^^^^^^^
decimal.InvalidOperation: [<class 'decimal.InvalidOperation'>]"""
                    previous_action_price = Decimal(round(Decimal(row[3]), 8))
                    local_peak_price = Decimal(round(Decimal(row[4]), 8))
                    received_qty = Decimal(row[5])

                    if last_exchange_action is SymbolAction.SELL:
                        """ last action is SELL, so our qty is "from the pool" and next action is BUY """
                        my_qty = config.MainCoinAmountToUse
                        next_symbol_action = SymbolAction.BUY

                    if last_exchange_action is SymbolAction.BUY:
                        """ last action is BUY, so our qty is 'qty' and next action is SELL """
                        my_qty = last_record_qty
                        next_symbol_action = SymbolAction.SELL

                    logger.info(f"!!! fetched from db, current_record_time: {current_record_time}, "
                                f"last_record_qty: {last_record_qty}, previous_action_price: {previous_action_price}, "
                                f"local_peak_price: {local_peak_price}, my_qty: {my_qty}")

                    db_data_fetched = True
                except IndexError:
                    logger.warning("something wrong with query")

        for bid in market_depth['bids']:
            bid_price = Decimal(bid[0])
            bid_qty = Decimal(bid[1])

            if bid_qty >= my_qty:
                """ and this is our price! higher are first """
                current_symbol_price = bid_price
                break

        if next_symbol_action is SymbolAction.BUY:
            """"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
            """                         BUY algorithm                            """
            """"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

            # logger.info(f"[{config.Symbol}] asked for analysis...")
            # suggestion = analysis.suggested_buy_action()
            # if suggestion is SymbolAction.BUY:
            #     logger.warning("suggestion is that I should BUY now")

            # TODO: now previous highest price should go down or what?

            # when SIDE=BUY quantity means: I want "quantity" base for "current_symbol_price"
            # when SIDE=SELL quantity means: I want to use this "quantity" for "current_symbol_price"

            if not bought:

                for idx, ask in enumerate(market_depth['asks']):

                    if idx == 0:
                        """ not first offer - big chance it will dissapear """
                        continue

                    ask_price = Decimal(ask[0])
                    ask_qty = Decimal(ask[1])

                    quantity = Decimal(config.MainCoinAmountToUse) / ask_price

                    if ask_qty >= quantity:
                        """ and this is our price! higher are first """
                        current_symbol_price = ask_price
                        if False is True:
                            exchange.buy_target_asset(quantity, current_symbol_price, db_connection)
                        bought = True

                        break

        if next_symbol_action is SymbolAction.SELL:
            """"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
            """                         SELL algorithm                           """
            """"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

            percent_diff = calculated_percent_diff(previous_action_price, current_symbol_price)
            logger.info(f"my_qty: {my_qty}, previous_action_price: {previous_action_price}, "
                        f"current_symbol_price: {current_symbol_price}")

            if percent_diff > Decimal(0):
                """ the most importand condition: there is profit already - we can check if we should keep or sell """

                profit_value = current_symbol_price - previous_action_price
                percent_diff_rounded = round(percent_diff, 3)
                logger.info(f"I bought asset [{config.Symbol}] for {previous_action_price}, looking for occasion to "
                            f"{next_symbol_action}, current price: {current_symbol_price} [profit: {percent_diff_rounded} % "
                            f"=> {profit_value}]")

                if current_symbol_price >= local_peak_price:
                    """ new local high """
                    logger.info(f"price [{current_symbol_price}] is currently HIGHEST since I'm following, "
                                f"previous high: [{local_peak_price}]")

                    """ update db and current highest prices """
                    local_peak_price = current_symbol_price
                    cursor.execute("UPDATE exchange_actions SET highest_price_seen_so_far = ? WHERE time = ?",
                                   (str(local_peak_price), current_record_time))
                    db_connection.commit()
                else:
                    """ price dropped """
                    drop_percent = round(calculated_percent_diff(current_symbol_price, local_peak_price), 3)
                    logger.warning(f"current price [{current_symbol_price}] is smaller by [{drop_percent}%] than last "
                                   f"previous peak price [{local_peak_price}]")

                    if drop_percent > config.SellWhenPercentDrop:
                        """ drop threshold - sell/buy """
                        logger.warning(f"SELLING => I would sell now for price {current_symbol_price} as dropped from peak "
                                       f"by required {config.SellWhenPercentDrop}%")
                    """ watch for drop """

        await asyncio.sleep(config.MarketAnalyseDelay)
