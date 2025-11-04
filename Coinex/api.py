import hmac
import hashlib
import time
import requests
import json
import logging
from enum import Enum
from urllib.parse import urlparse, urlencode

logger = logging.getLogger("coinex_api")




class CoinexTimeFrame(Enum):
    ONE_MINUTE = "1min"
    THREE_MINUTES = "3min"
    FIVE_MINUTES = "5min"
    FIFTEEN_MINUTES = "15min"
    THIRTY_MINUTES = "30min"
    ONE_HOUR = "1hour"
    TWO_HOURS = "2hour"
    FOUR_HOURS = "4hour"
    SIX_HOURS = "6hour"
    TWELVE_HOURS = "12hour"
    ONE_DAY = "1day"
    THREE_DAY = "3day"
    ONE_WEEK = "1week"


class CoinexAPI:
    HEADERS = {
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "application/json",
        "X-COINEX-KEY": "",
        "X-COINEX-SIGN": "",
        "X-COINEX-TIMESTAMP": "",
    }
    base_url = "https://api.coinex.com/v2"

    def __init__(self, access_id: str = "", secret_key: str = ""):
        self.__access_id = access_id
        self.__secret_key = secret_key
        self.headers = self.HEADERS.copy()

    def _sign(self, method, request_path, body, timestamp):
        prepared_str = f"{method}{request_path}{body}{timestamp}"
        signature = (
            hmac.new(
                bytes(self.__secret_key, "latin-1"),
                msg=bytes(prepared_str, "latin-1"),
                digestmod=hashlib.sha256,
            )
            .hexdigest()
            .lower()
        )
        return signature

    def get_common_headers(self, signed_str, timestamp):
        headers = self.HEADERS.copy()
        headers["X-COINEX-KEY"] = self.__access_id
        headers["X-COINEX-SIGN"] = signed_str
        headers["X-COINEX-TIMESTAMP"] = timestamp
        headers["Content-Type"] = "application/json; charset=utf-8"
        return headers

    def _request(self, method, end_point, params={}, data={}):
        url = self.base_url + end_point
        req = urlparse(url)
        request_path = req.path

        timestamp = str(int(time.time() * 1000))
        if method.upper() == "GET":
            # If params exist, query string needs to be added to the request path
            if params:
                for item in params.copy():
                    if params[item] is None:
                        del params[item]
                        continue
                request_path = request_path + "?" + urlencode(params)

            signed_str = self._sign(method, request_path, body="", timestamp=timestamp)
            response = requests.get(
                url,
                params=params,
                headers=self.get_common_headers(signed_str, timestamp),
            )

        else:
            data = json.dumps(data)
            signed_str = self._sign(
                method, request_path, body=data, timestamp=timestamp
            )
            response = requests.post(
                url, data, headers=self.get_common_headers(signed_str, timestamp)
            )

        if response.status_code != 200 or not response.json()["data"]:
            logger.error(
                f"Request failed with status code {response.status_code}-{response.text}"
            )

        logger.debug(f"{method} {url}: {data=}-{params=} -> {response.status_code}")
        return response.json()


class CoinexFuturesAPI(CoinexAPI):
    def __init__(self, access_id: str = "", secret_key: str = "") -> None:
        super().__init__(access_id, secret_key)

    def get_balance(self):
        end_point = "/assets/futures/balance"
        return self._request("GET", end_point)

    def get_market_info(self, symbol):
        end_point = "/futures/market"
        res = self._request("GET", end_point, params={"market": symbol})
        if not res["data"]:
            logger.error(f"Coinex failed on getting market info {symbol=}")
        return res["data"]

    def get_kline(self, symbol, timeframe: CoinexTimeFrame, limit=200):
        end_point = "/futures/kline"
        res = self._request(
            "GET",
            end_point,
            params={"market": symbol, "limit": limit, "period": timeframe.value},
        )
        return res["data"]

    def get_position_history(self, symbol=None, limit=10):
        end_point = "/futures/finished-position"
        result = self._request(
            "GET",
            end_point,
            params={"market": symbol, "market_type": "FUTURES", "limit": limit},
        )
        if not result.get("data"):
            logger.warning(f"No Closed Position in {symbol}: {result=}")
            return None
        return result["data"]

    def set_leverage(self, symbol, leverage):
        end_point = "/futures/adjust-position-leverage"
        return self._request(
            "POST",
            end_point,
            data={
                "market": symbol,
                "margin_mode": "isolated",
                "market_type": "FUTURES",
                "leverage": leverage,
            },
        )

    def place_order(self, symbol, side, type, amount, price=""):
        end_point = "/futures/order"
        result = self._request(
            "POST",
            end_point,
            data={
                "market": symbol,
                "market_type": "FUTURES",
                "side": side,
                "type": type,
                "amount": amount,
            },
        )
        if not result["data"]:
            logger.error(f"Coinex Failed opening position: {result}")
            return None
        return result["data"]

    def place_stoploss(self, symbol, price):
        end_point = "/futures/set-position-stop-loss"
        result = self._request(
            "POST",
            end_point,
            data={
                "market": symbol,
                "market_type": "FUTURES",
                "stop_loss_type": "latest_price",
                "stop_loss_price": price,
            },
        )
        if not result["data"]:
            logger.error(f"Coinex Failed on Placing SL: {result}")
        return result["data"]

    def place_takeprofit(self, symbol, price):
        end_point = "/futures/set-position-take-profit"
        result = self._request(
            "POST",
            end_point,
            data={
                "market": symbol,
                "market_type": "FUTURES",
                "take_profit_type": "latest_price",
                "take_profit_price": price,
            },
        )
        if not result["data"]:
            logger.error(f"Coinex Failed on Placing TP: {result}")
        return result["data"]
    
    def close_position(self,symbol, amount):
        end_point = "/futures/close-position"
        result = self._request(
            "POST",
            end_point,
            data={
                "market": symbol,
                "market_type": "FUTURES",
                "type": "market",
                "amount": amount,
            },
        )
        if not result["data"]:
            logger.error(f"Coinex Failed on Closing Position with {amount=} on {symbol}: {result}")
        return result["data"]

