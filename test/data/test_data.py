import unittest

import pandas as pd

from lettrade.data import DataFeed
from lettrade.exchange.backtest.data import CSVBackTestDataFeed


class CSVBackTestDataFeedTestCase(unittest.TestCase):
    def setUp(self):
        self.data = CSVBackTestDataFeed("test/assets/EURUSD_1h-0_1000.csv")

    def test_types(self):
        self.assertIsInstance(
            self.data,
            DataFeed,
            "Data is not instance of DataFeed",
        )

        self.assertIsInstance(
            self.data.index,
            pd.DatetimeIndex,
            "Index is not instance of pd.DatetimeIndex",
        )

    def test_name(self):
        self.assertEqual(self.data.name, "EURUSD_1h", "Name is wrong")

    def test_size(self):
        self.assertEqual(len(self.data), 1_000, "Size is wrong")

    def test_copy_and_drop(self):
        df = self.data.copy(deep=True)
        df.loc[0, "open"] = 0

        # Test deepcopy is not a mirror
        self.assertEqual(df.loc[0, "open"], 0, "Set value to data.open error")
        self.assertNotEqual(self.data.loc[0, "open"], 0, "Value change when deepcopy")

        # Test set value
        df[0].open = 1
        self.assertEqual(df.loc[0, "open"], 1, "Set value to data.open error")

        # Test drop
        df.drop_since(100)
        self.assertEqual(len(df), 900, "Drop data size wrong")
        self.assertEqual(len(self.data), 1_000, "Drop data size wrong")
