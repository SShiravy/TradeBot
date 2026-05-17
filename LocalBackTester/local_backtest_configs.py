from LocalBackTester.agent import LocalAgent
from Forex.bot_config import ForexDiverTradeConfig
from DivergenceStrategy.divergence import Divergence
from Coinex.bot_config import CoinexDiverTradeConfig
from TradingModule.PositionHandlers.ratio_handlers import (
    SlTpRatioForex,
    SlTpRatioCrypto,
)
from TradingModule.PositionHandlers.simple_handlers import SimpleCrypto
from LocalBackTester.all_charts import (
    XAUUSD_1m_5000_test,
    SOLUSD_1m_5000_test,
    XAUUSD_1m_99000,
    SOLUSD_1m_99000,
    BTCUSDT_1h_2024_9,
    SOLUSDT_1h_2024_9,
)


local_agent = LocalAgent()


# Forex -----

diver_forex_xau_1m_5000_test = ForexDiverTradeConfig(
    chart=XAUUSD_1m_5000_test,
    second_chart=SOLUSD_1m_5000_test,
    n_candle_check=500,
    strategy=Divergence(3, 500, [], name="ForexDiver", inverse_diver_long=True),
    position_handler=SlTpRatioForex(
        local_agent,
        ratio=4,
        stoploss_pip=10,
        initial_volume=0.01,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=True,
    merge_two_chart_time=True,
    send_signal=False,
)
diver_forex_xau_1m_5000_test.agent = local_agent


diver_forex_xau_1m = ForexDiverTradeConfig(
    chart=XAUUSD_1m_99000,
    second_chart=SOLUSD_1m_99000,
    n_candle_check=500,
    strategy=Divergence(3, 500, [], name="ForexDiver", inverse_diver_long=True),
    position_handler=SlTpRatioForex(
        local_agent,
        ratio=3,
        stoploss_pip=20,
        initial_volume=0.01,
        long_trade=False,
        short_trade=False,
    ),
    heikingashi_chartdata=True,
    merge_two_chart_time=True,
    send_signal=False,
)
diver_forex_xau_1m.agent = local_agent


# Crypto

local_agent = LocalAgent()
diver_crypto_solbtc_1m = CoinexDiverTradeConfig(
    chart=SOLUSDT_1h_2024_9,
    second_chart=BTCUSDT_1h_2024_9,
    n_candle_check=100,
    strategy=Divergence(3, 500, [], name="CoinexDiver", inverse_diver_long=True),
    position_handler=SlTpRatioCrypto(
        local_agent,
        ratio=2,
        stoploss_percent=2,
        initial_volume=10,
        riskfree_trigger_ratio=0,
        leverage=10,
        long_trade=False,
        short_trade=False,
    ),
    agent=local_agent,  # type: ignore
    heikingashi_chartdata=True,
    send_signal=False,
)
