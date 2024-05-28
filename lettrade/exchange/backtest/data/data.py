import logging
from typing import Optional

import pandas as pd

from lettrade.data import DataFeed, TimeFrame

logger = logging.getLogger(__name__)


class BackTestDataFeed(DataFeed):
    def __init__(
        self,
        data: pd.DataFrame,
        name: str,
        timeframe: Optional[str | int | pd.Timedelta] = None,
        meta: Optional[dict] = None,
        drop_since: Optional[int] = None,
        **kwargs,
    ) -> None:
        if timeframe is None:
            timeframe = self._find_timeframe(data)
            logger.info("DataFeed %s auto detect timeframe %s", name, timeframe)
        super().__init__(
            data=data,
            name=name,
            timeframe=timeframe,
            meta=meta,
            **kwargs,
        )
        if drop_since is not None:
            self.drop_since(drop_since)

    def _find_timeframe(self, df):
        dt = df.datetime if "datetime" in df.columns else df.index
        if len(df.index) < 3:
            raise RuntimeError("DataFeed not enough data to detect timeframe")
        for i in range(0, 5):
            tf = dt[i + 1] - dt[i]
            if tf == dt[i + 2] - dt[i + 1]:
                return tf
        raise RuntimeError("DataFeed cannot detect timeframe")

    def drop_since(self, since):
        df = self[self.index < since]
        self.drop(index=df.index, inplace=True)
        # self.reset_index(inplace=True)
        logger.info("BackTestDataFeed %s dropped %s rows", self.name, len(df.index))

    def alive(self):
        return self.index.stop > 1

    def next(
        self,
        size=1,
        next: pd.Timestamp = None,
        timeframe: TimeFrame = None,
    ) -> bool:
        has_next = True
        if not self.is_main:
            if next is None:
                raise RuntimeError("DataFeed parameter next is None")
            size = 0

            while True:
                dt = self.datetime[size]
                # No more next data
                if not dt:
                    has_next = False
                    break

                if dt == next:
                    break
                if dt > next:
                    # Higher timeframe
                    if self.timeframe > timeframe:
                        if dt - next > self.timeframe:
                            raise RuntimeError(
                                f"DataFeed {self.name} missing data from {next} to {dt}",
                            )
                        break

                    raise RuntimeError(
                        f"DataFeed {self.name} missing data from {next} to {dt}",
                    )
                size += 1
        if size > 0:
            self.index.next(size)
            # self.index = pd.RangeIndex(
            #     self.index.start - size,
            #     self.index.stop - size,
            # )
        # else:
        #     if self.timeframe == timeframe:
        #         print(
        #             "------>", self.name, self.datetime[-1], self.now, next, self.index
        #         )
        return has_next


class CSVBackTestDataFeed(BackTestDataFeed):
    """Implement help to load DataFeed from csv file"""

    def __init__(
        self,
        path: str = None,
        name: str = None,
        timeframe: Optional[str | int | pd.Timedelta] = None,
        delimiter: str = ",",
        index_col: int = 0,
        header: int = 0,
        meta: dict = None,
        data: DataFeed = None,
        **kwargs: dict,
    ) -> None:
        """_summary_

        Args:
            name (str): Path to csv file
            delimiter (str, optional): _description_. Defaults to ",".
            index_col (int, optional): _description_. Defaults to 0.
            header (int, optional): _description_. Defaults to 0.
            **kwargs (dict): [DataFeed](./data.md#lettrade.data.data.DataFeed) dict parameters
        """
        if name is None:
            name = path

        if data is None:
            data = pd.read_csv(
                path,
                index_col=index_col,
                parse_dates=["datetime"],
                delimiter=delimiter,
                header=header,
            )
        # df.reset_index(inplace=True)

        super().__init__(
            data=data,
            name=name,
            timeframe=timeframe,
            meta=meta,
            **kwargs,
        )


class YFBackTestDataFeed(BackTestDataFeed):

    def __init__(
        self,
        name,
        ticker,
        start,
        end=None,
        period=None,
        interval="1d",
        **kwargs,
    ) -> None:
        params = dict(
            start=start,
            end=end,
            period=period,
            interval=interval,
        )

        # Download
        import yfinance as yf

        df = yf.download(ticker, **params)

        # Parse to lettrade datafeed
        from .yfinance import yf_parse

        df = yf_parse(df)
        # TODO: WIP
        df["date"] = pd.to_datetime(df["date"], unit="ms", utc=True)

        # # Reindex to 0,1,2,3...
        # df.reset_index(inplace=True)

        # Metadata
        meta = dict(yf=dict(ticker=ticker, **params))

        super().__init__(
            name=name,
            meta=meta,
            data=df,
            **kwargs,
        )
