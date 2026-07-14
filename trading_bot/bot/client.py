import hashlib
import hmac
import logging
import time
import urllib.parse
import requests
from bot.exceptions import APIError, NetworkError

logger = logging.getLogger(__name__)


class BinanceFuturesClient:

    def __init__(self, api_key: str, api_secret: str, base_url: str = "https://testnet.binancefuture.com"):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip("/")

    def _sign_request(self, query_string: str) -> str:
        return hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

    def _request(self, method: str, path: str, params: dict | None = None) -> dict:
        if params is None:
            params = {}

        params["timestamp"] = int(time.time() * 1000)
        query_params = {k: str(v) for k, v in params.items() if v is not None}
        query_string = urllib.parse.urlencode(query_params)
        signature = self._sign_request(query_string)
        signed_query_string = f"{query_string}&signature={signature}"

        url = f"{self.base_url}{path}"
        headers = {
            "X-MBX-APIKEY": self.api_key,
            "Content-Type": "application/x-www-form-urlencoded"
        }

        logger.info(f"API Request | Method: {method} | Endpoint: {path}")
        logger.debug(f"API Request Details | URL: {url} | Params: {query_params}")

        try:
            if method.upper() == "POST":
                response = requests.post(url, data=signed_query_string, headers=headers, timeout=15)
            elif method.upper() == "GET":
                response = requests.get(f"{url}?{signed_query_string}", headers=headers, timeout=15)
            elif method.upper() == "DELETE":
                response = requests.delete(f"{url}?{signed_query_string}", headers=headers, timeout=15)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            logger.info(f"API Response | Status Code: {response.status_code}")
            logger.debug(f"API Response Body: {response.text}")

        except requests.exceptions.Timeout as e:
            msg = f"Timeout connecting to Binance Futures API at {url}"
            logger.error(msg)
            raise NetworkError(msg) from e
        except requests.exceptions.RequestException as e:
            msg = f"Network exception when calling Binance Futures API: {e}"
            logger.error(msg)
            raise NetworkError(msg) from e

        try:
            response_json = response.json()
        except ValueError as e:
            msg = f"Invalid JSON received from server. Status: {response.status_code}, Body: {response.text}"
            logger.error(msg)
            raise APIError(-9999, msg, response.status_code) from e

        if response.status_code != 200 or "code" in response_json:
            code = response_json.get("code", -9999)
            message = response_json.get("msg", "Unknown error occurred on Binance server.")
            logger.error(f"Binance API reported error: code={code}, message='{message}'")
            raise APIError(code, message, response.status_code)

        return response_json

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float | None = None,
        stop_price: float | None = None,
    ) -> dict:
        api_type = order_type
        if order_type == "STOP_LIMIT":
            api_type = "STOP"

        params = {
            "symbol": symbol,
            "side": side,
            "type": api_type,
            "quantity": quantity,
        }

        if price is not None:
            params["price"] = price
        if stop_price is not None:
            params["stopPrice"] = stop_price

        if api_type in ("LIMIT", "STOP"):
            params["timeInForce"] = "GTC"

        return self._request("POST", "/fapi/v1/order", params)
