import os
import time
import random
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from bot.config import Config
from bot.exceptions import (
    APIError,
    AuthenticationError,
    NetworkError,
    ValidationError,
)
from bot.logging_config import setup_logging
from bot.validators import validate_order_inputs
from bot.client import BinanceFuturesClient
from bot.orders import place_market_order, place_limit_order, place_stop_limit_order

setup_logging()

app = FastAPI(
    title="Binance USDT-M Futures Trading Bot API",
    description="Web API for placing orders on Binance Futures Testnet",
    version="1.0.0"
)

session_config = {
    "api_key": None,
    "api_secret": None
}

PROJECT_ROOT = Path(__file__).resolve().parent
LOGS_FILE = PROJECT_ROOT / "logs" / "trading.log"


class OrderRequest(BaseModel):
    symbol: str
    side: str
    type: str
    quantity: str
    price: str | None = None
    stop_price: str | None = None
    mock: bool = False


class ConfigUpdateRequest(BaseModel):
    api_key: str
    api_secret: str


@app.get("/api/config")
def get_config():
    env_config = Config()
    
    has_env_key = env_config.api_key is not None and env_config.api_key.strip() not in ("", "your_testnet_api_key_here")
    has_session_key = session_config["api_key"] is not None and session_config["api_key"].strip() != ""
    
    has_env_secret = env_config.api_secret is not None and env_config.api_secret.strip() not in ("", "your_testnet_api_secret_here")
    has_session_secret = session_config["api_secret"] is not None and session_config["api_secret"].strip() != ""

    return {
        "configured": (has_env_key or has_session_key) and (has_env_secret or has_session_secret),
        "source": "Session Override" if has_session_key else ("Environment (.env)" if has_env_key else "None"),
        "base_url": env_config.base_url
    }


@app.post("/api/config")
def update_config(req: ConfigUpdateRequest):
    if not req.api_key.strip() or not req.api_secret.strip():
        raise HTTPException(status_code=400, detail="Keys cannot be empty.")
    
    session_config["api_key"] = req.api_key.strip()
    session_config["api_secret"] = req.api_secret.strip()
    
    return {"status": "success", "message": "API keys loaded into session storage successfully."}


@app.post("/api/order")
def create_order(req: OrderRequest):
    try:
        validated = validate_order_inputs(
            symbol=req.symbol,
            side=req.side,
            order_type=req.type,
            quantity_str=req.quantity,
            price_str=req.price,
            stop_price_str=req.stop_price
        )
    except ValidationError as e:
        return {"success": False, "error_type": "ValidationError", "message": str(e)}

    if req.mock:
        avg_price = validated["price"] if validated["price"] is not None else 64230.50
        status = "NEW" if validated["type"] in ("LIMIT", "STOP_LIMIT") else "FILLED"
        executed_qty = 0.0 if validated["type"] in ("LIMIT", "STOP_LIMIT") else validated["quantity"]
        
        response = {
            "orderId": random.randint(10000000, 99999999),
            "symbol": validated["symbol"],
            "status": status,
            "executedQty": str(executed_qty),
            "avgPrice": str(avg_price),
            "updateTime": int(time.time() * 1000)
        }
        return {"success": True, "data": response}

    try:
        env_config = Config()
        api_key = session_config["api_key"] or env_config.api_key
        api_secret = session_config["api_secret"] or env_config.api_secret
        base_url = env_config.base_url

        if not api_key or api_key.strip() in ("", "your_testnet_api_key_here"):
            raise AuthenticationError("API Key is missing. Please configure it in Settings or the .env file.")
        if not api_secret or api_secret.strip() in ("", "your_testnet_api_secret_here"):
            raise AuthenticationError("API Secret is missing. Please configure it in Settings or the .env file.")

        client = BinanceFuturesClient(api_key=api_key, api_secret=api_secret, base_url=base_url)
        t = validated["type"]
        
        if t == "MARKET":
            res = place_market_order(
                client=client,
                symbol=validated["symbol"],
                side=validated["side"],
                quantity=validated["quantity"]
            )
        elif t == "LIMIT":
            res = place_limit_order(
                client=client,
                symbol=validated["symbol"],
                side=validated["side"],
                quantity=validated["quantity"],
                price=validated["price"]
            )
        elif t == "STOP_LIMIT":
            res = place_stop_limit_order(
                client=client,
                symbol=validated["symbol"],
                side=validated["side"],
                quantity=validated["quantity"],
                price=validated["price"],
                stop_price=validated["stop_price"]
            )
        else:
            raise ValidationError(f"Unsupported order type: {t}")

        return {"success": True, "data": res}

    except AuthenticationError as e:
        return {"success": False, "error_type": "AuthenticationError", "message": str(e)}
    except APIError as e:
        return {"success": False, "error_type": "APIError", "code": e.code, "message": e.message}
    except NetworkError as e:
        return {"success": False, "error_type": "NetworkError", "message": str(e)}
    except Exception as e:
        return {"success": False, "error_type": "SystemError", "message": f"System error: {str(e)}"}


@app.get("/api/logs")
def get_logs():
    if not LOGS_FILE.exists():
        return {"logs": ["No logs recorded yet."]}
    
    try:
        with open(LOGS_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
            last_lines = [line.strip() for line in lines[-30:]]
            return {"logs": last_lines}
    except Exception as e:
        return {"logs": [f"Error reading log file: {e}"]}


static_path = PROJECT_ROOT / "static"
if static_path.exists():
    app.mount("/", StaticFiles(directory=str(static_path), html=True), name="static")


@app.get("/")
def get_index():
    return FileResponse(str(PROJECT_ROOT / "static" / "index.html"))
