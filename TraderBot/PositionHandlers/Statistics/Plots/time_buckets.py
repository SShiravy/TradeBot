from TraderBot.PositionHandlers.Statistics.Plots.base import ResultPlotter
from TraderBot.PositionHandlers.Statistics.Plots import theme
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator
from typing import TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from TraderBot.PositionHandlers.Statistics.Analyses.time_buckets import (
        TimeBucketResult,
    )


class TimeBucketPlotter(ResultPlotter["TimeBucketResult"]):
    def draw(self, result: "TimeBucketResult", title: str) -> dict[str, Figure]:
        if not result.active:
            return {}

        figure, (ax_pnl, ax_trades) = theme.new_figure(
            title, nrows=2, figsize=(13, 8), height_ratios=(2.2, 1), sharex=True
        )
        names = list(result.buckets)
        reports = list(result.buckets.values())
        x = np.arange(len(names))
        width = 0.62

        pnl = np.array([r.pnl_dollar if r else 0.0 for r in reports])
        bars = ax_pnl.bar(
            x, pnl, **theme.bar_style(color=theme.polarity_colors(pnl), width=width)
        )
        ax_pnl.bar_label(
            bars,
            labels=[theme.compact(v) if r else "" for v, r in zip(pnl, reports)],
            padding=3,
            fontsize=8.5,
            color=theme.INK_SECONDARY,
        )
        theme.baseline(ax_pnl)
        theme.number_axis(ax_pnl)
        ax_pnl.margins(y=0.14)
        theme.panel_title(
            ax_pnl, "Net PnL ($)", f"{result.total_trades} trades, by entry time"
        )

        wins = np.array([r.wins if r else 0 for r in reports])
        losses = np.array([r.loses if r else 0 for r in reports])
        flats = np.array([r.flats if r else 0 for r in reports])
        stack = [
            (wins, theme.GAIN, "Wins"),
            (losses, theme.LOSS, "Losses"),
            (flats, theme.NEUTRAL, "Flats"),
        ]
        bottom = np.zeros(len(names))
        top = None
        for counts, color, name in stack:
            if not counts.any():
                continue
            top = ax_trades.bar(
                x,
                counts,
                bottom=bottom,
                **theme.bar_style(color=color, width=width, label=name),
            )
            bottom = bottom + counts

        if top is not None:
            ax_trades.bar_label(
                top,
                labels=[f"{result.win_rate(r):.0f}%" if r else "" for r in reports],
                padding=3,
                fontsize=8.5,
                color=theme.INK_SECONDARY,
            )
        ax_trades.yaxis.set_major_locator(MaxNLocator(nbins=5, integer=True))
        ax_trades.margins(y=0.25)
        ax_trades.legend(loc="lower right", bbox_to_anchor=(1, 1), ncols=3)
        theme.panel_title(ax_trades, "Trades  (label: win rate)")
        ax_trades.set_xticks(x, names)
        ax_trades.set_xlabel(result.bucket_label)
        return {"pnl": figure}
