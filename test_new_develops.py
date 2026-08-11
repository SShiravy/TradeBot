from custom_logger import CustomLogger
import logging

CustomLogger(True, consol_log_level=logging.DEBUG)


async def divergence_test():
    from DivergenceStrategy.diver_configs import xau_jpy_1m

    res = await xau_jpy_1m.backtest()
    print(f"backtest result: {res}")
    # TODO: remove unnecessary logs


if __name__ == "__main__":
    from asyncio import run
    import cProfile
    import pstats

    profiler = cProfile.Profile()
    profiler.enable()

    run(divergence_test())

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats("cumtime")
    stats.print_stats(30)
