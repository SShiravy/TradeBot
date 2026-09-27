from TraderBot.PositionHandlers.Statistics.base import AnalysisResult
from TraderBot.PositionHandlers.Statistics.Plots.theme import RC
from abc import ABC, abstractmethod
from matplotlib.figure import Figure
from pathlib import Path
import matplotlib.pyplot as plt
import logging
import re


logger = logging.getLogger("Statistics")


def _slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")


class ResultPlotter[R: AnalysisResult](ABC):
    """Draws an analysis result. `render` owns theme, saving, showing and closing."""

    @abstractmethod
    def draw(self, result: R, title: str) -> dict[str, Figure]:
        """Figures keyed by a short file-name suffix; {} when there is nothing to draw."""

    def render(
        self,
        result: R,
        label: str = "",
        show: bool = True,
        save_dir: str | Path | None = None,
    ) -> list[Path]:
        title = f"{result.title}  ·  {label}" if label else result.title
        saved: list[Path] = []
        with plt.rc_context(RC):
            figures = self.draw(result, title)
            if not figures:
                logger.info(f"{result.title}: nothing to plot")
                return saved

            if save_dir is not None:
                directory = Path(save_dir)
                directory.mkdir(parents=True, exist_ok=True)
                stem = _slug(f"{label}_{result.title}" if label else result.title)
                for key, figure in figures.items():
                    path = directory / f"{stem}_{key}.png"
                    figure.savefig(path)
                    saved.append(path)

            if show:
                plt.show()

        for figure in figures.values():
            plt.close(figure)
        return saved
