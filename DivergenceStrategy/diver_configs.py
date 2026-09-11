from ChartModule.models import Chart, TimeFrame, ChartType
from DivergenceStrategy.divergence import Divergence, DivergenceConfig
from Forex.agent import ForexAgent
from TradingModule.PositionHandlers.stepping_handler import SteppingHandlerForex


xau_jpy_1m = DivergenceConfig(
    chart=Chart("XAUUSD!", TimeFrame.one_minute, ChartType.Simple),
    second_chart=Chart("USDJPY!", TimeFrame.one_minute, ChartType.Heikinashi),
    agent=ForexAgent(),
    strategy=Divergence(5, 100, [], name="ForexDiver", inverse_diver_long=True),
    bar_between_signals=2,
    position_generator=SteppingHandlerForex(
        ForexAgent(),
        stoploss_pip=5,
        targets_ratio=[],
        targets_ratio_volumes=[],
        targets_in_pip=[20],
        targets_in_pip_volumes=[0.01],
        trail_stop=False,
        pip_trail_stop_under_entry=False,
        long_trade=False,
        short_trade=False,
    ),
)
