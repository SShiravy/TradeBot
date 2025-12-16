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

    diver_last_signal: DivergenceSignal | None = field(default=None, init=False)
    diver_next_check: datetime | None = field(default=None, init=False)

    async def initialize_diver(self):
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

        position = self.position_handler.generate_position(signal)
        if self.fibo_stoploss:
            sl = self.position_handler.init_stoploss(
                signal.fibochoch_model.fibo.start_tick.price, position.side
            )
            position.stoploss = sl

        if (self.position_handler.long_trade and position.side is OrderSide.BUY) or (
            self.position_handler.short_trade and position.side is OrderSide.SELL
        ):
            commands.OpenPosition(position, self.agent)
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
            self.diver_next_check = datetime.now() + delay

        return await super().task()

    async def backtest(  # type: ignore
        self, n_bar=500, len_sub_data=100, show_image=True, consider_positions=True
    ):
        self.divergence_config.n_candle_check = int(n_bar / 2)
        res = await self.initialize_diver()
        if res is None:
            raise ValueError(f"Diver {res=}")

        diver_signals = res[0]
        diver_plot = res[2]
        diver_signal_index = 0
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
                diver_signals[-1] != self.diver_last_signal
                and self.get_chartdata()[-1].time
                >= diver_signals[diver_signal_index + 1].candle.time
            ):
                diver_signal_index += 1
                self.diver_last_signal = diver_signals[diver_signal_index]  # type: ignore
                logger.info(f"New Diver Signal: {self.diver_last_signal}")

            res = await self.task()
            if isinstance(res, timedelta):
                candle_delay = 1
            else:
                all_signals.append(res[1])  # type: ignore
                if consider_positions:
                    all_positions.append(res[2])
                candle_delay = self.bar_between_signals + 1
            agent.index += candle_delay
            if consider_positions:
                position_handler.manage_positions()
                await commands.TradeCommand.execute_pending_commands(
                    time=agent.get_chartdata(self.chart)[-1].time,  # type: ignore
                    report=False,
                )
            logger.debug(f"{candle_delay} Candle next")

        plot = PlotChart(agent.chartdata)  # type: ignore
        for signal in all_signals:
            self.strategy.draw(plot, signal)
            # diver_plot.base_plot(signal.candle,color= "#e24800")
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
            diver_plot.show()
            plot.show()

        return all_signals, all_positions, plot, all_reports, commands_report
