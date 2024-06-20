import logging

from lettrade.account import LetAccountInsufficientException
from lettrade.commander import Commander
from lettrade.data import DataFeed, DataFeeder, LetTradeNoMoreDataFeed
from lettrade.exchange import (
    Exchange,
    Execution,
    LetOrderValidateException,
    Order,
    Position,
)
from lettrade.strategy import Strategy

logger = logging.getLogger(__name__)


class Brain:
    """Brain of bot"""

    strategy: Strategy
    exchange: Exchange
    feeder: DataFeeder
    commander: Commander

    # datas: list[DataFeed]
    data: DataFeed

    def __init__(
        self,
        strategy: Strategy,
        exchange: Exchange,
        feeder: DataFeeder,
        commander: Commander,
        **kwargs,
    ) -> None:
        """_summary_

        Args:
            strategy (Strategy): _description_
            exchange (Exchange): _description_
            feeder (DataFeeder): _description_
            commander (Commander): _description_
        """
        self.strategy = strategy
        self.exchange = exchange
        self.feeder = feeder
        self.commander = commander

        # self.datas = self.feeder.datas
        self.data = self.feeder.data

    def start(self):
        self.data._set_main()

        self.strategy.init()

        self.feeder.start()
        self.exchange.start()

        self.strategy._start()

    def run(self):
        """Run the trading bot"""

        while self.feeder.alive():
            # Load feeder next data
            try:
                self.feeder.next()
                self.exchange.next()
                self.strategy._next()
                self.exchange.next_next()
            except LetOrderValidateException as e:
                logger.error(
                    "[%s] Order validates exception",
                    self.data.now,
                    exc_info=e,
                )
                continue
            except LetAccountInsufficientException as e:
                logger.error("Account equity is insufficient", exc_info=e)
                break
            except LetTradeNoMoreDataFeed:
                break
            except Exception as e:
                logger.exception("Bot running error", exc_info=e)
                break

        self.strategy._stop()

    def stop(self):
        """Stop the trading bot"""
        self.feeder.stop()
        self.exchange.stop()

    # Events
    def on_execution(self, execution: Execution):
        """Receive new `Execution` event and send to `Strategy`"""
        self.on_transaction(execution)
        self.strategy.on_execution(execution)

    def on_order(self, order: Order):
        """Receive new `Order` event and send to `Strategy`"""
        self.on_transaction(order)
        self.strategy.on_order(order)

    def on_position(self, position: Position):
        """Receive new `Position` event and send to `Strategy`"""
        self.on_transaction(position)
        self.strategy.on_position(position)

    def on_notify(self, *args, **kwargs):
        """Receive new notify and send to Strategy"""
        self.strategy.on_notify(*args, **kwargs)

    def on_transaction(self, transaction):
        """Receive new transaction event and send to `Strategy`"""
        if self.commander is not None:
            # TODO: send message to commander when new transaction
            self.commander.send_message(f"New transaction: {str(transaction)}")

        self.strategy.on_transaction(transaction)
