from datetime import date, datetime, time, timezone

import httpx

from app.config import settings


class CoinGeckoError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


def fetch_market_chart(
    coin_id: str, currency: str, start_date: date, end_date: date
) -> dict:
    if not settings.coingecko_api_key or settings.coingecko_api_key == "coloca_aqui_tu_clave":
        raise CoinGeckoError("Falta configurar la clave de CoinGecko.", 503)

    start = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
    end = datetime.combine(end_date, time.max, tzinfo=timezone.utc)
    params = {"vs_currency": currency, "from": int(start.timestamp()), "to": int(end.timestamp())}
    headers = {"x-cg-demo-api-key": settings.coingecko_api_key}

    try:
        with httpx.Client(timeout=httpx.Timeout(20.0, connect=5.0)) as client:
            response = client.get(
                f"{settings.coingecko_base_url}/coins/{coin_id}/market_chart/range",
                params=params,
                headers=headers,
            )
        if response.status_code == 429:
            raise CoinGeckoError("CoinGecko alcanzó su límite de solicitudes.", 429)
        if response.status_code >= 400:
            if response.status_code == 404:
                raise CoinGeckoError("CoinGecko no encontró la criptomoneda solicitada.", 404)
            if response.status_code == 400:
                raise CoinGeckoError("CoinGecko rechazó los parámetros de consulta.", 400)
            raise CoinGeckoError(
                f"CoinGecko rechazó la consulta (HTTP {response.status_code}).",
                502,
            )
        payload = response.json()
        if not isinstance(payload, dict) or not isinstance(payload.get("prices"), list):
            raise CoinGeckoError("CoinGecko devolvió una respuesta inválida.", 502)
        return payload
    except httpx.TimeoutException as error:
        raise CoinGeckoError("La consulta a CoinGecko agotó el tiempo de espera.", 502) from error
    except httpx.HTTPError as error:
        raise CoinGeckoError("No fue posible conectar con CoinGecko.", 502) from error
    except ValueError as error:
        raise CoinGeckoError("CoinGecko devolvió una respuesta JSON inválida.", 502) from error
