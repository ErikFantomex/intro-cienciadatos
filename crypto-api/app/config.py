import os
from dataclasses import dataclass

from pathlib import Path


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{Path(__file__).resolve().parents[2] / 'cryptoinsight.db'}",
    )
    internal_api_key: str = os.getenv("INTERNAL_API_KEY", "")
    default_coins: tuple[str, ...] = tuple(
        coin.strip()
        for coin in os.getenv("DEFAULT_COINS", "bitcoin,ethereum,solana").split(",")
        if coin.strip()
    )
    default_currency: str = os.getenv("DEFAULT_CURRENCY", "usd").lower()

settings = Settings()
