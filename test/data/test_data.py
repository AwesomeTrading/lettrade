import unittest

import pandas as pd
from pandas import testing as pdtest

from lettrade.exchange.backtest.data import CSVBackTestDataFeed


class DataFeedTestCase(unittest.TestCase):
    def setUp(self):
        self.data = CSVBackTestDataFeed("test/assets/EURUSD_1h-0_1000.csv")
        self.raw_data = pd.read_csv(
            "test/assets/EURUSD_1h-0_1000.csv",
            index_col=0,
            parse_dates=["datetime"],
        )
        self.raw_data.reset_index(inplace=True)

    def test_value(self):
        pdtest.assert_frame_equal(
            self.data,
            self.raw_data,
            "DataFrame is not equal pandas.DataFrame",
            check_index_type=False,
        )

    def test_next(self):
        df = self.data.copy(deep=True)
        df._set_main()

        for i in range(0, len(df)):
            row = df[0]
            raw_row = self.raw_data.iloc[i]

            pdtest.assert_series_equal(
                row,
                raw_row,
                f"DataFeed[{i}] is not equal",
                check_names=False,
            )

            df.next()

    def test_iloc(self):
        df = self.data.copy(deep=True)
        df._set_main()

        for i in range(0, len(df)):
            row = df.iloc[i]
            raw_row = self.raw_data.iloc[i]

            pdtest.assert_series_equal(
                row,
                raw_row,
                f"DataFeed[{i}] is not equal",
                check_names=False,
            )
            df.next()

    def test_loc(self):
        df = self.data.copy(deep=True)
        df._set_main()

        for i in range(0, len(df)):
            row = df.loc[0]
            raw_row = self.raw_data.iloc[i]

            pdtest.assert_series_equal(
                row,
                raw_row,
                f"DataFeed[{i}] is not equal",
                check_names=False,
            )
            df.next()


if __name__ == "__main__":
    unittest.main(verbosity=2)
