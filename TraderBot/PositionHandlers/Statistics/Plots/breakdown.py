from TraderBot.PositionHandlers.Statistics.Plots.base import ResultPlotter
from TraderBot.PositionHandlers.Statistics.Plots import theme
from matplotlib.figure import Figure
from typing import TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from TraderBot.PositionHandlers.Statistics.Analyses.breakdown import (
        BreakdownResult,
    )


class BreakdownPlotter(ResultPlotter["BreakdownResult"]):
    def draw(self, result: "BreakdownResult", title: str) -> dict[str, Figure]:
        # a single identifier is one number: the text report says it better
        if len(result.reports) < 2:
            return {}

        reports = result.reports
        figure, (ax,) = theme.new_figure(title, figsize=(13, 1.6 + 0.5 * len(reports)))
        y = np.arange(len(reports))
        pnl = np.array([r.pnl_dollar for r in reports])
        bars = ax.barh(
            y, pnl, **theme.bar_style(color=theme.polarity_colors(pnl), height=0.6)
        )
        ax.bar_label(
            bars,
            labels=[
                f"{theme.compact(r.pnl_dollar)}   "
                f"{r.total_positions} trades, {result.win_rate(r):.0f}% win"
                for r in reports
            ],
            padding=6,
            fontsize=9,
            color=theme.INK_SECONDARY,
        )
        ax.set_yticks(y, [result.label(r) for r in reports])
        ax.invert_yaxis()
        ax.grid(axis="y", visible=False)
        ax.grid(axis="x", visible=True)
        ax.spines["bottom"].set_visible(False)
        ax.tick_params(axis="y", labelsize=9.5)
        theme.baseline(ax, vertical=True)
        theme.number_axis(ax, axis="x")
        ax.margins(x=0.3)
        theme.panel_title(ax, "Net PnL ($)", "by source | side | chart")
        return {"pnl": figure}
