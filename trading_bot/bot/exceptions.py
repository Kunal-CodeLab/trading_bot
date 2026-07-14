class TradingBotError(Exception):
    pass


class ValidationError(TradingBotError):
    pass


class AuthenticationError(TradingBotError):
    pass


class APIError(TradingBotError):
    def __init__(self, code: int, message: str, status_code: int):
        super().__init__(f"Binance API Error (Status {status_code}): Code {code} - {message}")
        self.code = code
        self.message = message
        self.status_code = status_code


class NetworkError(TradingBotError):
    pass
