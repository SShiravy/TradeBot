from BacktestModule.dummy_agent import DummyAgent
from FiboChochStrategy.fibochoch import FiboChochSignal
from TradingModule import Position, OrderSide, commands
from TradingModule.models import PositionsReport
from ChartModule.models import Signal, ChartData
from ChartModule.plot import PlotChart
from FiboChochStrategy import FiboChochConfig
from DivergenceStrategy import DivergenceTradeConfig, DivergenceSignal
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from copy import copy
import logging


logger = logging.getLogger("FiChDiverStrategy")


@dataclass(kw_only=True)
class FiboChochDiver(FiboChochConfig):
    divergence_config: DivergenceTradeConfig

    n_fich_signal_per_diver: int = field(default=1)

    n_bar_support_range: int = field(default=50)

    modify_positions_sl: bool = field(default=True)

    diver_last_signal: DivergenceSignal | None = field(default=None, init=False)
    diver_next_check: datetime | None = field(default=None, init=False)

    _n_fich_diver_signal: int = field(default=1, init=False)

    def give_diver_n_bar(self, fich_n_bar: int | None):
        if fich_n_bar is None:
            fich_n_bar = self.n_candle_check

        minutes = self.chart.timeframe.minutes * fich_n_bar
        n_bar = round(minutes / self.divergence_config.chart.timeframe.minutes) + 1
        if n_bar > self.divergence_config.strategy.max_step:
            return n_bar + self.divergence_config.n_candle_check
        else:
            return self.divergence_config.strategy.max_step

    def check_support_range(self, signal: FiboChochSignal) -> bool:
        if self.diver_last_signal is None:
            return False
        t_diff = signal.candle.time - self.diver_last_signal.candle.time
        n_bar = round(t_diff.total_seconds() / (self.chart.timeframe.minutes * 60))

        logger.critical(f"{n_bar}|{t_diff}|{self.n_bar_support_range}")
        if n_bar > self.n_bar_support_range:
            self.diver_last_signal = None
            return False
        return True

    async def initialize_diver(self):
        self._n_fich_diver_signal = self.n_fich_signal_per_diver
        self.divergence_config.send_signal = False
        self.divergence_config.max_long_lose = 100
        self.divergence_config.max_short_lose = 100
        self.divergence_config.bar_between_signals = 1
        self.send_position_command = False

        res = await self.divergence_config.backtest(
            self.divergence_config.n_candle_check,
            show_image=False,
            consider_positions=False,
        )
        base_chartdata, _ = self.divergence_config.get_chartdata(5)
        delay = self.divergence_config.give_delay(base_chartdata[-1])
        self.diver_next_check = datetime.now() + delay

        if not res[0]:
            # there is no signal
            logger.warning(f"no diver signal: {res}")
            return
        self.diver_last_signal = res[0][-1]  # type: ignore
        logger.info(f"current diver signal: {self.diver_last_signal}")
        return res

    def find_signal(
        self, chartdata: ChartData
    ) -> None | tuple[FiboChochSignal, Position]:
        if self.diver_last_signal is None:
            return None

        signal = self.strategy.check_signal(
            chartdata, self.long_signal, self.short_signal
        )
        if signal is None or signal.fibochoch_model.fibo is None:
            return None
        if self.diver_last_signal.side != signal.side:
            return None
        if self._n_fich_diver_signal < 1:
            return None
        if not self.check_support_range(signal):
            return None
        if signal.candle.time < self.diver_last_signal.candle.time:
            return None

        position = self.position_handler.generate_position(
            signal, sl_base_price=signal.fibochoch_model.fibo.start_tick.price
        )
        if self.modify_positions_sl:
            position.stoploss = self.position_handler.init_stoploss(
                signal.fibochoch_model.fibo.start_tick.price, position.side
            )

        if (self.position_handler.long_trade and position.side is OrderSide.BUY) or (
            self.position_handler.short_trade and position.side is OrderSide.SELL
        ):
            commands.OpenPosition(position, self.agent)

        self._n_fich_diver_signal -= 1
        return signal, position

    async def task(self) -> timedelta | tuple[timedelta, Signal, Position]:
        if self.diver_next_check is None:
            await self.initialize_diver()

        if self.diver_next_check and datetime.now() > self.diver_next_check:
            res = await self.divergence_config.task()
            if isinstance(res, timedelta):
                delay = res
            else:
                delay = res[0]
                self.diver_last_signal = res[1]
                self._n_fich_diver_signal = self.n_candle_check
            self.diver_next_check = datetime.now() + delay

        return await super().task()

    async def backtest(  # type: ignore
        self, n_bar=500, len_sub_data=100, show_image=True, consider_positions=True
    ):
        self.divergence_config.n_candle_check = self.give_diver_n_bar(n_bar)
        res = await self.initialize_diver()
        if res is None:
            raise ValueError(f"Diver {res=}")

        diver_signals = res[0]

        self.diver_last_signal = diver_signals[0]  # type: ignore

        self.diver_next_check = datetime.now() + timedelta(days=1)
        self.send_signal = False

        position_handler = copy(self.position_handler)

        chartdata = self.get_chartdata(n_bar)
        if chartdata is None:
            raise ValueError(f"{chartdata=}")

        agent = DummyAgent(
            self.agent, position_handler.open_positions, chartdata, len_sub_data
        )
        position_handler.exchange_agent = agent
        self.agent = agent
        position_handler.long_trade = False
        position_handler.short_trade = False

        all_positions: list[Position] = []
        all_signals: list[FiboChochSignal] = []

        while agent.index < len(agent.chartdata.candles) - 1:  # type: ignore
            while (
                len(diver_signals) > 1
                and self.get_chartdata()[-1].time >= diver_signals[1].candle.time
            ):
                diver_signals.pop(0)
                self.diver_last_signal = diver_signals[0]  # type: ignore
                self._n_fich_diver_signal = self.n_fich_signal_per_diver
                logger.info(f"New Diver Signal: {self.diver_last_signal}")

            res = await self.task()
            if isinstance(res, timedelta):
                candle_delay = 1
            else:
                all_signals.append(res[1])  # type: ignore
                if consider_positions:
                    all_positions.append(res[2])
                candle_delay = self.bar_between_signals + 1
            if consider_positions:
                position_handler.manage_positions()
                await commands.TradeCommand.execute_pending_commands(
                    time=agent.get_chartdata(self.chart)[-1].time,  # type: ignore
                    report=False,
                )
            agent.index += candle_delay
            logger.debug(f"{candle_delay} Candle next")

        plot = PlotChart(agent.chartdata)  # type: ignore
        for signal in all_signals:
            self.strategy.draw(plot, signal)

        for pos in all_positions:
            pos.draw(plot)

        commands_report = commands.TradeCommand.close_records()
        all_reports = position_handler.report()
        logger.info("Result:\n\n" + commands_report)
        for poses_report in all_reports:
            logger.info("\n" + str(poses_report))
        overal_report = PositionsReport.give_overall_report(copy(all_reports))
        logger.info("\n" + str(overal_report))
        logger.info(
            f"total time: {agent.chartdata[-1].time - agent.chartdata[0].time} with {len(agent.chartdata)} candles"  # type: ignore
        )
        if show_image:
            plot.show()

        return all_signals, all_positions, plot, all_reports, commands_report
