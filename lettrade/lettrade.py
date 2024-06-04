import logging
import os
from concurrent.futures import ProcessPoolExecutor
from typing import Optional, Type

from lettrade.account import Account
from lettrade.bot import LetTradeBot
from lettrade.commander import Commander
from lettrade.data import DataFeed, DataFeeder
from lettrade.exchange import Exchange
from lettrade.stats import Statistic
from lettrade.strategy import Strategy

logger = logging.getLogger(__name__)


class LetTrade:
    """Building new bot object and handle multiprocessing"""

    datas: list[DataFeed]
    """DataFeed list for bot"""
    data: DataFeed
    """Main DataFeed for bot"""

    _plotter: "Plotter" = None
    """Plot graphic results"""
    _stats: Statistic = None
    _bot: LetTradeBot = None

    _strategy_cls: Type[Strategy]
    _feeder_cls: Type[DataFeeder]
    _exchange_cls: Type[Exchange]
    _account_cls: Type[Account]
    _commander_cls: Type[Commander]
    _plotter_cls: Type["Plotter"]
    _stats_cls: Type["Statistic"]
    _bot_cls: LetTradeBot
    _kwargs: dict
    _name: str

    def __init__(
        self,
        strategy: Type[Strategy],
        datas: DataFeed | list[DataFeed] | str | list[str],
        feeder: Type[DataFeeder],
        exchange: Type[Exchange],
        account: Type[Account],
        commander: Optional[Type[Commander]] = None,
        plotter: Optional[Type["Plotter"]] = None,
        stats: Optional[Type["Statistic"]] = None,
        name: Optional[str] = None,
        bot: Optional[Type[LetTradeBot]] = LetTradeBot,
        **kwargs,
    ) -> None:
        self._strategy_cls = strategy
        self._feeder_cls = feeder
        self._exchange_cls = exchange
        self._account_cls = account
        self._commander_cls = commander
        self._plotter_cls = plotter
        self._stats_cls = stats
        self._bot_cls = bot
        self._name = name
        self._kwargs = kwargs

        # DataFeeds
        # TODO: remove datas from self to avoid pickle from multipleprocessing
        self.datas = self._init_datafeeds(datas)
        self.data = self.datas[0]

    def _new_bot(
        self,
        datas: Optional[list] = None,
        name: Optional[str] = None,
    ) -> LetTradeBot:
        if datas is None:
            datas = self.datas
        bot = self._bot_cls(
            strategy=self._strategy_cls,
            datas=datas,
            feeder=self._feeder_cls,
            exchange=self._exchange_cls,
            account=self._account_cls,
            commander=self._commander_cls,
            plotter=self._plotter_cls,
            stats=self._stats_cls,
            name=name,
            **self._kwargs,
        )
        return bot

    def _datafeed(self, data: DataFeed, **kwargs) -> DataFeed:
        """Init and validate DataFeed

        Args:
            data (DataFeed): DataFeed or config of it

        Raises:
            RuntimeError: Validate error

        Returns:
            DataFeed: The DataFeed
        """
        match data:
            case DataFeed():
                return data
            case _:
                raise RuntimeError(f"data {data} is invalid")

    def _init_datafeeds(self, datas) -> None:
        # Support single and multiple data
        if not isinstance(datas, list):
            datas = [datas]

        # Check data
        if isinstance(datas[0], list):
            feeds = []
            for i, data in enumerate(datas):
                data_feeds = []
                for j, d in enumerate(data):
                    d = self._datafeed(data=d, index=i * j)
                    data_feeds.append(d)
                feeds.append(data_feeds)
        else:
            feeds = [self._datafeed(data=data, index=i) for i, data in enumerate(datas)]
        return feeds

    def init(self, force=False):
        if force:
            if self._bot is not None:
                self._bot = None

        if self._bot is None:
            self._bot = self._init_bot()

    def start(self):
        if self._bot is None:
            self.init()
        self._start_bot(bot=self._bot)

    def run(self, worker: Optional[int] = None, **kwargs):
        """Run strategy in single or multiple processing

        Args:
            worker (Optional[int], optional): Number of processing. Defaults to None.
        """
        if worker or isinstance(self.data, list):
            if not isinstance(self.data, list):
                self.data = self.datas
                self.datas = [self.data]

            if not worker:
                worker = len(self.datas)
            elif worker > len(self.datas):
                logger.warning(
                    "Worker size %s is more then datas size %s",
                    worker,
                    len(self.datas),
                )
                worker = len(self.datas)

            self._multiprocess()
            with ProcessPoolExecutor(max_workers=worker) as executor:
                futures = [
                    executor.submit(
                        self._run_process,
                        datas=datas,
                        index=i,
                    )
                    for i, datas in enumerate(self.datas)
                ]
                for future in futures:
                    result = future.result()
                    print(result)
        else:
            result = self._run_process(bot=self._bot, **kwargs)
            print(result)

    def _run_process(self, bot: LetTradeBot = None, **kwargs):
        # Skip pickle bot object between processing
        if bot is None:
            bot = self._init_bot(**kwargs)
        bot = self._start_bot(bot=bot, **kwargs)
        bot = self._run_bot(bot=bot, **kwargs)
        self._bot = bot
        return str(bot.stats)

    def _init_bot(self, bot=None, datas=None, name=None):
        if bot is None:
            bot = self._new_bot(
                datas=datas,
                name=name,
                **self._kwargs.get("bot_kwargs", {}),
            )
        bot.init()
        return bot

    def _start_bot(self, bot=None, datas=None, name=None):
        if bot is None:
            bot = self._init_bot(bot=bot, datas=datas, name=name)

        bot.start()
        return bot

    def _run_bot(
        self,
        bot: LetTradeBot,
        datas: Optional[list[DataFeed]] = None,
        index: Optional[int] = None,
        name: str = None,
        **kwargs,
    ):
        if bot is None:
            bot = self._new_bot(
                datas=datas,
                name=name,
                **self._kwargs.get("bot_kwargs", {}),
            )

        # Set name for current processing
        if name is None:
            d = datas[0] if datas else self.data
            name = f"{index}-{os.getpid()}-{d.name}"

        # build bot

        bot.run(
            # multiprocess=multiprocess,
            **kwargs.pop("bot_kwargs", {}),
        )

        return bot

    def _multiprocess(self, **kwargs):
        if self._bot is not None:
            logger.warning("Remove exist bot when running in multiprocessing")
            self._bot = None

        if self._commander_cls:
            # Impletement commander dependencies and save to commander_kwargs
            commander_kwargs = self._kwargs.setdefault("commander_kwargs", {})
            self._commander_cls.multiprocess(
                kwargs=commander_kwargs,
                # self_kwargs=self._kwargs,
                **kwargs,
            )

    # def reset(self):
    #     self._bot = None
    #     self.datas = self._init_datafeeds(datas)
    #     self.data = self.datas[0]

    def stop(self):
        """Stop strategy"""
        if self._bot is not None:
            return self._bot.stop()

    @property
    def stats(self) -> Statistic:
        if self._stats:
            return self._stats
        if self._bot is not None:
            return self._bot.stats

    def plot(self, *args, **kwargs):
        """Plot strategy result"""
        if self._plotter is not None:
            return self._plotter.plot(*args, **kwargs)
        if self._bot is not None:
            return self._bot.plot(*args, **kwargs)
