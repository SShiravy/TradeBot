from typing import Dict, Optional, Any, List
from BitUnix.error_codes import ErrorCode
import requests
import hashlib
import logging
import json
import time
import uuid


logger = logging.getLogger("BitUnixAPI")


class BitUnixAPI:
    base_url = "https://fapi.bitunix.com"

    def __init__(self, api_key: str, secret_key: str) -> None:
        self.__api_key = api_key
        self.__secret_key = secret_key
        self.session = requests.Session()
        # Set common request headers
        self.session.headers.update(
            {"language": "en-US", "Content-Type": "application/json"}
        )

    def _sign_auth(self, query_params: str = "", body: str = "") -> Dict[str, str]:
        """
        Generate signature according to Bitunix OpenAPI doc
        Args:
            api_key: API key
            secret_key: Secret key
            query_params: Sorted query string (no spaces)
            body: Raw JSON string (no spaces)
        Returns:
            str: Signature
        """
        # nonce: Random string
        nonce = str(uuid.uuid4()).replace("-", "")

        timestamp = str(int(time.time() * 1000))
        digest_input = nonce + timestamp + self.__api_key + query_params + body
        digest = hashlib.sha256(digest_input.encode("utf-8")).hexdigest()
        sign_input = digest + self.__secret_key
        sign = hashlib.sha256(sign_input.encode("utf-8")).hexdigest()

        return {
            "api-key": self.__api_key,
            "sign": sign,
            "nonce": nonce,
            "timestamp": timestamp,
        }

    @classmethod
    def _sort_params(cls, params: Dict[str, str]) -> str:
        """
        Sort parameters and concatenate them

        Args:
            params: Parameter dictionary

        Returns:
            str: Sorted parameter string
        """
        if not params:
            return ""
        # Sort by key and concatenate directly
        return "".join(f"{k}{v}" for k, v in sorted(params.items()))

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Handle response

        Args:
            response: Response object

        Returns:
            Dict[str, Any]: Response data

        Raises:
            Exception: When the response status code is not 200 or the business status code is not 0
        """
        if response.status_code != 200:
            raise Exception(f"HTTP Error: {response.json()=}")

        data = response.json()
        if data["code"] != 0:
            error = ErrorCode.get_by_code(data["code"])
            if error:
                raise Exception(str(error))
            raise Exception(f"Unknown Error: {response.json()=}")
        return data["data"]

    def get_tickers(self, symbols: Optional[str] = None) -> Dict[str, Any]:
        """
        Get futures trading pair market data

        Args:
            symbols: Futures trading pair, multiple separated by commas, e.g.: BTCUSDT,ETHUSDT

        Returns:
            Dict[str, Any]: Market data
        """
        url = f"{self.base_url}/api/v1/futures/market/tickers"
        params = {}
        if symbols:
            params["symbols"] = symbols

        query_string = self._sort_params(params)
        headers = self._sign_auth(query_string)

        response = self.session.get(url=url, params=params, headers=headers)
        return self._handle_response(response)

    def get_kline(
        self,
        symbol: str,
        interval: str,
        limit: int = 100,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        type: str = "LAST_PRICE",
    ) -> list[Dict[str, Any]]:
        """
        Get K-line data

        Args:
            symbol: Futures trading pair
            interval: K-line interval, e.g.: 1m, 5m, 15m, 30m, 1h, 4h, 1d
            limit: Number of data to get, default 100, maximum 200
            start_time: Start time (Unix timestamp, milliseconds format)
            end_time: End time (Unix timestamp, milliseconds format)
            type: K-line type, optional values: LAST_PRICE (latest price), MARK_PRICE (mark price), default: LAST_PRICE

        Returns:
            Dict[str, Any]: K-line data
        """
        url = f"{self.base_url}/api/v1/futures/market/kline"
        params = {"symbol": symbol, "interval": interval, "limit": limit, "type": type}

        if start_time is not None:
            params["startTime"] = start_time
        if end_time is not None:
            params["endTime"] = end_time

        query_string = self._sort_params(params)
        headers = self._sign_auth(query_string)
        response = self.session.get(url, params=params, headers=headers)
        return self._handle_response(response)  # type: ignore

    def get_account(self, margin_coin: str = "USDT") -> Dict[str, Any]:
        """
        Get account information

        Args:
            margin_coin: Margin currency, default USDT

        Returns:
            Dict[str, Any]: Account information
        """
        url = f"{self.base_url}/api/v1/futures/account"
        params = {"marginCoin": margin_coin}

        query_string = self._sort_params(params)
        headers = self._sign_auth(query_string)
        response = self.session.get(url, params=params, headers=headers)
        return self._handle_response(response)

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        qty: str,
        price: Optional[str] = None,
        position_id: Optional[str] = None,
        trade_side: str = "OPEN",
        effect: str = "GTC",
        reduce_only: bool = False,
        client_id: Optional[str] = None,
        tp_price: Optional[str] = None,
        tp_stop_type: Optional[str] = None,
        tp_order_type: Optional[str] = None,
        tp_order_price: Optional[str] = None,
        sl_price: Optional[str] = None,
        sl_stop_type: Optional[str] = None,
        sl_order_type: Optional[str] = None,
        sl_order_price: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Place order
        Args:
            symbol: Trading pair
            side: Direction, BUY or SELL
            order_type: Order type, LIMIT or MARKET
            qty: Quantity
            price: Price, required when order_type is LIMIT
            position_id: Position ID
            trade_side: Trading direction, OPEN (open position) or CLOSE (close position), default OPEN
            effect: Order validity period, default GTC
            reduce_only: Whether to reduce position only
            client_id: Client order ID
            tp_price: Take profit price
            tp_stop_type: Take profit trigger type, MARK (mark price) or LAST (last price)
            tp_order_type: Take profit order type, LIMIT or MARKET
            tp_order_price: Take profit order price
            same for sl...

        Returns:
            Dict[str, Any]: Order information
        """
        url = f"{self.base_url}/api/v1/futures/trade/place_order"

        data = {
            "symbol": symbol,
            "side": side,
            "orderType": order_type,
            "qty": qty,
            "tradeSide": trade_side,
            "effect": effect,
            "reduceOnly": reduce_only,
        }

        if price is not None:
            data["price"] = price
        if position_id is not None:
            data["positionId"] = position_id
        if client_id is not None:
            data["clientId"] = client_id
        if tp_price is not None:
            data["tpPrice"] = tp_price
        if tp_stop_type is not None:
            data["tpStopType"] = tp_stop_type
        if tp_order_type is not None:
            data["tpOrderType"] = tp_order_type
        if tp_order_price is not None:
            data["tpOrderPrice"] = tp_order_price
        if sl_price is not None:
            data["slPrice"] = sl_price
        if sl_stop_type is not None:
            data["slStopType"] = sl_stop_type
        if sl_order_type is not None:
            data["slOrderType"] = sl_order_type
        if sl_order_price is not None:
            data["slOrderPrice"] = sl_order_price

        body = json.dumps(data)
        headers = self._sign_auth(body=body)

        response = self.session.post(url, json=data, headers=headers)
        return self._handle_response(response)

    def cancel_orders(
        self, symbol: str, order_list: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Cancel multiple orders

        Args:
            symbol: Trading pair
            order_list: List of orders, each containing orderId or clientId

        Returns:
            Dict[str, Any]: Cancellation result
        """
        url = f"{self.base_url}/api/v1/futures/trade/cancel_orders"

        data = {"symbol": symbol, "orderList": order_list}

        body = json.dumps(data)
        headers = self._sign_auth(body=body)

        response = self.session.post(url, json=data, headers=headers)
        return self._handle_response(response)

    def change_leverage(
        self, symbol: str, leverage: int, margin_coin: str = "USDT"
    ) -> Dict[str, Any]:
        """
        change leverage
            Dict[str, Any]: change leverage result
        """

        url = f"{self.base_url}/api/v1/futures/account/change_leverage"

        data = {"symbol": symbol, "leverage": leverage, "marginCoin": margin_coin}

        body = json.dumps(data)
        headers = self._sign_auth(body=body)

        response = self.session.post(url, json=data, headers=headers)
        return self._handle_response(response)

    def get_pending_positions(
        self,
        symbol: str,
    ) -> Dict[str, Any]:
        """
        get pending positions
            Dict[str, Any]: change leverage result
        """

        url = f"{self.base_url}/api/v1/futures/position/get_pending_positions"

        data = {"symbol": symbol}

        body = json.dumps(data)
        headers = self._sign_auth(body=body)

        response = self.session.get(url, json=data, headers=headers)
        return self._handle_response(response)

    def place_tp_sl_order(
        self,
        symbol: str,
        position_id: str,
        tp_qty: Optional[str] = None,
        sl_qty: Optional[str] = None,
        tp_price: Optional[str] = None,
        tp_stop_type: Optional[str] = None,
        tp_order_type: Optional[str] = None,
        tp_order_price: Optional[str] = None,
        sl_price: Optional[str] = None,
        sl_stop_type: Optional[str] = None,
        sl_order_type: Optional[str] = None,
        sl_order_price: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Place tp_sl
        Args:
            symbol: Trading pair
            position_id: Position ID
            tp_qty: Quantity
            sl_qty: Quantity
            tp_price: Take profit price
            tp_stop_type: Take profit trigger type, MARK (mark price) or LAST (last price)
            tp_order_type: Take profit order type, LIMIT or MARKET
            tp_order_price: Take profit order
            same for sl ...

        Returns:
            Dict[str, Any]: Order information
        """
        url = f"{self.base_url}/api/v1/futures/tpsl/place_order"

        data = {
            "symbol": symbol,
            "positionId": symbol,
        }
        if tp_qty is not None:
            data["tpQty"] = tp_qty
        if sl_qty is not None:
            data["slQty"] = sl_qty
        if position_id is not None:
            data["positionId"] = position_id
        if tp_price is not None:
            data["tpPrice"] = tp_price
        if tp_stop_type is not None:
            data["tpStopType"] = tp_stop_type
        if tp_order_type is not None:
            data["tpOrderType"] = tp_order_type
        if tp_order_price is not None:
            data["tpOrderPrice"] = tp_order_price
        if sl_price is not None:
            data["slPrice"] = sl_price
        if sl_stop_type is not None:
            data["slStopType"] = sl_stop_type
        if sl_order_type is not None:
            data["slOrderType"] = sl_order_type
        if sl_order_price is not None:
            data["slOrderPrice"] = sl_order_price

        body = json.dumps(data)
        headers = self._sign_auth(body=body)

        response = self.session.post(url, json=data, headers=headers)
        return self._handle_response(response)

    def change_position_tp_sl_order(
        self,
        symbol: str,
        position_id: str,
        tp_price: Optional[str] = None,
        tp_stop_type: Optional[str] = None,
        sl_price: Optional[str] = None,
        sl_stop_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Change Position main sl tp (whole positions volume)
        Args:
            symbol: Trading pair
            position_id: Position ID
            tp_price: Take profit price
            tp_stop_type: Take profit trigger type, MARK (mark price) or LAST (last price)
            same for sl ...

        Returns:
            Dict[str, Any]: Order information
        """
        url = f"{self.base_url}/api/v1/futures/tpsl/position/modify_order"

        data = {
            "symbol": symbol,
            "positionId": symbol,
        }

        if position_id is not None:
            data["positionId"] = position_id
        if tp_price is not None:
            data["tpPrice"] = tp_price
        if tp_stop_type is not None:
            data["tpStopType"] = tp_stop_type
        if sl_price is not None:
            data["slPrice"] = sl_price
        if sl_stop_type is not None:
            data["slStopType"] = sl_stop_type

        body = json.dumps(data)
        headers = self._sign_auth(body=body)

        response = self.session.post(url, json=data, headers=headers)
        return self._handle_response(response)

    def get_history_orders(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Get historical orders

        Args:
            symbol: Trading pair, if not provided, get orders for all trading pairs

        Returns:
            Dict[str, Any]: Historical order list
        """
        url = f"{self.base_url}/api/v1/futures/trade/get_history_orders"
        params = {}
        if symbol:
            params["symbol"] = symbol

        query_string = self._sort_params(params)
        headers = self._sign_auth(query_string)

        response = self.session.get(url, params=params, headers=headers)
        return self._handle_response(response)

    def get_history_positions(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Get historical position information

        Args:
            symbol: Trading pair, if not provided, get all positions

        Returns:
            Dict[str, Any]: Historical position information
        """
        url = f"{self.base_url}/api/v1/futures/position/get_history_positions"
        params = {}
        if symbol:
            params["symbol"] = symbol

        query_string = self._sort_params(params)
        headers = self._sign_auth(query_string)

        response = self.session.get(url, params=params, headers=headers)
        return self._handle_response(response)
