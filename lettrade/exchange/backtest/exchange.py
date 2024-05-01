from typing import Optional

from lettrade.data import DataFeed
from lettrade.exchange import (
    Exchange,
    Execute,
    Order,
    OrderType,
    Position,
    State,
    Trade,
)


class BackTestExchange(Exchange):
    __id = 0

    def _id(self) -> str:
        self.__id += 1
        return str(self.__id)

    def next(self):
        pass

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

        if OrderType.Market:
            limit = 0
            stop = 0

        order = Order(
            id=self._id(),
            exchange=self,
            data=data,
            size=size,
            type=type,
            limit_price=limit,
            stop_price=stop,
            sl_price=sl,
            tp_price=tp,
            tag=tag,
        )
        self.on_order(order)
        self._simulate_order()

    def _simulate_order(self):
        for order in self.orders.to_list():
            if order.type == OrderType.Market:
                order._entry_bar = self.data.index[0]
                order._entry_price = self.data.close[0]
                order._replace(state=State.Close)
                self.on_order(order)

                execute = Execute(
                    id=self._id(),
                    size=order.size,
                    exchange=self,
                    data=order.data,
                    price=self.data.close[0],
                    parent=order,
                )
                self.on_execute(execute)

                trade = Trade(
                    id=self._id(),
                    size=order.size,
                    exchange=self,
                    data=order.data,
                    entry_price=execute.price,
                    parent=order,
                )
                self.on_trade(trade)
