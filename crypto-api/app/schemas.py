from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.config import settings


class IngestRequest(BaseModel):
    coin_ids: list[str] = Field(min_length=1, max_length=20)
    currency: str = Field(default=settings.default_currency, min_length=2, max_length=10)
    start_date: date
    end_date: date

    @field_validator("coin_ids")
    @classmethod
    def validate_coin_ids(cls, coin_ids: list[str]) -> list[str]:
        import re

        normalized = [coin_id.strip().lower() for coin_id in coin_ids]
        if any(not re.fullmatch(r"[a-z0-9-]{1,100}", coin_id) for coin_id in normalized):
            raise ValueError("Los identificadores de criptomoneda no son válidos.")
        if len(set(normalized)) != len(normalized):
            raise ValueError("No se permiten identificadores duplicados.")
        return normalized

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, currency: str) -> str:
        normalized = currency.strip().lower()
        if not normalized.isalpha():
            raise ValueError("La moneda debe contener solo letras.")
        return normalized

    @model_validator(mode="after")
    def validate_date_range(self) -> "IngestRequest":
        if self.end_date < self.start_date:
            raise ValueError("La fecha final debe ser igual o posterior a la inicial.")
        return self


class CryptocurrencyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    coin_id: str
    symbol: str | None
    name: str | None
    active: bool
    created_at: datetime


class MarketPriceOut(BaseModel):
    coin_id: str
    symbol: str | None
    name: str | None
    observed_at: datetime
    currency: str
    price: Decimal
    market_cap: Decimal | None
    total_volume: Decimal | None
    source: str


class MarketSummaryOut(BaseModel):
    coin_id: str
    symbol: str | None
    name: str | None
    currency: str
    first_price: Decimal
    last_price: Decimal
    max_price: Decimal
    min_price: Decimal
    average_price: Decimal
    percentage_change: Decimal | None
    latest_market_cap: Decimal | None
    latest_total_volume: Decimal | None
    observations: int
    first_observed_at: datetime
    last_observed_at: datetime


class IngestionRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    coin_id: str
    currency: str
    start_date: date
    end_date: date
    records_received: int
    records_stored: int
    status: str
    error_message: str | None
    started_at: datetime
    finished_at: datetime | None
