from ChartModule.models import Chart
from Settings.timing import TimeHandler
from TraderBot.events import TakeProfitHit
from TraderBot.models import PnLReport, Position, PositionSide


class PnLCalculator:
    @staticmethod
    def dollar(
        chart: Chart,
        side: PositionSide,
        entry_price: float,
        executed_price: float,
        volume: float,
    ) -> float:
        return (
            (executed_price - entry_price) * side.factor * volume * chart.contract_size
        )

    @staticmethod
    def percent(
        entry_price: float, executed_price: float, side: PositionSide, leverage: int = 1
    ) -> float:
        return (
            (executed_price - entry_price) * side.factor / entry_price * 100 * leverage
        )

    @staticmethod
    def pips(
        chart: Chart, side: PositionSide, entry_price: float, executed_price: float
    ) -> float:
        return (executed_price - entry_price) * side.factor / chart.pip_factor


class PnLReportGenerator:
    @staticmethod
    def from_pnl(position: Position, pnl_dollar: float, volume: float) -> PnLReport:
        last_time = position.closed_timestamp or position.last_check_timestamp
        report = PnLReport(
            chart=position.chart,
            side=position.side,
            source=position.source,
            first_time=position.defined_timestamp,
            last_time=last_time,
        )
        report.pnl_dollar = pnl_dollar
        report.volume = volume
        # report.pnl_percent =
        # report.pnl_pips =
        return report

    @staticmethod
    def from_position(position: Position) -> PnLReport:
        last_time = position.closed_timestamp or position.last_check_timestamp

        report = PnLReport(
            chart=position.chart,
            side=position.side,
            source=position.source,
            first_time=position.defined_timestamp,
            last_time=last_time,
        )

        # weighted accumulators for percent/pips (weighted by volume closed at each event)
        weighted_percent = 0.0
        weighted_pips = 0.0
        closed_volume = 0.0

        # all triggered TP
        for i, step in enumerate(position.steps):
            if (
                not isinstance(step.event, TakeProfitHit)
                or step.triggered_timestamp is None
            ):
                continue

            event_pnl = PnLCalculator.dollar(
                position.chart,
                position.side,
                position.entry_price,
                step.price,
                step.volume,
            )
            event_percent = PnLCalculator.percent(
                position.entry_price, step.price, position.side, position.leverage
            )
            event_pips = PnLCalculator.pips(
                position.chart, position.side, position.entry_price, step.price
            )

            report.pnl_dollar += event_pnl
            weighted_percent += event_percent * step.volume
            weighted_pips += event_pips * step.volume
            closed_volume += step.volume

            report.triggered_steps[i] = report.triggered_steps.get(i, 0) + 1

        # stoploss, closing whatever volume remains after all TP closes
        remaining_volume = position.volume - closed_volume
        if position.stoploss.triggered_timestamp is not None and remaining_volume > 0:
            sl_price = position.stoploss.price
            event_pnl = PnLCalculator.dollar(
                position.chart,
                position.side,
                position.entry_price,
                sl_price,
                remaining_volume,
            )
            event_percent = PnLCalculator.percent(
                position.entry_price, sl_price, position.side, position.leverage
            )
            event_pips = PnLCalculator.pips(
                position.chart, position.side, position.entry_price, sl_price
            )

            report.pnl_dollar += event_pnl
            weighted_percent += event_percent * remaining_volume
            weighted_pips += event_pips * remaining_volume
            closed_volume += remaining_volume

        report.volume = closed_volume

        # volume-weighted average across every close event (TP hits + SL, if any)
        if closed_volume > 0:
            report.pnl_percent = weighted_percent / closed_volume
            report.pnl_pips = weighted_pips / closed_volume

        if report.pnl_dollar > 0:
            report.wins += 1
        elif report.pnl_dollar < 0:
            report.loses += 1
        else:
            report.flats += 1

        return report

    @staticmethod
    def identifier_reports(all_positions: list[Position]) -> list[PnLReport]:
        """Return one merged report per unique (chart, side, source) identifier."""
        reports_dict: dict[str, PnLReport] = {}
        for pos in all_positions:
            report = PnLReportGenerator.from_position(pos)
            if report.identifier not in reports_dict:
                reports_dict[report.identifier] = report
            else:
                reports_dict[report.identifier] += report
        return list(reports_dict.values())

    @staticmethod
    def overall_report(all_positions: list[Position]) -> PnLReport:
        ordered_positions = sorted(
            all_positions,
            key=lambda pos: pos.closed_timestamp or TimeHandler.now(),
        )
        win_in_a_row = 0
        lose_in_a_row = 0
        overall_report = PnLReportGenerator.from_position(ordered_positions[0])
        for pos in ordered_positions[1:]:
            report = PnLReportGenerator.from_position(pos)
            if report.pnl_dollar > 0:
                win_in_a_row += 1
                lose_in_a_row = 0
            elif report.pnl_dollar < 0:
                lose_in_a_row += 1
                win_in_a_row = 0

            overall_report += report
            overall_report.max_win_in_a_row = max(
                overall_report.max_win_in_a_row, win_in_a_row
            )
            overall_report.max_lose_in_a_row = max(
                overall_report.max_lose_in_a_row, lose_in_a_row
            )

        return overall_report
