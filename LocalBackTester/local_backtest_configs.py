from ChartModule.Indicators.moving_avg import EMA
from LocalBackTester.agent import LocalAgent
from Forex.bot_config import ForexDiverTradeConfig
from DivergenceStrategy.divergence import Divergence
from Coinex.bot_config import CoinexDiverTradeConfig
from TradingModule.PositionHandlers import (
    SteppingHandlerForex,
    SteppingHandlerCrypto,
)
from LocalBackTester.all_charts import (
    AVAXUSDT_5m_2024_month0203,
    AVAXUSDT_5m_test_2024,
    BTCUSDT_5m_test_2024,
    FTMUSDT_5m_2024_month0203,
    BTCUSDT_5m_2024_month0203,
    FTMUSDT_5m_test_2024,
    NEARUSDT_5m_2024_month0203,
    NEARUSDT_5m_test_2024,
    PENDLEUSDT_5m_2024_month0203,
    PENDLEUSDT_5m_test_2024,
    RNDRUSDT_5m_2024_month0203,
    RNDRUSDT_5m_test_2024,
    SOLUSDT_5m_2024_month0203,
    SOLUSDT_5m_test_2024,
    XAUUSD_1m_5000_test,
    SOLUSD_1m_5000_test,
    XAUUSD_1m_99000,
    SOLUSD_1m_99000,
    SOLUSDT_5m_2026_4_5,
    BTCUSDT_5m_2026_4_5,
    SOLUSDT_5m_test,
    BTCUSDT_5m_test,
)
from TradingModule.PositionHandlers.trading_constraints import (
    LoseInRowConstraint,
    SideConstraint,
)


local_agent = LocalAgent()


# Forex -----

diver_forex_xau_1m_5000_test = ForexDiverTradeConfig(
    chart=XAUUSD_1m_5000_test,
    second_chart=SOLUSD_1m_5000_test,
    n_candle_check=300,
    strategy=Divergence(5, 100, [EMA(120)], name="ForexDiver"),
    position_handler=SteppingHandlerForex(
        local_agent,
        stoploss_pip=30,
        targets_ratio=[1, 2, 3],
        targets_ratio_volumes=[0.01, 0.01, 0.01],
        targets_in_pip=[20],
        targets_in_pip_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
        trading_constraints=[
            # SideConstraint(n_pos_each_side=1, n_bar=30, check_closed_positions=False),
            # LoseInRowConstraint(n_long_lose=1, n_short_lose=1, n_bar=30),
        ],
    ),
    heikingashi_chartdata=True,
    merge_two_chart_time=True,
    send_signal=False,
)
diver_forex_xau_1m_5000_test.agent = local_agent


diver_forex_xau_1m_99000 = ForexDiverTradeConfig(
    chart=XAUUSD_1m_99000,
    second_chart=SOLUSD_1m_99000,
    n_candle_check=300,
    strategy=Divergence(5, 100, [EMA(10)], name="ForexDiver"),
    position_handler=SteppingHandlerForex(
        local_agent,
        stoploss_pip=30,
        targets_ratio=[1, 2, 3],
        targets_ratio_volumes=[0.01, 0.01, 0.01],
        targets_in_pip=[20],
        targets_in_pip_volumes=[0.01],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
        trading_constraints=[
            SideConstraint(n_pos_each_side=1, n_bar=30, check_closed_positions=False),
            LoseInRowConstraint(n_long_lose=1, n_short_lose=1, n_bar=30),
        ],
    ),
    heikingashi_chartdata=True,
    merge_two_chart_time=True,
    send_signal=False,
)
diver_forex_xau_1m_99000.agent = local_agent


# Crypto

