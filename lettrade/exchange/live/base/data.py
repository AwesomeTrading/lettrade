import logging
from datetime import datetime
from typing import Optional, Type

import pandas as pd

from lettrade.data import DataFeed

from .api import LiveAPI

logger = logging.getLogger(__name__)


class LiveDataFeed(DataFeed):
    _api_cls: Type[LiveAPI] = LiveAPI

    def __init__(
        self,
        symbol: str,
        timeframe: str | int | pd.Timedelta,
        name: str = None,
        **kwargs,
    ) -> None:
        super().__init__(
            name=name or f"{symbol}_{timeframe}",
            timeframe=timeframe,
            **kwargs,
        )
        self.meta.update(dict(symbol=symbol))

        # Columns
        self["open"] = pd.Series(dtype="float64")
        self["high"] = pd.Series(dtype="float64")
        self["low"] = pd.Series(dtype="float64")
        self["close"] = pd.Series(dtype="float64")
        self["volume"] = pd.Series(dtype="float64")

    @property
    def symbol(self) -> str:
        return self.meta["symbol"]

    @property
    def _api(self) -> LiveAPI:
        return getattr(self, "__api")

    @_api.setter
    def _api(self, value) -> LiveAPI:
        setattr(self, "__api", value)

    def next(self, size=1, tick=0) -> bool:
        rates = self._api.bars(
            symbol=self.symbol,
            timeframe=self.timeframe.string,
            since=0,
            to=size + 1,  # Get last completed bar
        )
        if len(rates) == 0:
            logger.warning("No rates data for %s", self.name)
            return False

        return self.on_rates(rates, tick=tick)

    def on_rates(self, rates, tick=0):
        self.push(rates)
        self.l.go_stop()
        return True

    def dump_csv(
        self,
        path: str = None,
        since: Optional[int | str | datetime] = 0,
        to: Optional[int | str | datetime] = 1_000,
    ):
        if self.empty:
            if isinstance(since, str):
                since = pd.to_datetime(since).to_pydatetime()
            if isinstance(to, str):
                to = pd.to_datetime(to).to_pydatetime()

            rates = self._api.bars(
                symbol=self.symbol,
                timeframe=self.timeframe.string,
                since=since,
                to=to,
            )
            self.on_rates(rates)

        if path is None:
            path = f"data/{self.name}-{since}_{to}.csv"

        from lettrade.data.extra.csv import csv_export

        csv_export(dataframe=self, path=path)

    @classmethod
    def instance(
        cls,
        api: LiveAPI = None,
        api_kwargs: dict = None,
        **kwargs,
    ) -> "LiveDataFeed":
        """_summary_

        Args:
            api (LiveAPI, optional): _description_. Defaults to None.
            api_kwargs (dict, optional): _description_. Defaults to None.

        Raises:
            RuntimeError: Missing api requirement

        Returns:
            LiveDataFeed: DataFeed object
        """
        if api is None:
            if api_kwargs is None:
                raise RuntimeError("api or api_kwargs cannot missing")
            api = cls._api_cls(**api_kwargs)
        data = cls(**kwargs)
        data._api = api
        return data
