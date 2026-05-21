import matplotlib.pyplot as plt
import pandas as pd


def plot_hourly_pnl_histogram(
    pnl_list: list[float], timestamps: list[int], plot_name: str, show: bool = True
):
    """
    Plot hourly PnL histogram.

    Parameters
    ----------
    pnl_list : list[float]
        List of position pnl values.

    timestamps : list[int]
        Unix timestamps (seconds).
    """

    if len(pnl_list) != len(timestamps):
        raise ValueError("pnl_list and timestamps must have same length")
    df = pd.DataFrame(
        {
            "timestamp": timestamps,
            "pnl": pnl_list,
        }
    )
    df["datetime"] = pd.to_datetime(
        df["timestamp"],
        unit="s",
        utc=True,
    )
    df["hour"] = df["datetime"].dt.hour
    hourly_pnl = df.groupby("hour")["pnl"].sum().reindex(range(24), fill_value=0)
    plt.figure(figsize=(14, 6))
    plt.bar(
        hourly_pnl.index,
        hourly_pnl.values,  # type: ignore
    )
    # Zero line in center
    plt.axhline(
        y=0,
        linewidth=1,
    )
    plt.xticks(range(24))
    plt.xlabel("Hour of Day (UTC)")
    plt.ylabel("Total PnL")
    plt.title("Hourly PnL Histogram")
    plt.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(rf"D:\TraderBot\LocalBackTester\Images\{plot_name}.png")
    if show:
        plt.show()
