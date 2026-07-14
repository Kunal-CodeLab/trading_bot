from bot.client import BinanceFuturesClient


def place_market_order(
    client: BinanceFuturesClient,
    symbol: str,
    side: str,
    quantity: float
) -> dict:
    return client.place_order(
        symbol=symbol,
        side=side,
        order_type="MARKET",
        quantity=quantity
    )


def place_limit_order(
    client: BinanceFuturesClient,
    symbol: str,
    side: str,
    quantity: float,
    price: float
) -> dict:
    return client.place_order(
        symbol=symbol,
        side=side,
        order_type="LIMIT",
        quantity=quantity,
        price=price
    )


def place_stop_limit_order(
    client: BinanceFuturesClient,
    symbol: str,
    side: str,
    quantity: float,
    price: float,
    stop_price: float
) -> dict:
    return client.place_order(
        symbol=symbol,
        side=side,
        order_type="STOP_LIMIT",
        quantity=quantity,
        price=price,
        stop_price=stop_price
    )
