from TradingModule.trader_bot import TraderBot
import json
import hashlib


def generate_hash(payload: dict):
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


def give_config_dict(trade_config: TraderBot):
    conf_dict = trade_config.export_config()
    conf_dict.update(trade_config.strategy.export_config())

    return conf_dict


def give_config_hash(trade_config: TraderBot):
    conf_dict = give_config_dict(trade_config)
    return generate_hash(conf_dict)
