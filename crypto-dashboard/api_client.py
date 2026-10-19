import os
from typing import Any

import httpx


class ApiClientError(Exception):
    pass


class NestApiClient:
    def __init__(self) -> None:
        self.base_url = os.getenv("NEST_API_URL", "http://nest-api:3000").rstrip("/")
        self.timeout = httpx.Timeout(15.0, connect=5.0)

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        token: str | None = None,
    ) -> Any:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        try:
            response = httpx.request(
                method,
                f"{self.base_url}{path}",
                params=params,
                json=json,
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as error:
            messages = {
                400: "La solicitud enviada no es válida.",
                401: "Inicia sesión para actualizar los datos.",
                403: "Tu usuario no tiene permiso para actualizar los datos.",
                404: "No se encontró la información solicitada.",
                429: "CoinGecko limitó las consultas; espera antes de reintentar.",
                502: "El proveedor devolvió una respuesta inválida.",
                503: "Un servicio financiero no está disponible.",
            }
            message = messages.get(
                error.response.status_code,
                "El servicio no pudo completar la solicitud.",
            )
            raise ApiClientError(message) from error
        except httpx.TimeoutException as error:
            raise ApiClientError("La conexión con NestJS agotó el tiempo de espera.") from error
        except httpx.HTTPError as error:
            raise ApiClientError("No fue posible conectar con NestJS.") from error
        except ValueError as error:
            raise ApiClientError("NestJS devolvió una respuesta inválida.") from error

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/api/crypto/health")

    def coins(self) -> list[dict[str, Any]]:
        return self._request("GET", "/api/crypto/coins")

    def market_data(
        self,
        coin_ids: list[str],
        currency: str,
        start_date: str,
        end_date: str,
    ) -> list[dict[str, Any]]:
        return self._request(
            "GET",
            "/api/crypto/market-data",
            params={
                "coin_ids": ",".join(coin_ids),
                "currency": currency,
                "start_date": start_date,
                "end_date": end_date,
            },
        )

    def market_summary(
        self,
        coin_ids: list[str],
        currency: str,
        start_date: str,
        end_date: str,
    ) -> list[dict[str, Any]]:
        return self._request(
            "GET",
            "/api/crypto/market-summary",
            params={
                "coin_ids": ",".join(coin_ids),
                "currency": currency,
                "start_date": start_date,
                "end_date": end_date,
            },
        )

    def ingest(
        self,
        coin_ids: list[str],
        currency: str,
        start_date: str,
        end_date: str,
        token: str,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/api/crypto/ingest",
            json={
                "coin_ids": coin_ids,
                "currency": currency,
                "start_date": start_date,
                "end_date": end_date,
            },
            token=token,
        )

    def ingestion_runs(self, limit: int = 50) -> list[dict[str, Any]]:
        return self._request(
            "GET", "/api/crypto/ingestion-runs", params={"limit": limit}
        )

    def login(self, email: str, password: str) -> dict[str, Any]:
        return self._request(
            "POST",
            "/api/auth/login",
            json={"email": email, "password": password},
        )
