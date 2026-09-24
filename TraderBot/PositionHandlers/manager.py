from Settings import TimeHandler
from ChartModule import Signal, MarketSide, Chart, TimeFrame
from TraderBot import Position, PositionSide, ExchangeAgent
from TraderBot.Commands.report_commands import ReportCommandContext
from TraderBot.Commands.trade_commands import TradeCommandContext
from TraderBot.PositionHandlers.trading_constraints import TradingConstraint
from TraderBot.models import PnLReport, PositionType, ReporterBot, Trigger
from abc import ABC, abstractmethod
import numpy as np
import logging


logger = logging.getLogger("PositionManager")


class PositionGenerator(ABC):
    def __init__(
        self,
        initial_volume: float = 0.0,
        leverage: int = 1,
    ) -> None:
        self.initial_volume = initial_volume
        self.leverage = leverage

    @abstractmethod
    def init_stoploss(
        self, entry_price: float, side: PositionSide, chart: Chart, *args, **kwargs
    ) -> Trigger:
        pass

    @abstractmethod
    def generate_triggers(
        self, entry_price: float, side: PositionSide, chart: Chart, *args, **kwargs
    ) -> list[Trigger]:
        pass

    @abstractmethod
    def export_config(self) -> dict:
        return {
            "initial_volume": self.initial_volume,
            "leverage": self.leverage,
        }

    def generate(
        self,
        signal: Signal,
        last_price: float,
        *args,
        **kwargs,
    ) -> Position | None:
        side = PositionSide.convert_market_side(signal.side)

        position = Position(
            signal.chart,
            side,
            last_price,
            self.initial_volume,
            self.generate_triggers(last_price, side, signal.chart),
            self.init_stoploss(last_price, side, signal.chart),
            self.leverage,
            type=PositionType.MARKET,
            source=signal.source,
        )

        logger.info(f"New Position on {position.chart}")
        return position


class TradesManager:
    def __init__(
        self,
        exchange_agent: ExchangeAgent,
        generator: PositionGenerator,
        reporter: ReporterBot,
        long_trade: bool = True,
        short_trade: bool = True,
        trading_constraints: list[TradingConstraint] = [],
        agent_check: bool = False,
    ):
        self.exchange_agent = exchange_agent
        self.long_trade: bool = long_trade
        self.short_trade: bool = short_trade
        self.trading_constraints = trading_constraints
        self.reporter = reporter
        self.generator = generator
        self.agent_check = agent_check
        self.current_positions: list[Position] = []
        self.closed_positions: list[Position] = []

    def export_config(self) -> dict:
        return {
            "generator": self.generator.export_config(),
            "long_trade": self.long_trade,
            "short_trade": self.short_trade,
            "constraints": [c.export_config() for c in self.trading_constraints],
        }

    def generate_position(self, signal: Signal, *args, **kwargs) -> Position | None:
        if signal.side is MarketSide.BEARISH:
            if not self.short_trade:
                return None
        else:  # signal.side is MarketSide.BULLISH:
            if not self.long_trade:
                return None
        entry_price = self.exchange_agent.get_current_tick(signal.chart)
        pos = self.generator.generate(signal, entry_price, *args, **kwargs)
        if pos:
            for constraint in self.trading_constraints:
                if not constraint.check(
                    signal, pos, self.current_positions, self.closed_positions
                ):
                    return None
            self.current_positions.append(pos)
            logger.debug(f"New Position {pos}")
        return pos

    def modify_init_sl_tp(self, position: Position):
        # TODO: implement here
        # sl = self.init_stoploss(position.entry_price, position.side)
        # if sl != position.stoploss:
        #     trade_commands.TrailStoploss(position, self.exchange_agent, sl, report=False)
        #     trade_commands.cha
        # tp = self.init_takeprofit(position.entry_price, position.side)
        # if tp != position.takeprofit:
        #     position.takeprofit = tp
        #     commands.ChangeTakeProfit(position, self.exchange_agent, tp, report=False)
        # position.confiremed = True
        # logger.info(f"Position Updated on {position.chart}")
        pass

    def triggers_handler(self, position: Position, ticks: np.ndarray):
        if not position.open_timestamp:
            logger.debug(f"Position is not open yet.")
            return
        if position.stoploss.triggered_timestamp:
            logger.debug(f"stoploss of {position} hit, waiting for its command")
            return
        if position.stoploss.check(ticks):
            logger.debug(f"SL hit for {position}")
            position.stoploss.event.occur(
                trade_context=TradeCommandContext(position, self.exchange_agent),
                report_context=ReportCommandContext(
                    self.reporter, reply_id=position.report_id
                )
                if self.reporter
                else None,
            )
            return
        for trigger in position.steps:
            if trigger.triggered_timestamp:
                continue
            if trigger.check(ticks):
                logger.debug(f"Trigger Hit: {trigger=}|{position=}")
                trigger.event.occur(
                    trade_context=TradeCommandContext(position, self.exchange_agent),
                    report_context=ReportCommandContext(
                        self.reporter, reply_id=position.report_id
                    )
                    if self.reporter
                    else None,
                )
                continue
            return

    def agent_handler(self, position: Position):
        if not position.open_timestamp:
            logger.debug(f"Position is not open yet.")
            return

        pnl_report = self.exchange_agent.check_position_closed(position)
        if not pnl_report:
            return None
        if pnl_report.pnl_dollar <= 0:
            sl_report: PnLReport | None = getattr(
                position.stoploss.event, "pnl_report", None
            )
            if sl_report is None or round(sl_report.volume, 8) < round(
                position.stoploss.volume, 8
            ):
                logger.debug(f"{position} stoploss partially closed: {sl_report}")
                return None
            position.stoploss.event.occur(
                trade_context=TradeCommandContext(position, self.exchange_agent),
                report_context=ReportCommandContext(
                    self.reporter, reply_id=position.report_id
                )
                if self.reporter
                else None,
            )
        else:
            for trigger in position.steps:
                if (
                    trigger.triggered_timestamp is None
                    or trigger.event.occur_timestamps
                ):
                    continue
                logger.debug(f"Trigger Hit: {trigger=}|{position=}")
                trigger.event.occur(
                    trade_context=TradeCommandContext(position, self.exchange_agent),
                    report_context=ReportCommandContext(
                        self.reporter, reply_id=position.report_id
                    )
                    if self.reporter
                    else None,
                )

    def ochl_handler(self, position: Position):
        ticks = []

        chart_1m = Chart(position.chart.symbol, TimeFrame.one_minute)
        chartdata = self.exchange_agent.get_chartdata(chart_1m, 3)
        if not chartdata:
            logger.warning(f"getting candles failed for {position}")
            return
        for candle in chartdata:
            if candle.timestamp < position.last_check_timestamp:
                continue
            ticks += [candle.open, candle.low, candle.high, candle.close]
        position.last_check_timestamp = chartdata[-1].timestamp
        return self.triggers_handler(position, np.array(ticks))

    def manage_positions(self):
        all_pos = self.current_positions.copy()
        for pos in all_pos:
            if self.agent_check:
                self.agent_handler(pos)
            else:
                self.ochl_handler(pos)
            if pos.closed_timestamp:
                self.closed_positions.append(pos)
                self.current_positions.remove(pos)
