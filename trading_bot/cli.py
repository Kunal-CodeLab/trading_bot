import argparse
import datetime
import logging
import sys
import traceback

from bot.config import Config
from bot.exceptions import (
    APIError,
    AuthenticationError,
    NetworkError,
    TradingBotError,
    ValidationError,
)
from bot.logging_config import setup_logging
from bot.client import BinanceFuturesClient
from bot.orders import place_market_order, place_limit_order, place_stop_limit_order
from bot.validators import validate_order_inputs

logger = logging.getLogger("bot.cli")


def format_timestamp(ms_timestamp) -> str:
    if ms_timestamp is None:
        return "N/A"
    try:
        dt = datetime.datetime.fromtimestamp(int(ms_timestamp) / 1000.0, tz=datetime.timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        return str(ms_timestamp)


def print_summary(symbol: str, side: str, order_type: str, quantity: float, price: float | None = None, stop_price: float | None = None) -> None:
    print("\n-----------------------------------")
    print("Trading Bot")
    print("-----------------------------------")
    print(f"Symbol : {symbol}")
    print(f"Side : {side}")
    print(f"Type : {order_type}")
    print(f"Quantity : {quantity}")
    if price is not None:
        print(f"Price : {price}")
    if stop_price is not None:
        print(f"Stop Price : {stop_price}")
    print("-----------------------------------")


def main() -> None:
    setup_logging()
    logger.info("Trading Bot CLI started.")

    parser = argparse.ArgumentParser(
        description="Simplified USDT-M Futures Trading Bot CLI.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--symbol",
        type=str,
        required=True,
        help="Trading pair",
    )
    parser.add_argument(
        "--side",
        type=str,
        required=True,
        help="Trade side: BUY or SELL",
    )
    parser.add_argument(
        "--type",
        type=str,
        required=True,
        help="Order type: MARKET, LIMIT, or STOP_LIMIT",
    )
    parser.add_argument(
        "--quantity",
        type=str,
        required=True,
        help="Order quantity",
    )
    parser.add_argument(
        "--price",
        type=str,
        default=None,
        help="Limit price",
    )
    parser.add_argument(
        "--stop-price",
        type=str,
        default=None,
        help="Trigger stop price",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run in mock mode",
    )

    args = parser.parse_args()
    logger.debug(f"Parsed CLI arguments: {vars(args)}")

    try:
        validated = validate_order_inputs(
            symbol=args.symbol,
            side=args.side,
            order_type=args.type,
            quantity_str=args.quantity,
            price_str=args.price,
            stop_price_str=args.stop_price,
        )
        logger.info("CLI input parameters successfully validated.")
    except ValidationError as e:
        logger.error(f"Input Validation Failure: {e}")
        print("\n==========================")
        print("INPUT VALIDATION ERROR")
        print("==========================")
        print(f"Message: {e}")
        print("Use --help to view parameter rules.")
        sys.exit(1)

    print_summary(
        symbol=validated["symbol"],
        side=validated["side"],
        order_type=validated["type"],
        quantity=validated["quantity"],
        price=validated["price"],
        stop_price=validated["stop_price"],
    )

    try:
        if args.mock:
            import random
            import time
            logger.info("Running in MOCK mode. Generating mock response.")
            order_id = random.randint(10000000, 99999999)
            avg_price = validated["price"] if validated["price"] is not None else "64230.50"
            status = "NEW" if validated["type"] in ("LIMIT", "STOP_LIMIT") else "FILLED"
            executed_qty = "0.000" if validated["type"] in ("LIMIT", "STOP_LIMIT") else str(validated["quantity"])
            response = {
                "orderId": order_id,
                "symbol": validated["symbol"],
                "status": status,
                "executedQty": executed_qty,
                "avgPrice": str(avg_price),
                "updateTime": int(time.time() * 1000)
            }
        else:
            config = Config()
            config.validate()
            logger.info("Environment variables loaded and verified.")

            client = BinanceFuturesClient(
                api_key=config.api_key,
                api_secret=config.api_secret,
                base_url=config.base_url,
            )

            logger.info(
                f"Placing {validated['type']} order for {validated['symbol']} (Side: {validated['side']}, Qty: {validated['quantity']})"
            )
            
            t = validated["type"]
            if t == "MARKET":
                response = place_market_order(
                    client=client,
                    symbol=validated["symbol"],
                    side=validated["side"],
                    quantity=validated["quantity"],
                )
            elif t == "LIMIT":
                response = place_limit_order(
                    client=client,
                    symbol=validated["symbol"],
                    side=validated["side"],
                    quantity=validated["quantity"],
                    price=validated["price"],
                )
            elif t == "STOP_LIMIT":
                response = place_stop_limit_order(
                    client=client,
                    symbol=validated["symbol"],
                    side=validated["side"],
                    quantity=validated["quantity"],
                    price=validated["price"],
                    stop_price=validated["stop_price"],
                )
            else:
                raise ValidationError(f"Unsupported order type: {t}")

        logger.info(f"Order successfully placed. Order ID: {response.get('orderId')}")
        
        print("\n-----------------------------------")
        print("API Response")
        print("-----------------------------------")
        print(f"Order ID : {response.get('orderId')}")
        print(f"Status : {response.get('status')}")
        print(f"Executed Quantity : {response.get('executedQty')}")
        
        avg_price = response.get("avgPrice")
        if avg_price and float(avg_price) > 0:
            print(f"Average Price : {avg_price}")
        else:
            print("Average Price : N/A")
            
        print(f"Time : {format_timestamp(response.get('updateTime'))}")
        print("Success / Failure : Success")
        print("-----------------------------------")

    except APIError as e:
        logger.error(f"Binance API rejected order: {e}")
        print("\n-----------------------------------")
        print("API Response")
        print("-----------------------------------")
        print("Success / Failure : Failure")
        print(f"Error Code : {e.code}")
        print(f"Error Message : {e.message}")
        print("-----------------------------------")
        sys.exit(1)

    except NetworkError as e:
        logger.error(f"Network error during order submission: {e}")
        print("\n-----------------------------------")
        print("API Response")
        print("-----------------------------------")
        print("Success / Failure : Failure")
        print(f"Error Message : {e}")
        print("Please check your internet connection and verify if Binance services are active.")
        print("-----------------------------------")
        sys.exit(1)

    except TradingBotError as e:
        logger.error(f"General trading bot exception: {e}")
        print("\n-----------------------------------")
        print("API Response")
        print("-----------------------------------")
        print("Success / Failure : Failure")
        print(f"Error Message : {e}")
        print("-----------------------------------")
        sys.exit(1)

    except Exception as e:
        logger.critical(f"Unhandled system exception: {e}\n{traceback.format_exc()}")
        print("\n-----------------------------------")
        print("API Response")
        print("-----------------------------------")
        print("Success / Failure : Failure")
        print("Error Message : An unexpected system error occurred.")
        print(f"Details : {e}")
        print("-----------------------------------")
        sys.exit(1)


if __name__ == "__main__":
    main()