local_agent = LocalAgent()
diver_solbtc_5m_17570 = CoinexDiverTradeConfig(
    chart=SOLUSDT_5m_2026_4_5,
    second_chart=BTCUSDT_5m_2026_4_5,
    n_candle_check=100,
    strategy=Divergence(3, 500, [], name="CoinexDiver", inverse_diver_long=True),
    position_handler=SteppingHandlerCrypto(
        local_agent,
        leverage=10,
        stoploss_percent=0.1,
        targets_ratio=[1, 2, 3],
        initial_volume=[10, 10, 10],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    agent=local_agent,  # type: ignore
    heikingashi_chartdata=True,
    send_signal=False,
)


diver_solbtc_5m_1000 = CoinexDiverTradeConfig(
    chart=SOLUSDT_5m_test,
    second_chart=BTCUSDT_5m_test,
    n_candle_check=100,
    strategy=Divergence(3, 500, [], name="CoinexDiver", inverse_diver_long=True),
    position_handler=SteppingHandlerCrypto(
        local_agent,
        leverage=10,
        stoploss_percent=0.1,
        targets_ratio=[1, 2, 3],
        initial_volume=[10, 10, 10],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    agent=local_agent,  # type: ignore
    heikingashi_chartdata=True,
    send_signal=False,
)


diver_ftmbtc_5m_17280_2024_month0203 = CoinexDiverTradeConfig(
    chart=FTMUSDT_5m_2024_month0203,
    second_chart=BTCUSDT_5m_2024_month0203,
    n_candle_check=100,
    strategy=Divergence(3, 300, [], name="CoinexDiver", inverse_diver_long=True),
    position_handler=SteppingHandlerCrypto(
        local_agent,
        leverage=10,
        stoploss_percent=0.25,
        targets_ratio=[1, 2, 3],
        initial_volume=[3, 3, 3],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    agent=local_agent,  # type: ignore
    heikingashi_chartdata=True,
    send_signal=False,
    merge_two_chart_time=False,
)


diver_ftmbtc_5m_test = CoinexDiverTradeConfig(
    chart=FTMUSDT_5m_test_2024,
    second_chart=BTCUSDT_5m_test_2024,
    n_candle_check=100,
    strategy=Divergence(3, 300, [], name="CoinexDiver", inverse_diver_long=True),
    position_handler=SteppingHandlerCrypto(
        local_agent,
        leverage=10,
        stoploss_percent=0.1,
        targets_ratio=[1, 2, 3],
        initial_volume=[10, 10, 10],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    agent=local_agent,  # type: ignore
    heikingashi_chartdata=True,
    send_signal=False,
)


diver_avaxbtc_5m_17280_2024_month0203 = CoinexDiverTradeConfig(
    chart=AVAXUSDT_5m_2024_month0203,
    second_chart=BTCUSDT_5m_2024_month0203,
    n_candle_check=100,
    strategy=Divergence(3, 300, [], name="CoinexDiver", inverse_diver_long=True),
    position_handler=SteppingHandlerCrypto(
        local_agent,
        leverage=10,
        stoploss_percent=0.25,
        targets_ratio=[1, 2, 3],
        initial_volume=[3, 3, 3],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    agent=local_agent,  # type: ignore
    heikingashi_chartdata=True,
    send_signal=False,
    merge_two_chart_time=False,
)


diver_avaxbtc_5m_test = CoinexDiverTradeConfig(
    chart=AVAXUSDT_5m_test_2024,
    second_chart=BTCUSDT_5m_test_2024,
    n_candle_check=100,
    strategy=Divergence(3, 300, [], name="CoinexDiver", inverse_diver_long=True),
    position_handler=SteppingHandlerCrypto(
        local_agent,
        leverage=10,
        stoploss_percent=0.1,
        targets_ratio=[1, 2, 3],
        initial_volume=[10, 10, 10],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    agent=local_agent,  # type: ignore
    heikingashi_chartdata=True,
    send_signal=False,
)


diver_nearbtc_5m_17280_2024_month0203 = CoinexDiverTradeConfig(
    chart=NEARUSDT_5m_2024_month0203,
    second_chart=BTCUSDT_5m_2024_month0203,
    n_candle_check=100,
    strategy=Divergence(3, 300, [], name="CoinexDiver", inverse_diver_long=True),
    position_handler=SteppingHandlerCrypto(
        local_agent,
        leverage=10,
        stoploss_percent=0.25,
        targets_ratio=[1, 2, 3],
        initial_volume=[3, 3, 3],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    agent=local_agent,  # type: ignore
    heikingashi_chartdata=True,
    send_signal=False,
    merge_two_chart_time=False,
)


diver_nearbtc_5m_test = CoinexDiverTradeConfig(
    chart=NEARUSDT_5m_test_2024,
    second_chart=BTCUSDT_5m_test_2024,
    n_candle_check=100,
    strategy=Divergence(3, 300, [], name="CoinexDiver", inverse_diver_long=True),
    position_handler=SteppingHandlerCrypto(
        local_agent,
        leverage=10,
        stoploss_percent=0.1,
        targets_ratio=[1, 2, 3],
        initial_volume=[10, 10, 10],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    agent=local_agent,  # type: ignore
    heikingashi_chartdata=True,
    send_signal=False,
)


diver_pendlebtc_5m_17280_2024_month0203 = CoinexDiverTradeConfig(
    chart=PENDLEUSDT_5m_2024_month0203,
    second_chart=BTCUSDT_5m_2024_month0203,
    n_candle_check=100,
    strategy=Divergence(3, 300, [], name="CoinexDiver", inverse_diver_long=True),
    position_handler=SteppingHandlerCrypto(
        local_agent,
        leverage=10,
        stoploss_percent=0.25,
        targets_ratio=[1, 2, 3],
        initial_volume=[3, 3, 3],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    agent=local_agent,  # type: ignore
    heikingashi_chartdata=True,
    send_signal=False,
    merge_two_chart_time=False,
)


diver_pendlebtc_5m_test = CoinexDiverTradeConfig(
    chart=PENDLEUSDT_5m_test_2024,
    second_chart=BTCUSDT_5m_test_2024,
    n_candle_check=100,
    strategy=Divergence(3, 300, [], name="CoinexDiver", inverse_diver_long=True),
    position_handler=SteppingHandlerCrypto(
        local_agent,
        leverage=10,
        stoploss_percent=0.1,
        targets_ratio=[1, 2, 3],
        initial_volume=[10, 10, 10],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    agent=local_agent,  # type: ignore
    heikingashi_chartdata=True,
    send_signal=False,
)


diver_rndrbtc_5m_17280_2024_month0203 = CoinexDiverTradeConfig(
    chart=RNDRUSDT_5m_2024_month0203,
    second_chart=BTCUSDT_5m_2024_month0203,
    n_candle_check=100,
    strategy=Divergence(3, 300, [], name="CoinexDiver", inverse_diver_long=True),
    position_handler=SteppingHandlerCrypto(
        local_agent,
        leverage=10,
        stoploss_percent=0.25,
        targets_ratio=[1, 2, 3],
        initial_volume=[3, 3, 3],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    agent=local_agent,  # type: ignore
    heikingashi_chartdata=True,
    send_signal=False,
    merge_two_chart_time=False,
)


diver_rndrbtc_5m_test = CoinexDiverTradeConfig(
    chart=RNDRUSDT_5m_test_2024,
    second_chart=BTCUSDT_5m_test_2024,
    n_candle_check=100,
    strategy=Divergence(3, 300, [], name="CoinexDiver", inverse_diver_long=True),
    position_handler=SteppingHandlerCrypto(
        local_agent,
        leverage=10,
        stoploss_percent=0.1,
        targets_ratio=[1, 2, 3],
        initial_volume=[10, 10, 10],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    agent=local_agent,  # type: ignore
    heikingashi_chartdata=True,
    send_signal=False,
)


diver_solbtc_5m_17280_2024_month0203 = CoinexDiverTradeConfig(
    chart=SOLUSDT_5m_2024_month0203,
    second_chart=BTCUSDT_5m_2024_month0203,
    n_candle_check=100,
    strategy=Divergence(3, 300, [], name="CoinexDiver", inverse_diver_long=True),
    position_handler=SteppingHandlerCrypto(
        local_agent,
        leverage=10,
        stoploss_percent=0.25,
        targets_ratio=[1, 2, 3],
        initial_volume=[3, 3, 3],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    agent=local_agent,  # type: ignore
    heikingashi_chartdata=True,
    send_signal=False,
    merge_two_chart_time=False,
)


diver_solbtc_5m_test = CoinexDiverTradeConfig(
    chart=SOLUSDT_5m_test_2024,
    second_chart=BTCUSDT_5m_test_2024,
    n_candle_check=100,
    strategy=Divergence(3, 300, [], name="CoinexDiver", inverse_diver_long=True),
    position_handler=SteppingHandlerCrypto(
        local_agent,
        leverage=10,
        stoploss_percent=0.1,
        targets_ratio=[1, 2, 3],
        initial_volume=[10, 10, 10],
        trail_stop=True,
        long_trade=False,
        short_trade=False,
    ),
    agent=local_agent,  # type: ignore
    heikingashi_chartdata=True,
    send_signal=False,
)
