import os
from dataclasses import dataclass

from sqlalchemy import URL


@dataclass(frozen=True)
class Settings:
    database_host: str = os.getenv("CRYPTO_DB_HOST", "mysql")
    database_port: int = int(os.getenv("CRYPTO_DB_PORT", "3306"))
    database_name: str = os.getenv("CRYPTO_DB_NAME", "crypto_db")
    database_user: str = os.getenv("CRYPTO_DB_USER", "crypto_user")
    database_password: str = os.getenv("CRYPTO_DB_PASSWORD", "")
    coingecko_api_key: str = os.getenv("COINGECKO_API_KEY", "")
    coingecko_base_url: str = os.getenv(
        "COINGECKO_BASE_URL", "https://api.coingecko.com/api/v3"
    ).rstrip("/")
    internal_api_key: str = os.getenv("INTERNAL_API_KEY", "")
    default_coins: tuple[str, ...] = tuple(
        coin.strip()
        for coin in os.getenv("DEFAULT_COINS", "bitcoin,ethereum,solana").split(",")
        if coin.strip()
    )
    default_currency: str = os.getenv("DEFAULT_CURRENCY", "usd").lower()

    @property
    def database_url(self) -> URL:
        return URL.create(
            "mysql+pymysql",
            username=self.database_user,
            password=self.database_password,
            host=self.database_host,
            port=self.database_port,
            database=self.database_name,
            query={"charset": "utf8mb4"},
        )


settings = Settings()
