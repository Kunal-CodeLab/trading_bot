import re
from bot.exceptions import ValidationError


def validate_symbol(symbol: str) -> str:
    if not symbol or not isinstance(symbol, str):
        raise ValidationError("Symbol is required and must be a string.")
        
    normalized = symbol.strip().upper()
    if not re.match(r"^[A-Z0-9]{3,}USDT$", normalized):
        raise ValidationError(
            f"Invalid symbol: '{symbol}'. Must be an uppercase alphanumeric string "
            f"ending with 'USDT' (e.g., 'BTCUSDT')."
        )
    return normalized


def validate_side(side: str) -> str:
    if not side or not isinstance(side, str):
        raise ValidationError("Side is required and must be a string.")
        
    normalized = side.strip().upper()
    if normalized not in ("BUY", "SELL"):
        raise ValidationError(f"Invalid side: '{side}'. Must be either 'BUY' or 'SELL'.")
    return normalized


def validate_type(order_type: str) -> str:
    if not order_type or not isinstance(order_type, str):
        raise ValidationError("Order type is required and must be a string.")
        
    normalized = order_type.strip().upper()
    if normalized not in ("MARKET", "LIMIT", "STOP_LIMIT"):
        raise ValidationError(
            f"Invalid order type: '{order_type}'. Must be 'MARKET', 'LIMIT', or 'STOP_LIMIT'."
        )
    return normalized


def validate_quantity(quantity_str: str) -> float:
    if not quantity_str:
        raise ValidationError("Quantity is required.")
        
    try:
        quantity = float(quantity_str)
    except (ValueError, TypeError):
        raise ValidationError(f"Quantity must be a valid number, received: '{quantity_str}'.")
        
    if quantity <= 0:
        raise ValidationError(f"Quantity must be greater than zero, received: {quantity}.")
        
    return quantity


def validate_price(price_str: str | None, name: str = "Price") -> float:
    if not price_str:
        raise ValidationError(f"{name} is required for this order type.")
        
    try:
        price = float(price_str)
    except (ValueError, TypeError):
        raise ValidationError(f"{name} must be a valid number, received: '{price_str}'.")
        
    if price <= 0:
        raise ValidationError(f"{name} must be greater than zero, received: {price}.")
        
    return price


def validate_order_inputs(
    symbol: str,
    side: str,
    order_type: str,
    quantity_str: str,
    price_str: str | None = None,
    stop_price_str: str | None = None,
) -> dict:
    validated = {}
    
    validated["symbol"] = validate_symbol(symbol)
    validated["side"] = validate_side(side)
    validated["type"] = validate_type(order_type)
    validated["quantity"] = validate_quantity(quantity_str)
    
    t = validated["type"]
    
    if t == "LIMIT":
        validated["price"] = validate_price(price_str, "Price")
        if stop_price_str is not None:
            raise ValidationError("Stop price should not be provided for LIMIT orders.")
        validated["stop_price"] = None
        
    elif t == "STOP_LIMIT":
        validated["price"] = validate_price(price_str, "Price")
        validated["stop_price"] = validate_price(stop_price_str, "Stop Price")
        
    elif t == "MARKET":
        if price_str is not None:
            raise ValidationError("Price should not be provided for MARKET orders.")
        if stop_price_str is not None:
            raise ValidationError("Stop price should not be provided for MARKET orders.")
        validated["price"] = None
        validated["stop_price"] = None
        
    return validated
