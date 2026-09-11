from Coinex import CoinexAgent, CoinexDiverTradeConfig
from ChartModule import Chart, TimeFrame
from DivergenceStrategy.divergence import Divergence
from TradingModule.PositionHandlers import SlTpRatioCrypto
from TradingModule.models import PositionsReport
from TradingModule.reporter import TelegramReporter
from itertools import product
from config import settings
from datetime import datetime
import logging

# Coinex ----------------------------------------------------------------


coinex_agent = CoinexAgent(settings.COINEX_ACCESS_ID, settings.COINEX_SECRET_KEY)


param_grid = {
    "symbol": ["SOLUSDT", "LINKUSDT", "SONICUSDT", "ETHUSDT", "INJUSDT", "RENDERUSDT"],
    "ratio": [1],
    "body_candle": [True, False],
    "sl_percent": [0.25],
}

all_params_set = [
    dict(zip(param_grid.keys(), combination))
    for combination in product(*param_grid.values())
]


async def start_diver_crypto_backtest_pack(send_report=False):
    if send_report:
        await TelegramReporter().send_msg(
            channel_id=settings.TELEGRAM_BACKTEST_REPORT_CHANNEL,
            msg=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            + " Starting Divergence Crypto Backtest Pack",
        )

    for params_set in all_params_set:
        logging.info(f"Backtesting with params:\n{params_set}")
        five_m_diver = CoinexDiverTradeConfig(
            chart=Chart(params_set["symbol"], TimeFrame.five_minutes),
            second_chart=Chart("BTCUSDT", TimeFrame.five_minutes),
            strategy=Divergence(
                5,
                200,
                [],
                name="CoinexDiver",
                inverse_diver_long=True,
                body_candle=params_set["body_candle"],
            ),
            position_generator=SlTpRatioCrypto(
                coinex_agent,
                ratio=params_set["ratio"],
                stoploss_percent=params_set["sl_percent"],
                initial_volume=10,
                leverage=10,
                long_trade=False,
                short_trade=False,
            ),
            agent=coinex_agent,
        )
        res = await five_m_diver.backtest(1000, show_image=False)
        overal_report = PositionsReport.give_overall_report(res[-2])
        final_report = str(overal_report) + "\n" + f"Params:\n{params_set}"
        pnl = overal_report.pnl
        if pnl > 0:
            final_report = "🟢 PROFITABLE 🟢\n" + final_report
        elif pnl < 0:
            final_report = "🔴 NOT PROFITABLE 🔴\n" + final_report
        else:
            final_report = "⚪ BREAKEVEN ⚪\n" + final_report

        if send_report:
            await TelegramReporter().send_msg(
                channel_id=settings.TELEGRAM_BACKTEST_REPORT_CHANNEL, msg=final_report
            )
