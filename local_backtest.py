from LocalBackTester.agent import LocalAgent
from LocalBackTester.all_charts import BTCUSDT_1h_2024_9,SOLUSDT_1h_2024_9
from ChartModule.plot import ChartPlot


def plot_csv_kline():
    agent = LocalAgent()
    chartdata = agent.get_chartdata(SOLUSDT_1h_2024_9)
    ChartPlot(chartdata,len(chartdata.candles)).show() # type: ignore


if __name__ == "__main__":
    plot_csv_kline()

    