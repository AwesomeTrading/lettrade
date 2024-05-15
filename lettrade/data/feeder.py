from abc import ABCMeta, abstractmethod

from .data import DataFeed


class DataFeeder(metaclass=ABCMeta):
    datas: list[DataFeed]
    data: DataFeed

    def init(self, datas: list[DataFeed]):
        self.datas = datas
        self.data = datas[0]

    @property
    def is_continous(self):
        """Flag check is realtime continous datafeeder"""
        return True

    @abstractmethod
    def alive(self):
        pass

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def next(self):
        pass
