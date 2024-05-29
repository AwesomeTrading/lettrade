import logging

from lettrade.base.error import LetTradeNoMoreDataFeed
from lettrade.data import DataFeeder

from .data import BackTestDataFeed

logger = logging.getLogger(__name__)


class BackTestDataFeeder(DataFeeder):
    """BackTest DataFeeder"""

    datas: list[BackTestDataFeed]
    data: BackTestDataFeed

    @property
    def is_continous(self):
        """Flag check is realtime continous datafeeder"""
        return False

    def start(self, size=100):
        # self._cleanup_data()

        next = self.data.datetime[size]
        for data in self.datas:
            data.next(
                size=size,
                next=next,
                missing="bypass",
            )

    # def _cleanup_data(self):
    #     # Synchronize start time
    #     start = self.data.now
    #     tf = self.data.timeframe
    #     for data in self.datas:
    #         if data is self.data:
    #             continue

    #         if data.timeframe <= tf:
    #             data_start = start
    #         else:
    #             data_start = start - data.timeframe

    #         df = data[data["datetime"] < data_start]
    #         logger.info(
    #             "BackTestDataFeed %s dropped %d rows from start",
    #             data.name,
    #             len(df.index),
    #         )
    #         data.drop(index=df.index, inplace=True)
    #         data.reset_index(inplace=True)

    def next(self):
        # End of main data
        if self.data.index.stop <= 0:
            return False

        next = self.data.datetime[1]

        has_next = True
        for data in self.datas:
            if not data.next(next=next):
                has_next = False

        if not has_next:
            # Skip lastest available bar, because if next some data feeded some are not
            raise LetTradeNoMoreDataFeed()

    def alive(self):
        return self.data.alive()
