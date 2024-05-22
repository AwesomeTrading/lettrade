from typing import Optional

from lettrade.account import Account


class BackTestAccount(Account):
    def __repr__(self):
        return "<BackTestAccount " + str(self) + ">"


class ForexBackTestAccount(Account):
    def __repr__(self):
        return "<ForexBackTestAccount " + str(self) + ">"

    def pl(self, size, entry_price: float, exit_price: Optional[float] = None) -> float:
        if exit_price is None:
            exit_price = self._exchange.data.open[0]

        pl = size * (exit_price - entry_price) * 100_000

        return pl