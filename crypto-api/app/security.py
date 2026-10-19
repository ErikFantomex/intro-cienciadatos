import hmac
import secrets

from fastapi import Header, HTTPException, status

from app.config import settings


def require_internal_key(
    provided_key: str | None = Header(default=None, alias="X-Internal-API-Key"),
) -> None:
    expected_key = settings.internal_api_key
    if not expected_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="La autenticación interna no está configurada.",
        )
    if provided_key is None or not hmac.compare_digest(
        secrets.token_bytes(0).hex() + provided_key, expected_key
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credencial interna inválida.",
        )
