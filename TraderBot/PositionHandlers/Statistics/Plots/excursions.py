from TraderBot.PositionHandlers.Statistics.Plots.base import ResultPlotter
from TraderBot.PositionHandlers.Statistics.Plots import theme
from matplotlib.figure import Figure
from typing import TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from TraderBot.PositionHandlers.Statistics.Analyses.excursions import (
        ExcursionResult,
    )


class ExcursionPlotter(ResultPlotter["ExcursionResult"]):
    def draw(self, result: "ExcursionResult", title: str) -> dict[str, Figure]:
        if not result.all.size:
            return {}

        figure, (ax_hist, ax_reach) = theme.new_figure(
            title, ncols=2, figsize=(14, 6.5)
        )
        measure = result.measure
        sides = (
            (result.long, theme.LONG, "Long"),
            (result.short, theme.SHORT, "Short"),
        )

        edges, long_counts, short_counts = result.histogram()
        centers = (edges[:-1] + edges[1:]) / 2
        widths = np.diff(edges)
        bottom = np.zeros(centers.shape)
        for (values, color, name), counts in zip(sides, (long_counts, short_counts)):
            if not values.size:
                continue
            ax_hist.bar(
                centers,
                counts,
                bottom=bottom,
                **theme.bar_style(
                    color=color, width=widths, label=f"{name} ({values.size})"
                ),
            )
            bottom = bottom + counts
        ax_hist.set_xlim(edges[0], edges[-1])
        ax_hist.set_xlabel(measure.label)
        ax_hist.legend(loc="upper right")
        theme.panel_title(
            ax_hist, "Distribution", f"trades per {measure.format(widths[0])} bin"
        )

        levels = np.linspace(0, edges[-1], 400)
        for values, color, name in (*sides, (result.all, theme.TOTAL, "All")):
            if not values.size:
                continue
            ax_reach.plot(
                levels, result.reach_share(values, levels), color=color, label=name
            )
        median = float(np.median(result.all))
        ax_reach.axvline(median, color=theme.BASELINE, linewidth=1, zorder=1.5)
        ax_reach.annotate(
            f"median {measure.format(median)}",
            (median, 100),
            xytext=(6, -4),
            textcoords="offset points",
            va="top",
            fontsize=9,
            color=theme.INK_SECONDARY,
        )
        theme.share_axis(ax_reach)
        ax_reach.set_xlim(0, edges[-1])
        ax_reach.set_xlabel(measure.label)
        ax_reach.legend(loc="upper right")
        theme.panel_title(ax_reach, "Reach", "share of trades reaching at least x")
        # measure and window in the key, so differently configured runs don't overwrite
        return {f"{measure.name.lower()}_{result.candles_range}candles": figure}
