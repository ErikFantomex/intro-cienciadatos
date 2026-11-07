from datetime import date, datetime, time, timedelta, timezone
import math

import httpx

from app.config import settings


class MarketDataProviderError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


def _demo_market_chart(
    coin_id: str, start_date: date, end_date: date
) -> dict:
    """Return clearly marked deterministic data when the public API is unreachable."""
    bases = {"bitcoin": 68000, "btc": 68000, "ethereum": 3500, "eth": 3500,
             "solana": 160, "sol": 160, "dogecoin": 0.15, "doge": 0.15}
    base = bases.get(coin_id.lower(), 100.0)
    prices = []
    volumes = []
    current = start_date
    index = 0
    while current <= end_date:
        value = base * (1 + 0.04 * math.sin(index / 3) + 0.01 * index / 30)
        timestamp = int(datetime.combine(current, time.min, tzinfo=timezone.utc).timestamp() * 1000)
        prices.append([timestamp, round(value, 8)])
        volumes.append([timestamp, round(base * 1200 * (1 + abs(math.sin(index))), 2)])
        current += timedelta(days=1)
        index += 1
    return {"prices": prices, "market_caps": [], "total_volumes": volumes, "demo": True}


def fetch_market_chart(
    coin_id: str, currency: str, start_date: date, end_date: date
) -> dict:
    """Fetch daily candles from Binance's public API (no key required)."""
    quote_asset = {"usd": "USDT", "usdt": "USDT", "eur": "EUR"}.get(
        currency.lower()
    )
    if quote_asset is None:
        raise MarketDataProviderError(
            "La API pública admite únicamente usd, usdt o eur.", 400
        )

    start = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
    end = datetime.combine(end_date, time.max, tzinfo=timezone.utc)
    base_asset = {
        "bitcoin": "BTC",
        "ethereum": "ETH",
        "solana": "SOL",
        "dogecoin": "DOGE",
    }.get(coin_id.lower(), coin_id.upper())
    params = {
        "symbol": f"{base_asset}{quote_asset}",
        "interval": "1d",
        "startTime": int(start.timestamp() * 1000),
        "endTime": int(end.timestamp() * 1000),
        "limit": 1000,
    }

    try:
        with httpx.Client(timeout=httpx.Timeout(20.0, connect=5.0)) as client:
            response = client.get(
                "https://api.binance.com/api/v3/klines",
                params=params,
            )
        if response.status_code == 429:
            raise MarketDataProviderError("Binance limitó las consultas.", 429)
        if response.status_code >= 400:
            if response.status_code == 404:
                raise MarketDataProviderError("Binance no encontró la criptomoneda solicitada.", 404)
            if response.status_code == 400:
                raise MarketDataProviderError("Binance rechazó el símbolo o rango solicitado.", 400)
            raise MarketDataProviderError(
                f"Binance rechazó la consulta (HTTP {response.status_code}).",
                502,
            )
        payload = response.json()
        if not isinstance(payload, list):
            raise MarketDataProviderError("Binance devolvió una respuesta inválida.", 502)
        return {
            "prices": [[candle[0], float(candle[4])] for candle in payload if len(candle) >= 6],
            "market_caps": [],
            "total_volumes": [[candle[0], float(candle[5])] for candle in payload if len(candle) >= 6],
        }
    except httpx.TimeoutException as error:
        raise MarketDataProviderError("La consulta a Binance agotó el tiempo de espera.", 502) from error
    except httpx.HTTPError:
        return _demo_market_chart(coin_id, start_date, end_date)
    except ValueError as error:
        raise MarketDataProviderError("Binance devolvió una respuesta JSON inválida.", 502) from error
