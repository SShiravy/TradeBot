from Forex.agent import ForexAgent
from ChartModule import Chart, TimeFrame
from ChartModule.plot import TwoChartPlot
from TradingModule import TradeConfig, TraderBot, ExchangeAgent, OrderSide
from TradingModule import commands
from TradingModule.position_handlers import SimpleForexHandler
from TradingModule.Strategies import Divergence
from dataclasses import dataclass, field
from custom_logger import CustomLogger
import asyncio

CustomLogger(log_file=True, file_log_name="ForexBot")


@dataclass(kw_only=True)
class ForexDiverTradeConfig(TradeConfig):
    second_chart: Chart
    agent: ExchangeAgent = field(default=ForexAgent())
    strategy: Divergence  # type: ignore[override]

    async def task(self, telegram_bot):
        base_chartdata = self.agent.get_chartdata(self.chart, 200)
        second_chartdata = self.agent.get_chartdata(self.second_chart, 200)

        if base_chartdata is None or second_chartdata is None:
            raise ValueError(f"chart data is None from {self.agent.__qualname__}")

        signal = self.strategy.check_signal(
            base_chartdata, second_chartdata, self.long_signal, self.short_signal
        )
        if signal is None:
            return self.give_delay(base_chartdata[-1])

        position = self.position_handler.generate_position(signal)

        if (self.long_trade and position.side is OrderSide.BUY) or (
            self.short_trade and position.side is OrderSide.SELL
        ):
            command = commands.OpenPosition(position)
            command.execute(self.agent)

        if self.send_signal:
            plot = TwoChartPlot(base_chartdata, second_chartdata)
            self.strategy.draw(plot, signal, draw_indicators=True)
            position.draw(plot.base_plot)
            img_path = plot.save_image()
            await telegram_bot.send_photo_to_channel(
                img_path, self.msg_generator(position)
            )

        return self.give_delay(signal.candle, jump=True)


one_m_diver = ForexDiverTradeConfig(
    chart=Chart("XAUUSD!", TimeFrame.one_minute),
    second_chart=Chart("SOLUSD", TimeFrame.one_minute),
    strategy=Divergence(3, 3, [], name="ForexDivergence", inverse_diver_long=True),
    position_handler=SimpleForexHandler(ForexAgent()),
)


TraderBot("ForexTraderBot", [one_m_diver])


if __name__ == "__main__":
    asyncio.run(TraderBot().start())
