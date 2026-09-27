"""One look for every statistics figure: palette, rc params and small axis helpers."""

from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter, MaxNLocator
from typing import Iterable, Sequence
import matplotlib.pyplot as plt


# chrome
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"

# identity: fixed categorical order, colorblind-safe as a set
LONG = "#2a78d6"
SHORT = "#eb6834"
TOTAL = "#1baf7a"

# polarity: diverging poles with a neutral in between
GAIN = "#2a78d6"
LOSS = "#e34948"
NEUTRAL = "#c3c2b7"

WASH = 0.12

NOTE = {"fontsize": 9, "fontweight": "normal", "color": INK_MUTED}

RC = {
    "axes.unicode_minus": False,
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
    "savefig.dpi": 150,
    "figure.dpi": 100,
    "font.family": "sans-serif",
    "font.sans-serif": ["Segoe UI", "Helvetica Neue", "Arial", "DejaVu Sans"],
    "font.size": 10,
    "text.color": INK,
    "axes.titlesize": 11,
    "axes.titleweight": "semibold",
    "axes.titlecolor": INK,
    "axes.titlelocation": "left",
    "axes.titlepad": 10,
    "axes.labelsize": 10,
    "axes.labelcolor": INK_SECONDARY,
    "axes.edgecolor": BASELINE,
    "axes.linewidth": 1,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.spines.left": False,
    "axes.grid": True,
    "axes.grid.axis": "y",
    "axes.axisbelow": True,
    "grid.color": GRID,
    "grid.linewidth": 0.8,
    "grid.linestyle": "-",
    "xtick.color": INK_MUTED,
    "ytick.color": INK_MUTED,
    "xtick.labelcolor": INK_SECONDARY,
    "ytick.labelcolor": INK_SECONDARY,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "xtick.major.size": 0,
    "ytick.major.size": 0,
    "xtick.major.pad": 6,
    "ytick.major.pad": 6,
    "lines.linewidth": 2,
    "lines.solid_capstyle": "round",
    "lines.solid_joinstyle": "round",
    "legend.frameon": False,
    "legend.fontsize": 9,
    "legend.labelcolor": INK_SECONDARY,
    "legend.handlelength": 1.2,
}


def new_figure(
    title: str,
    nrows: int = 1,
    ncols: int = 1,
    figsize: tuple[float, float] = (13, 7),
    height_ratios: Sequence[float] | None = None,
    sharex: bool = False,
) -> tuple[Figure, list[Axes]]:
    figure, axes = plt.subplots(
        nrows,
        ncols,
        figsize=figsize,
        sharex=sharex,
        squeeze=False,
        layout="constrained",
        gridspec_kw={"height_ratios": height_ratios},
    )
    figure.get_layout_engine().set(h_pad=0.12, w_pad=0.15)  # type: ignore[union-attr]
    figure.suptitle(title, x=0.01, ha="left", fontsize=14, fontweight="semibold")
    return figure, list(axes.ravel())


def compact(value: float) -> str:
    """Short label: 1234.5 -> 1.2K, -2_500_000 -> -2.5M, 95.0 -> 95, 12.34 -> 12.3"""
    magnitude = abs(value)
    for threshold, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if magnitude >= threshold:
            return f"{value / threshold:,.1f}{suffix}"
    if magnitude >= 100 or float(value).is_integer():
        return f"{value:,.0f}"
    return f"{value:,.{1 if magnitude >= 10 else 2}f}"


def polarity_colors(values: Iterable[float]) -> list[str]:
    return [GAIN if v > 0 else LOSS if v < 0 else NEUTRAL for v in values]


def bar_style(**kwargs) -> dict:
    """A surface-colored edge draws the gap between touching bars (no borders)."""
    return {"edgecolor": SURFACE, "linewidth": 1.2, **kwargs}


def panel_title(ax: Axes, title: str, note: str = "") -> None:
    ax.set_title(title, loc="left")
    if note:
        ax.set_title(note, loc="right", **NOTE)


def baseline(ax: Axes, value: float = 0.0, vertical: bool = False) -> None:
    line = ax.axvline if vertical else ax.axhline
    line(value, color=BASELINE, linewidth=1, zorder=1.5)


def number_axis(ax: Axes, decimals: int = 0, axis: str = "y") -> None:
    formatter = FuncFormatter(lambda v, _: f"{v:,.{decimals}f}")
    (ax.yaxis if axis == "y" else ax.xaxis).set_major_formatter(formatter)


def share_axis(ax: Axes) -> None:
    ax.set_ylim(0, 102)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}%"))


def trade_number_axis(ax: Axes, n_trades: int) -> None:
    ax.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=12))
    ax.set_xlim(0, max(n_trades, 1))
    ax.set_xlabel("Trade #")


def end_label(ax: Axes, x: float, y: float, text: str, color: str) -> None:
    """Ringed end-dot with the final value beside it."""
    ax.plot(
        [x],
        [y],
        "o",
        color=color,
        markersize=6,
        markeredgecolor=SURFACE,
        markeredgewidth=2,
        zorder=4,
    )
    ax.annotate(
        text,
        (x, y),
        xytext=(8, 0),
        textcoords="offset points",
        va="center",
        fontsize=9,
        color=INK,
        annotation_clip=False,
    )


def marker(ax: Axes, x: float, y: float, color: str, text: str, above: bool) -> None:
    """Ringed dot on an extreme point with a short label."""
    ax.plot(
        [x],
        [y],
        "o",
        color=color,
        markersize=7,
        markeredgecolor=SURFACE,
        markeredgewidth=2,
        zorder=4,
    )
    ax.annotate(
        text,
        (x, y),
        xytext=(0, 9 if above else -9),
        textcoords="offset points",
        ha="center",
        va="bottom" if above else "top",
        fontsize=9,
        color=INK,
    )


def empty_panel(ax: Axes, message: str) -> None:
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)
    ax.spines["bottom"].set_visible(False)
    ax.text(
        0.5,
        0.5,
        message,
        transform=ax.transAxes,
        ha="center",
        va="center",
        color=INK_MUTED,
    )
