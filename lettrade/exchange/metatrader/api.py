import logging
from datetime import datetime, timedelta
from time import sleep
from typing import Optional

from mt5linux import MetaTrader5 as Mt5

logger = logging.getLogger(__name__)


TIMEFRAME_L2M = {
    "1m": Mt5.TIMEFRAME_M1,
    "2m": Mt5.TIMEFRAME_M2,
    "3m": Mt5.TIMEFRAME_M3,
    "4m": Mt5.TIMEFRAME_M4,
    "5m": Mt5.TIMEFRAME_M5,
    "6m": Mt5.TIMEFRAME_M6,
    "10m": Mt5.TIMEFRAME_M10,
    "12m": Mt5.TIMEFRAME_M12,
    "15m": Mt5.TIMEFRAME_M15,
    "20m": Mt5.TIMEFRAME_M20,
    "30m": Mt5.TIMEFRAME_M30,
    "1h": Mt5.TIMEFRAME_H1,
    "2h": Mt5.TIMEFRAME_H2,
    "3h": Mt5.TIMEFRAME_H3,
    "4h": Mt5.TIMEFRAME_H4,
    "6h": Mt5.TIMEFRAME_H6,
    "8h": Mt5.TIMEFRAME_H8,
    "12h": Mt5.TIMEFRAME_H12,
    "1d": Mt5.TIMEFRAME_D1,
    "1w": Mt5.TIMEFRAME_W1,
    "1mn": Mt5.TIMEFRAME_MN1,
}


class MetaTraderAPI:
    _mt5: Mt5
    _callbacker: "MetaTraderExchange"

    __deal_time_checked = datetime.now() - timedelta(days=1)
    __orders_stored: dict[int, object] = {}
    __trades_stored: dict[int, object] = {}

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_singleton"):
            cls._singleton = object.__new__(cls)
            cls._singleton.__init__(*args, **kwargs)
        return cls._singleton

    def __init__(self, wine: Optional[str] = None):
        if wine is not None:
            self._t_wine_server(wine)

    def init(
        self,
        login: int,
        password: str,
        server: str,
        timeout: int = 60,
        retry: int = 20,
        host: str = "localhost",
        port: int = 18812,
    ):
        try:
            self._mt5 = Mt5(host=host, port=port)
        except ConnectionRefusedError as e:
            raise ConnectionRefusedError(
                "Cannot connect to MetaTrader 5 Terminal rpyc server"
            ) from e
        except TimeoutError as e:
            raise RuntimeError("Timeout start MetaTrader 5 Terminal") from e

        account = self.account()
        if not account or account.login != login:
            while retry > 0:
                login = self._mt5.initialize(
                    login=int(login),
                    password=password,
                    server=server,
                    # timeout=timeout,
                )
                if login:
                    break

                if __debug__:
                    logger.info("Login retry: %d", retry)

                sleep(1)
                retry -= 1

            if retry == 0:
                raise RuntimeError(f"Cannot login {account}")

        logger.info(
            "Login success account=%s, server=%s, version=%s",
            account,
            server,
            self._mt5.version(),
        )

        terminal = self._mt5.terminal_info()
        logger.info("Terminal information: %s", str(terminal))
        if not terminal.trade_allowed:
            logger.warning("Terminal trading mode is not allowed")

    def _t_wine_server(self, wine):
        import time
        from subprocess import Popen

        p = Popen(wine, shell=True)
        time.sleep(5)
        logger.info("Wine MetaTrader rpyc server started")

    def start(self, callbacker=None):
        self._callbacker = callbacker
        self._check_transactions()

    def stop(self):
        self._mt5.shutdown()

    def next(self):
        self._check_transactions()

    def heartbeat(self):
        return True

    def account(self):
        return self._mt5.account_info()

    def markets(self, symbol):
        return self._mt5.symbol_info(symbol)

    def tick(self, symbol):
        return self._mt5.symbol_info_tick(symbol)

    def rates_from_pos(self, symbol, timeframe, since=0, to=1000):
        rates = self._mt5.copy_rates_from_pos(
            symbol,
            TIMEFRAME_L2M[timeframe],
            since,
            to,
        )
        return rates

    def order_send(self, request: "TradeRequest"):
        return self._mt5.order_send(request)

    def orders_total(self):
        return self._mt5.orders_total()

    def orders_get(self, **kwargs):
        return self._mt5.orders_get(**kwargs)

    def positions_total(self):
        return self._mt5.positions_total()

    def positions_get(self, **kwargs):
        return self._mt5.positions_get(**kwargs)

    # Transaction
    def _check_transactions(self):
        if not self._callbacker:
            return

        # Deals
        deals = self._check_deals()
        if deals:
            self._callbacker.on_new_deals(deals)

        # Orders
        orders, removed_orders = self._check_orders()
        if orders:
            self._callbacker.on_new_orders(orders)
        if removed_orders:
            self._callbacker.on_old_orders(removed_orders)

        # Trades
        trades, removed_trades = self._check_trades()
        if trades:
            self._callbacker.on_new_trades(trades)
        if removed_trades:
            self._callbacker.on_old_trades(removed_trades)

    # Deal
    def _check_deals(self):
        to = datetime.now()  # + timedelta(days=1)

        deal_total = self._mt5.history_deals_total(self.__deal_time_checked, to)

        # No thing new in deal
        if deal_total <= 0:
            return

        raws = self._mt5.history_deals_get(self.__deal_time_checked, to)

        # Update last check time +1 second
        self.__deal_time_checked = datetime.fromtimestamp(raws[-1].time + 1)

        return raws

    # Order
    def _check_orders(self):
        order_total = self._mt5.orders_total()

        # No thing new in order
        if order_total <= 0 and len(self.__orders_stored) == 0:
            return None, None

        raws = self._mt5.orders_get()
        tickets = [raw.ticket for raw in raws]

        removed_orders = [
            raw for raw in self.__orders_stored.values() if raw.ticket not in tickets
        ]

        added_orders = []
        for raw in raws:
            if raw.ticket in self.__orders_stored:
                stored = self.__orders_stored[raw.ticket]
                if (
                    raw.sl == stored.sl
                    and raw.tp == stored.tp
                    and raw.volume_current == stored.volume_current
                    and raw.price_open == stored.price_open
                    and raw.price_stoplimit == stored.price_stoplimit
                ):
                    continue

            added_orders.append(raw)
        self.__orders_stored = {raw.ticket: raw for raw in raws}
        return added_orders, removed_orders

    # Trade
    def _check_trades(self):
        trade_total = self._mt5.positions_total()

        # No thing new in trade
        if trade_total <= 0 and len(self.__trades_stored) == 0:
            return None, None

        raws = self._mt5.positions_get()
        tickets = [raw.ticket for raw in raws]

        removed_trades = [
            raw for raw in self.__trades_stored.values() if raw.ticket not in tickets
        ]

        added_trades = []
        for raw in raws:
            if raw.ticket in self.__trades_stored:
                stored = self.__trades_stored[raw.ticket]
                if (
                    raw.time_update == stored.time_update
                    and raw.sl == stored.sl
                    and raw.tp == stored.tp
                    and raw.volume == stored.volume
                    and raw.price_open == stored.price_open
                ):
                    continue

            added_trades.append(raw)

        self.__trades_stored = {raw.ticket: raw for raw in raws}
        return added_trades, removed_trades

    def __copy__(self):
        return self.__class__._singleton

    def __deepcopy__(self, memo):
        return self.__class__._singleton
