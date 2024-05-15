from .account import MetaTraderAccount
from .api import MetaTraderAPI
from .data import MetaTraderDataFeed
from .exchange import MetaTraderExchange
from .feeder import MetaTraderDataFeeder


class MetaTrader:
    _api: MetaTraderAPI
    _feeder: MetaTraderDataFeeder = None
    _exchange: MetaTraderExchange = None
    _account: MetaTraderAccount = None

    _tick: bool

    def __init__(self, tick=5, *args, **kwargs) -> None:
        self._tick = tick

        self._api = MetaTraderAPI()
        self._api.start(*args, **kwargs)

    def data(
        self,
        symbol: str,
        timeframe: str,
        name: str = None,
    ) -> MetaTraderDataFeed:
        return MetaTraderDataFeed(
            name=name or symbol,
            symbol=symbol,
            timeframe=timeframe,
            feeder=self.feeder(),
            api=self._api,
        )

    def feeder(self) -> MetaTraderDataFeeder:
        if not self._feeder:
            self._feeder = MetaTraderDataFeeder(api=self._api, tick=self._tick)
        return self._feeder

    def exchange(self) -> MetaTraderExchange:
        if not self._exchange:
            self._exchange = MetaTraderExchange(api=self._api)
        return self._exchange

    def account(self) -> MetaTraderAccount:
        if not self._account:
            self._account = MetaTraderAccount(api=self._api)
        return self._account
