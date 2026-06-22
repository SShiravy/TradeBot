import hmac
import hashlib
import time
import requests
import json
import logging
from enum import Enum
from urllib.parse import urlparse, urlencode

import json
from typing import Dict, Optional, Any, List
import requests
from config import Config
from error_codes import ErrorCode
from open_api_http_sign import get_auth_headers, sort_params
import logging
import asyncio

logger = logging.getLogger("coinex_api")


class BitUnix(Enum):
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


class OpenApiHttpFuturePrivate:
    def __init__(self, config: Config):
        """
        Initialize OpenApiHttpFuturePrivate class

        Args:
            config: Configuration object containing api_key and secret_key
        """
        self.config = config
        self.api_key = config.api_key
        self.secret_key = config.secret_key
        self.base_url = config.uri_prefix
        self.session = requests.Session()

        # Set common request headers
        self.session.headers.update(
            {"language": "en-US", "Content-Type": "application/json"}
        )

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Handle response

        Args:
            response: Response object

        Returns:
            Dict[str, Any]: Response data

        Raises:
            Exception: When response status code is not 200 or business status code is not 0
        """
        if response.status_code != 200:
            raise Exception(f"HTTP Error: {response.status_code}")

        data = response.json()
        if data["code"] != 0:
            error = ErrorCode.get_by_code(data["code"])
            if error:
                raise Exception(str(error))
            raise Exception(f"Unknown Error: {data['code']} - {data['msg']}")

        return data["data"]

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

        query_string = sort_params(params)
        headers = get_auth_headers(self.api_key, self.secret_key, query_string)

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

        body = json.dumps(data)
        headers = get_auth_headers(self.api_key, self.secret_key, body=body)

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
        headers = get_auth_headers(self.api_key, self.secret_key, body=body)

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

        query_string = sort_params(params)
        headers = get_auth_headers(self.api_key, self.secret_key, query_string)

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

        query_string = sort_params(params)
        headers = get_auth_headers(self.api_key, self.secret_key, query_string)

        response = self.session.get(url, params=params, headers=headers)
        return self._handle_response(response)
