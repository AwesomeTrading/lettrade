import logging

import numpy as np
import pandas as pd

from lettrade.account import Account
from lettrade.data import DataFeeder
from lettrade.exchange import Exchange
from lettrade.strategy import Strategy

logger = logging.getLogger(__name__)


class BotStatistic:
    """
    Compute strategy result
    """

    result: pd.Series

    def __init__(
        self,
        feeder: DataFeeder,
        exchange: Exchange,
        strategy: Strategy,
    ) -> None:
        self.feeder: DataFeeder = feeder
        self.exchange: Exchange = exchange
        self.strategy: Strategy = strategy
        self.account: Account = strategy.account

    def stop(self):
        pass

    def compute(self):
        """
        Calculate strategy report
        """
        data = self.feeder.data

        equities = list(self.account._equities.values())
        trades = list(self.exchange.history_trades.values()) + list(
            self.exchange.trades.values()
        )
        trades_columns = (
            "size",
            "entry_at",
            "exit_at",
            "entry_price",
            "exit_price",
            "pl",
            "fee",
        )
        trades_df = pd.DataFrame(columns=trades_columns)
        for trade in trades:
            trades_df.at[trade.id, trades_columns] = (
                trade.size,
                trade.entry_at,
                trade.exit_at,
                trade.entry_price,
                trade.exit_price,
                trade.pl,
                trade.fee,
            )
        trades_df["duration"] = trades_df["entry_at"] - trades_df["exit_at"]

        self.result = result = pd.Series(dtype=object)

        result.loc["strategy"] = str(self.strategy.__class__)
        result.loc["start"] = data.index[0]
        result.loc["end"] = data.index[-1]
        result.loc["duration"] = result.end - result.start

        # Equity
        result.loc["start_balance"] = round(equities[0], 2)
        result.loc["equity"] = round(equities[-1], 2)

        pl = equities[-1] - equities[0]
        result.loc["pl"] = round(pl, 2)
        result.loc["pl_percent"] = round(pl / equities[0] * 100, 2)

        # TODO
        # result.loc["buy_hold_pl_percent"] = 2.0
        # result.loc["max_drawdown_percent"] = -33.08
        # result.loc["avg_drawdown_percent"] = -5.58
        # result.loc["max_drawdown_duration"] = "688 days 00:00:00"
        # result.loc["avg_drawdown_duration"] = "41 days 00:00:00"

        # Separator
        result.loc[""] = ""

        # Trades
        trades_total = len(trades)
        pl = trades_df["pl"]

        result.loc["trades"] = trades_total

        win_rate = np.nan if not trades_total else (pl > 0).mean()
        result.loc["win_rate"] = round(win_rate, 2)
        result.loc["fee"] = trades_df.fee.sum()
        result.loc["best_trade_percent"] = pl.max()
        result.loc["worst_trade_percent"] = pl.min()
        result.loc["sqn"] = round(
            np.sqrt(trades_total) * pl.mean() / (pl.std() or np.nan),
            2,
        )
        result.loc["kelly_criterion"] = win_rate - (1 - win_rate) / (
            pl[pl > 0].mean() / -pl[pl < 0].mean()
        )
        # TODO
        result.loc["profit_factor"] = pl[pl > 0].sum() / (
            abs(pl[pl < 0].sum()) or np.nan
        )

        return self.result

    def __repr__(self) -> str:
        result = self.result.rename(
            {
                "strategy": "# Strategy",
                "start": "Start",
                "end": "End",
                "duration": "Duration",
                "start_balance": "Start Balance",
                "equity": "Equity [$]",
                "pl": "PL [$]",
                "pl_percent": "PL [%]",
                # "buy_hold_pl_percent": "Buy & Hold PL [%]",
                # "max_drawdown_percent": "Max. Drawdown [%]",
                # "avg_drawdown_percent": "Avg. Drawdown [%]",
                # "max_drawdown_duration": "Max. Drawdown Duration",
                # "avg_drawdown_duration": "Avg. Drawdown Duration",
                "trades": "# Trades",
                "win_rate": "Win Rate [%]",
                "fee": "Fee [$]",
                "best_trade_percent": "Best Trade [%]",
                "worst_trade_percent": "Worst Trade [%]",
                "profit_factor": "Profit Factor",
                "kelly_criterion": "Kelly Criterion",
                "sqn": "SQN",
            }
        )
        return str(result.to_string())

    def show(self):
        """
        Show statistic report
        """
        if "Start" not in self.result:
            logger.warning("call compute() before show()")
            self.compute()

        # Show result inside docs session
        if __debug__:
            from lettrade.utils.docs import is_docs_session

            if is_docs_session():
                print(str(self))
                return

        logger.info(
            "\n============= Statistic result =============\n%s\n",
            str(self),
        )
