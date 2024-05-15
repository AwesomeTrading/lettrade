import logging
from typing import Generator, Optional

from lettrade.data import DataFeed
from lettrade.exchange import Exchange, OrderType

logger = logging.getLogger(__name__)

from .api import MetaTraderAPI
from .trade import MetaTraderExecute, MetaTraderOrder, MetaTraderTrade


class MetaTraderExchange(Exchange):
    _api: MetaTraderAPI

    def __init__(self, api: MetaTraderAPI, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._api = api
        self._api._callbacker = self

    def start(self):
        self._sync_orders()
        self._sync_trades()
        return super().start()

    def next(self):
        self._api._check_transactions()
        super().next()

    def new_order(
        self,
        size: float,
        type: OrderType = OrderType.Market,
        limit: Optional[float] = None,
        stop: Optional[float] = None,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
        tag: object = None,
        data: DataFeed = None,
        *args,
        **kwargs
    ):
        if not data:
            data = self.data

        if type == OrderType.Market:
            limit = 0
            stop = 0

        order = MetaTraderOrder(
            id=-1,
            exchange=self,
            api=self._api,
            data=data,
            size=size,
            type=type,
            limit_price=limit,
            stop_price=stop,
            sl_price=sl,
            tp_price=tp,
            tag=tag,
            open_price=self.data.open[0],
            open_bar=self.data.bar(),
        )
        ok = order.place()

        if __debug__:
            logger.info("New order %s at %s", order, self.data.now)

        return ok

    def _sync_orders(self):
        total = self._api.orders_total()
        if total <= 0:
            return

        raws = self._api.orders_get()
        if not raws:
            logger.warning("Cannot get orders")
            return

        for order in self._parse_orders(raws):
            print("\n---> order:\n", order)
            if order.id not in self.orders:
                # TODO: detect exist and change
                self.orders[order.id] = order
        print(self.orders)

    def _parse_orders(self, raws) -> list[MetaTraderOrder]:
        return [self._parse_order(raw) for raw in raws]

    def _parse_order(self, raw) -> MetaTraderOrder:
        return MetaTraderOrder._from_raw(
            raw=raw,
            exchange=self,
            api=self._api,
        )

    def _sync_trades(self):
        total = self._api.positions_total()
        if total <= 0:
            return

        raws = self._api.positions_get()
        if not raws:
            logger.warning("Cannot get trades")
            return

        for raw in raws:
            print("\n---> trade:\n", raw)
            if raw.ticket not in self.trades:
                trade = MetaTraderTrade._from_raw(
                    raw=raw,
                    exchange=self,
                    api=self._api,
                )
                # TODO: detect exist and change
                self.trades[trade.id] = trade
        print(self.trades)

    # Events
    def _on_deals(self, raws):
        print("\n---> raw deals:", raws)
