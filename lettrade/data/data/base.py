import logging
import re
from typing import Optional

import pandas as pd

from .timeframe import TimeFrame

logger = logging.getLogger(__name__)


# Base class for DataFeed
_data_name_pattern = re.compile(r"^[\w\_]+$")


class BaseDataFeed(pd.DataFrame):
    """Data for Strategy. A implement of pandas.DataFrame"""

    _lt_pointers: list[int] = [0]

    def __init__(
        self,
        *args,
        name: str,
        # data: pd.DataFrame,
        timeframe: TimeFrame,
        meta: Optional[dict] = None,
        # dtype: list[tuple] = [],
        **kwargs,
    ) -> None:
        """_summary_

        Args:
            name (str): Name of DataFeed
            meta (Optional[dict], optional): metadata of DataFeed. Defaults to None.
            *args (list): `pandas.DataFrame` list parameters
            **kwargs (dict): `pandas.DataFrame` dict parameters
        """
        # Validate
        if not _data_name_pattern.match(name):
            raise RuntimeError(
                f"Bot name {name} is not valid format {_data_name_pattern}"
            )

        super().__init__(*args, **kwargs)
        # self.pointer_go_start()

        # Metadata
        if not meta:
            meta = dict()
        meta["name"] = name
        meta["timeframe"] = TimeFrame(timeframe)
        self.attrs = {"lt_meta": meta}

    def copy(self, deep=False, *args, **kwargs) -> "DataFeedBase":
        df = super().copy(deep=deep, *args, **kwargs)
        df = self.__class__(data=df, name=self.name, timeframe=self.timeframe)
        return df

    # Functions
    def _set_main(self):
        """Set this dataframe is main datafeed"""
        self.meta["is_main"] = True

    def bar(self, i=0) -> pd.Timestamp:
        raise NotImplementedError("Method is not implement yet")

    def push(self, rows: list):
        raise NotImplementedError("Method is not implement yet")

    def next(self, next=1):
        raise NotImplementedError("Method is not implement yet")

    # Properties
    @property
    def datetime(self) -> pd.DatetimeIndex:
        return self.index

    @property
    def meta(self) -> dict:
        return self.attrs["lt_meta"]

    @property
    def name(self) -> str:
        return self.meta["name"]

    @property
    def timeframe(self) -> TimeFrame:
        return self.meta["timeframe"]

    @property
    def is_main(self) -> bool:
        return self.meta.get("is_main", False)

    @property
    def now(self) -> pd.Timestamp:
        raise NotImplementedError("Method is not implement yet")

    # Pointer
    @property
    def pointer(self):
        raise NotImplementedError("Method is not implement yet")

    def pointer_go_start(self):
        raise NotImplementedError("Method is not implement yet")

    def pointer_go_stop(self):
        raise NotImplementedError("Method is not implement yet")

    @property
    def pointer_start(self) -> int:
        raise NotImplementedError("Method is not implement yet")

    @property
    def pointer_stop(self) -> int:
        raise NotImplementedError("Method is not implement yet")
