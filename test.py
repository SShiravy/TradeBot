from custom_logger import CustomLogger
import logging


CustomLogger(True, consol_log_level=logging.DEBUG)


async def start_diver_backtest():
    from DivergenceStrategy.backtest_configs import (
        forex_diver_five_m,
        forex_diver_one_m,
        five_m_diver,
        cvd_diver_one_m_cvd,
        coinex_4h_diver,
    )

    await forex_diver_five_m.backtest(200, show_image=True)


async def start_diver_crypto_backtest_pack():
    from BacktestModule.crypto_diver_pack import start_diver_crypto_backtest_pack

    await start_diver_crypto_backtest_pack(send_report=True)


async def start_fibochoch_backtest():
    from FiboChochStrategy.backtest_configs import one_m_forex, coinex_five_m

    await coinex_five_m.backtest(1000)


async def start_fich_diver_backtest():
    from FiboChochDiverStrategy.backtest_configs import coinex_five_m, forex_one_m

    await coinex_five_m.backtest(1000)


if __name__ == "__main__":
    import asyncio

    # asyncio.run(start_diver_crypto_backtest_pack())
    asyncio.run(start_diver_backtest())
    # asyncio.run(start_fibochoch_backtest())
    # asyncio.run(start_fich_diver_backtest())

    # new_backtest()

    # import requests
    # from datetime import datetime

    # import requests
    # from datetime import datetime
    # url = 'https://publicapi.ramzinex.com/exchange/api/v1.0/exchange/chart/tv/history'
    # params = {'symbol':'USDTIRR','resolution':1, 'from':int(datetime.now().timestamp())-10000, 'to':int(datetime.now().timestamp())}
    # print(int(datetime.now().timestamp()))
    # payload = {}
    # headers = {}
    # response = requests.request('GET', url, headers=headers, data=payload, params=params)
    # print(response.text)


# TODO: position handler with MA and control tp sl with it
# TODO: multiple loss in a row for long and short handler
# TODO: pos open candle should not check in position handler
# TODO: check market is open not woking! last tick is just now always


# result=OrderSendResult(retcode=10009, deal=0, order=0, volume=0.0, price=0.0, bid=0.0, ask=0.0, comment='Request executed', request_id=755861029, retcode_external=0, request=TradeRequest(action=6, magic=0, order=0, symbol='XAUUSD!', volume=0.0, price=0.0, stoplimit=0.0, sl=5080.23, tp=5059.23, deviation=0, type=0, type_filling=0, type_time=0, expiration=0, comment='', position=88630289, position_by=0))]|
# result=OrderSendResult(retcode=10027, deal=0, order=0, volume=0.0, price=0.0, bid=0.0, ask=0.0, comment='AutoTrading disabled by client', request_id=0, retcode_external=0, request=TradeRequest(action=1, magic=80713, order=0, symbol='XAUUSD!', volume=0.01, price=5008.21, stoplimit=0.0, sl=5002.32, tp=5018.545, deviation=20, type=0, type_filling=1, type_time=0, expiration=0, comment='PythonTraderBot', position=0, position_by=0))]|
# result=OrderSendResult(retcode=10009, deal=70468212, order=88630289, volume=0.01, price=5073.23, bid=5073.23, ask=5073.51, comment='Request executed', request_id=755861028, retcode_external=0, request=TradeRequest(action=1, magic=80713, order=0, symbol='XAUUSD!', volume=0.01, price=5073.23, stoplimit=0.0, sl=5080.23, tp=5057.94, deviation=20, type=1, type_filling=1, type_time=0, expiration=0, comment='PythonTraderBot', position=0, position_by=0))]|
