from technical.indicators import ema

from lettrade import DataFeed, Strategy
from lettrade import indicator as i
from lettrade.exchange.backtest import ForexBackTestAccount, let_backtest


class SmaCross(Strategy):
    ema1_period = 9
    ema2_period = 21

    def indicators(self, df: DataFeed):
        df["ema1"] = ema(df, period=self.ema1_period)
        df["ema2"] = ema(df, period=self.ema2_period)

        df["signal_ema_crossover"] = i.crossover(df.ema1, df.ema2)
        df["signal_ema_crossunder"] = i.crossunder(df.ema1, df.ema2)

    def next(self, df: DataFeed):
        if len(self.orders) > 0 or len(self.positions) > 0:
            return

        if df.l.signal_ema_crossover[-1]:
            price = self.data.l.close[-1]
            self.buy(size=0.1, sl=price - 0.01, tp=price + 0.01)
        elif df.l.signal_ema_crossunder[-1]:
            price = self.data.l.close[-1]
            self.sell(size=0.1, sl=price + 0.01, tp=price - 0.01)

    def plot(self, df: DataFeed):
        from lettrade.plot.plotly import PlotColor, plot_line, plot_merge

        plot_ema1 = plot_line(df["ema1"], color=PlotColor.AMBER)
        plot_ema2 = plot_line(df["ema2"], color=PlotColor.CYAN)
        return plot_merge(plot_ema1, plot_ema2)


lt = let_backtest(
    strategy=SmaCross,
    datas="example/data/data/EURUSD_5m-0_1000.csv",
    account=ForexBackTestAccount,
)

lt.run()
lt.plot()
