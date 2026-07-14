import os
from pathlib import Path
from dotenv import load_dotenv
from bot.exceptions import AuthenticationError

PROJECT_ROOT = Path(__file__).resolve().parent.parent
env_path = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=env_path)


class Config:
    def __init__(self):
        self.api_key = os.getenv("BINANCE_API_KEY")
        self.api_secret = os.getenv("BINANCE_API_SECRET")
        self.base_url = os.getenv("BINANCE_BASE_URL", "https://testnet.binancefuture.com").rstrip("/")
        
    def validate(self) -> None:
        if not self.api_key or self.api_key.strip() in ("", "your_testnet_api_key_here"):
            raise AuthenticationError("BINANCE_API_KEY is not configured or is using the default placeholder.")
            
        if not self.api_secret or self.api_secret.strip() in ("", "your_testnet_api_secret_here"):
            raise AuthenticationError("BINANCE_API_SECRET is not configured or is using the default placeholder.")
