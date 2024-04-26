from typing import Mapping

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ..data import DataFeed


class Plotter:
    figure: go.Figure = None

    _stored_datas: dict = {}

    def __init__(self, datas: list[DataFeed]) -> None:
        self.datas: list[DataFeed] = datas
        self.data: DataFeed = datas[0]

    def load(self):
        df = self.data

        self.figure = go.Figure(
            data=[
                go.Candlestick(
                    x=df.index,
                    open=df["open"],
                    high=df["high"],
                    low=df["low"],
                    close=df["close"],
                    customdata=df["datetime"],
                    text="At: %{customdata}",
                    hoverinfo="text",
                ),
                go.Scatter(
                    x=df.index,
                    meta=df["datetime"],
                    y=df["ema1"],
                    line=dict(color="blue", width=1),
                    name="ema1",
                ),
                go.Scatter(
                    x=df.index,
                    meta=df["datetime"],
                    y=df["ema2"],
                    line=dict(color="green", width=1),
                    name="ema2",
                ),
            ]
        )

    def jump(self, index, range=300, data=None):
        if data is None:
            data = self.data

        name = data.p["name"]

        stored_data: DataFeed = self._stored_datas.setdefault(name, data)
        self.data = DataFeed(name=name, data=stored_data[index : index + range].copy())

        self.load()

    def plot(self):
        if self.figure is None:
            self.load()

        # self.figure.add_scatter(
        #     x=df.index,
        #     y=df["pointpos"],
        #     mode="markers",
        #     marker=dict(size=5, color="MediumPurple"),
        #     name="Signal",
        # )
        self.figure.update_layout()
        self.figure.show()
