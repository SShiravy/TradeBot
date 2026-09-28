from typing import Any
from ExchangeAgents.BitUnix.error_codes import ErrorCode
import requests
import hashlib
import logging
import json
import time
import uuid


logger = logging.getLogger("BitUnixAPI")


class BitUnixAPIError(Exception):
    def __init__(self, message: str, code: int | None = None) -> None:
        super().__init__(message)
        self.code = code


class BitUnixAPI:
    """
    Bitunix futures OpenAPI
    https://www.bitunix.com/api-docs/futures/common/introduction.html
    Every method returns the `data` of the response, raises BitUnixAPIError on failure
    """

    base_url = "https://fapi.bitunix.com"

    def __init__(self, api_key: str, secret_key: str, timeout: float = 10) -> None:
        self.__api_key = api_key
        self.__secret_key = secret_key
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {"language": "en-US", "Content-Type": "application/json"}
        )

    def _sign_auth(self, query_params: str = "", body: str = "") -> dict[str, str]:
        """
        digest = SHA256(nonce + timestamp + api-key + queryParams + body)
        sign = SHA256(digest + secretKey)
        """
        nonce = uuid.uuid4().hex
        timestamp = str(int(time.time() * 1000))
        digest_input = nonce + timestamp + self.__api_key + query_params + body
        digest = hashlib.sha256(digest_input.encode("utf-8")).hexdigest()
        sign = hashlib.sha256((digest + self.__secret_key).encode("utf-8")).hexdigest()
        return {
            "api-key": self.__api_key,
            "sign": sign,
            "nonce": nonce,
            "timestamp": timestamp,
        }

    def _handle_response(self, response: requests.Response) -> Any:
        if response.status_code != 200:
            raise BitUnixAPIError(f"HTTP {response.status_code}: {response.text}")
        data = response.json()
        if data.get("code") != 0:
            error = ErrorCode.get_by_code(data.get("code"))
            raise BitUnixAPIError(
                f"{error or data.get('code')}: {data.get('msg')}", data.get("code")
            )
        return data.get("data")

    def _get(self, path: str, params: dict | None = None) -> Any:
        # query params are signed sorted by key, as key+value
        params = sorted((k, str(v)) for k, v in (params or {}).items() if v is not None) 
        headers = self._sign_auth("".join(k + v for k, v in params))
        response = self.session.get(
            self.base_url + path, params=params, headers=headers, timeout=self.timeout
        )
        return self._handle_response(response)

    def _post(self, path: str, data: dict) -> Any:
        # the signed body has to be exactly the sent one, without spaces
        body = json.dumps(
            {k: v for k, v in data.items() if v is not None}, separators=(",", ":")
        )
        response = self.session.post(
            self.base_url + path,
            data=body,
            headers=self._sign_auth(body=body),
            timeout=self.timeout,
        )
        return self._handle_response(response)

    # market

    def get_trading_pairs(self, symbols: str | None = None) -> list[dict]:
        """basePrecision (qty decimals), quotePrecision (price decimals), minTradeVolume"""
        return self._get("/api/v1/futures/market/trading_pairs", {"symbols": symbols})

    def get_tickers(self, symbols: str | None = None) -> list[dict]:
        return self._get("/api/v1/futures/market/tickers", {"symbols": symbols})

    def get_depth(self, symbol: str, limit: int = 1) -> dict:
        """asks and bids as [price, amount], best first"""
        return self._get(
            "/api/v1/futures/market/depth", {"symbol": symbol, "limit": limit}
        )

    def get_kline(
        self,
        symbol: str,
        interval: str,
        limit: int = 100,
        end_time: int | None = None,
        type: str = "LAST_PRICE",
    ) -> list[dict]:
        """
        closed candles only, newest first, 200 at most
        end_time (ms) is exclusive and must be a candle open time, otherwise a candle is skipped
        """
        return self._get(
            "/api/v1/futures/market/kline",
            {
                "symbol": symbol,
                "interval": interval,
                "limit": limit,
                "endTime": end_time,
                "type": type,
            },
        )

    # account

    def get_account(self, margin_coin: str = "USDT") -> Any:
        return self._get("/api/v1/futures/account", {"marginCoin": margin_coin})

    def change_leverage(
        self, symbol: str, leverage: int, margin_coin: str = "USDT"
    ) -> Any:
        return self._post(
            "/api/v1/futures/account/change_leverage",
            {"symbol": symbol, "leverage": leverage, "marginCoin": margin_coin},
        )

    # trade

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        qty: str,
        trade_side: str = "OPEN",
        price: str | None = None,
        position_id: str | None = None,
        effect: str | None = None,
        client_id: str | None = None,
    ) -> dict:
        """
        side: BUY for long, SELL for short. Closing uses the side of the position too,
        with trade_side CLOSE and its position_id (hedge mode)
        """
        return self._post(
            "/api/v1/futures/trade/place_order",
            {
                "symbol": symbol,
                "side": side,
                "orderType": order_type,
                "qty": qty,
                "tradeSide": trade_side,
                "price": price,
                "positionId": position_id,
                "effect": effect,
                "clientId": client_id,
            },
        )

    def get_history_orders(self, symbol: str | None = None) -> Any:
        return self._get("/api/v1/futures/trade/get_history_orders", {"symbol": symbol})

    # position

    def get_pending_positions(
        self, symbol: str | None = None, position_id: str | None = None
    ) -> list[dict]:
        """positionId, qty, side (LONG/SHORT), avgOpenPrice, realizedPNL, fee, funding"""
        return self._get(
            "/api/v1/futures/position/get_pending_positions",
            {"symbol": symbol, "positionId": position_id},
        )

    def get_history_positions(
        self, symbol: str | None = None, position_id: str | None = None
    ) -> list[dict]:
        """closed positions: entryPrice, closePrice, realizedPNL, fee, funding"""
        data = self._get(
            "/api/v1/futures/position/get_history_positions",
            {"symbol": symbol, "positionId": position_id},
        )
        return data.get("positionList", []) if isinstance(data, dict) else data

    # tp/sl

    def place_tp_sl_order(
        self,
        symbol: str,
        position_id: str,
        tp_price: str | None = None,
        tp_qty: str | None = None,
        sl_price: str | None = None,
        sl_qty: str | None = None,
        stop_type: str = "MARK_PRICE",
    ) -> dict:
        """a tp/sl for a part of the position, it closes at market when triggered"""
        return self._post(
            "/api/v1/futures/tpsl/place_order",
            {
                "symbol": symbol,
                "positionId": position_id,
                "tpPrice": tp_price,
                "tpQty": tp_qty,
                "tpStopType": stop_type if tp_price else None,
                "tpOrderType": "MARKET" if tp_price else None,
                "slPrice": sl_price,
                "slQty": sl_qty,
                "slStopType": stop_type if sl_price else None,
                "slOrderType": "MARKET" if sl_price else None,
            },
        )

    def modify_tp_sl_order(
        self,
        order_id: str,
        tp_price: str | None = None,
        tp_qty: str | None = None,
        stop_type: str = "MARK_PRICE",
    ) -> dict:
        return self._post(
            "/api/v1/futures/tpsl/modify_order",
            {
                "orderId": order_id,
                "tpPrice": tp_price,
                "tpQty": tp_qty,
                "tpStopType": stop_type,
                "tpOrderType": "MARKET",
            },
        )

    def place_position_tp_sl_order(
        self,
        symbol: str,
        position_id: str,
        sl_price: str,
        stop_type: str = "MARK_PRICE",
    ) -> dict:
        """one per position, it closes whatever is left of the position"""
        return self._post(
            "/api/v1/futures/tpsl/position/place_order",
            {
                "symbol": symbol,
                "positionId": position_id,
                "slPrice": sl_price,
                "slStopType": stop_type,
            },
        )

    def modify_position_tp_sl_order(
        self,
        symbol: str,
        position_id: str,
        sl_price: str,
        stop_type: str = "MARK_PRICE",
    ) -> dict:
        return self._post(
            "/api/v1/futures/tpsl/position/modify_order",
            {
                "symbol": symbol,
                "positionId": position_id,
                "slPrice": sl_price,
                "slStopType": stop_type,
            },
        )

    def get_pending_tp_sl_orders(
        self, symbol: str | None = None, position_id: str | None = None
    ) -> list[dict]:
        data = self._get(
            "/api/v1/futures/tpsl/get_pending_orders",
            {"symbol": symbol, "positionId": position_id, "limit": 100},
        )
        return data.get("orderList", []) if isinstance(data, dict) else data

    def get_history_tp_sl_orders(self, symbol: str | None = None) -> list[dict]:
        """status: FILLED when triggered, CANCELED / SYSTEM_CANCELED otherwise"""
        data = self._get(
            "/api/v1/futures/tpsl/get_history_orders", {"symbol": symbol, "limit": 100}
        )
        return data.get("orderList", []) if isinstance(data, dict) else data
