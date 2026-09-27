from TraderBot.PositionHandlers.Statistics.Plots.base import ResultPlotter
from TraderBot.PositionHandlers.Statistics.Plots import theme
from TraderBot.PositionHandlers.Statistics.text import moment
from matplotlib.figure import Figure
from typing import TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from TraderBot.PositionHandlers.Statistics.Analyses.performance import (
        PerformanceResult,
    )


class PerformancePlotter(ResultPlotter["PerformanceResult"]):
    def draw(self, result: "PerformanceResult", title: str) -> dict[str, Figure]:
        if not result.n_trades:
            return {}
        return {
            "equity": self._equity(result, title),
            "running": self._running(result, title),
            "streaks": self._streaks(result, title),
        }

    def _equity(self, result: "PerformanceResult", title: str) -> Figure:
        figure, (ax_equity, ax_dd) = theme.new_figure(
            title, nrows=2, figsize=(13, 8), height_ratios=(3, 1.3), sharex=True
        )
        x = np.arange(result.n_trades + 1)
        equity, drawdown = result.equity, result.drawdown

        ax_equity.fill_between(
            x,
            equity,
            0,
            where=equity >= 0,
            interpolate=True,
            color=theme.GAIN,
            alpha=theme.WASH,
            linewidth=0,
        )
        ax_equity.fill_between(
            x,
            equity,
            0,
            where=equity < 0,
            interpolate=True,
            color=theme.LOSS,
            alpha=theme.WASH,
            linewidth=0,
        )
        ax_equity.plot(
            x,
            result.high_watermark,
            color=theme.INK_MUTED,
            linewidth=1.2,
            label="High watermark",
        )
        ax_equity.plot(x, equity, color=theme.GAIN, label="Equity")
        theme.baseline(ax_equity)
        theme.end_label(ax_equity, x[-1], equity[-1], f"{equity[-1]:,.2f}", theme.GAIN)
        theme.number_axis(ax_equity)
        ax_equity.legend(loc="lower center", bbox_to_anchor=(0.5, 1), ncols=2)
        period = f"{moment(int(result.close_times[0]))}  to  {moment(int(result.close_times[-1]))}"
        theme.panel_title(ax_equity, "Equity ($)", period)

        ax_dd.fill_between(x, drawdown, 0, color=theme.LOSS, alpha=0.16, linewidth=0)
        ax_dd.plot(x, drawdown, color=theme.LOSS, linewidth=1.5)
        theme.baseline(ax_dd)
        if result.max_drawdown < 0:
            i = result.max_drawdown_trade
            theme.marker(
                ax_dd,
                i,
                drawdown[i],
                theme.LOSS,
                f"Max {result.max_drawdown:,.2f}",
                above=False,
            )
            ax_dd.set_ylim(result.max_drawdown * 1.35, -result.max_drawdown * 0.08)
        theme.number_axis(ax_dd)
        theme.panel_title(ax_dd, "Drawdown ($)")
        theme.trade_number_axis(ax_dd, result.n_trades)
        return figure

    def _running(self, result: "PerformanceResult", title: str) -> Figure:
        figure, axes = theme.new_figure(title, nrows=4, figsize=(13, 11), sharex=True)
        n = result.n_trades
        cumulative = np.arange(n + 1)
        running = np.arange(1, n + 1)

        # (x, y, panel title, end-label format)
        panels = (
            (cumulative, result.equity_percent, "Cumulative PnL (%)", "{:,.2f}%"),
            (cumulative, result.win_loss_score, "Win / loss score", "{:+,.0f}"),
            (running, result.running_win_rate, "Running win rate (%)", "{:.1f}%"),
            (running, result.running_average, "Running average trade ($)", "{:,.2f}"),
        )
        for ax, (x, y, name, fmt) in zip(axes, panels):
            ax.plot(x, y, color=theme.GAIN)
            theme.end_label(ax, x[-1], y[-1], fmt.format(y[-1]), theme.GAIN)
            theme.panel_title(ax, name)

        for ax in (axes[0], axes[1], axes[3]):
            theme.baseline(ax)
        theme.baseline(axes[2], 50)
        axes[2].set_ylim(0, 100)
        axes[1].set_title("+1 per win, -1 per loss", loc="right", **theme.NOTE)
        theme.trade_number_axis(axes[3], n)
        return figure

    def _streaks(self, result: "PerformanceResult", title: str) -> Figure:
        figure, axes = theme.new_figure(title, ncols=2, figsize=(13, 5.5))
        panels = (
            (axes[0], result.win_streaks, theme.GAIN, "Winning streaks"),
            (axes[1], result.loss_streaks, theme.LOSS, "Losing streaks"),
        )
        for ax, distribution, color, name in panels:
            theme.panel_title(ax, name, "occurrences per streak length")
            if not distribution:
                theme.empty_panel(ax, f"No {name.lower()}")
                continue
            lengths, counts = list(distribution), list(distribution.values())
            bars = ax.bar(lengths, counts, **theme.bar_style(color=color, width=0.6))
            ax.bar_label(bars, padding=3, fontsize=9, color=theme.INK_SECONDARY)
            ax.set_xticks(lengths)
            ax.set_xlabel("Consecutive trades")
            ax.margins(y=0.12)
        return figure
