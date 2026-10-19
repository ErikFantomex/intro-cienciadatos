import logging
from datetime import date

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, status
from sqlalchemy import inspect, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.coingecko_client import CoinGeckoError
from app.database import engine, get_session
from app.ingestion_service import (
    Cryptocurrency,
    IngestionRun,
    MarketPrice,
    ingest_market_data,
)
from app.market_service import (
    get_market_rows,
    list_coins,
    market_data_response,
    market_summary_response,
    recent_ingestion_runs,
)
from app.schemas import (
    CryptocurrencyOut,
    IngestRequest,
    IngestionRunOut,
    MarketPriceOut,
    MarketSummaryOut,
)
from app.security import require_internal_key

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI(title="CryptoInsight Data API", version="1.0.0")
router = APIRouter(prefix="/api", dependencies=[Depends(require_internal_key)])

REQUIRED_TABLES = {"cryptocurrencies", "market_prices", "ingestion_runs"}


@app.get("/health", tags=["Health"])
def health() -> dict:
    try:
        tables = set(inspect(engine).get_table_names())
        if not REQUIRED_TABLES.issubset(tables):
            missing = sorted(REQUIRED_TABLES - tables)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Faltan tablas requeridas en MySQL: {', '.join(missing)}.",
            )
        with engine.connect() as connection:
            connection.execute(select(1))
        return {"status": "healthy", "mysql": "connected", "tables": "ready"}
    except HTTPException:
        raise
    except SQLAlchemyError as error:
        logger.exception("Healthcheck de MySQL falló")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MySQL no está disponible.",
        ) from error


@router.get("/coins", response_model=list[CryptocurrencyOut])
def coins(session: Session = Depends(get_session)) -> list[Cryptocurrency]:
    return list_coins(session)


@router.get("/market-data", response_model=list[MarketPriceOut])
def market_data(
    coin_ids: str | None = Query(default=None),
    currency: str = Query(default="usd", min_length=2, max_length=10),
    start_date: date | None = None,
    end_date: date | None = None,
    session: Session = Depends(get_session),
) -> list[dict]:
    if start_date and end_date and end_date < start_date:
        raise HTTPException(status_code=400, detail="El rango de fechas no es válido.")
    ids = [coin_id.strip().lower() for coin_id in coin_ids.split(",") if coin_id.strip()] if coin_ids else None
    rows = get_market_rows(session, ids, currency, start_date, end_date)
    return market_data_response(rows)


@router.get("/market-summary", response_model=list[MarketSummaryOut])
def market_summary(
    coin_ids: str | None = Query(default=None),
    currency: str = Query(default="usd", min_length=2, max_length=10),
    start_date: date | None = None,
    end_date: date | None = None,
    session: Session = Depends(get_session),
) -> list[dict]:
    if start_date and end_date and end_date < start_date:
        raise HTTPException(status_code=400, detail="El rango de fechas no es válido.")
    ids = [coin_id.strip().lower() for coin_id in coin_ids.split(",") if coin_id.strip()] if coin_ids else None
    rows = get_market_rows(session, ids, currency, start_date, end_date)
    return market_summary_response(rows)


@router.post("/ingest", status_code=status.HTTP_200_OK)
def ingest(
    request: IngestRequest,
    session: Session = Depends(get_session),
) -> dict:
    try:
        return ingest_market_data(session, request)
    except CoinGeckoError as error:
        raise HTTPException(status_code=error.status_code, detail=str(error)) from error
    except SQLAlchemyError as error:
        session.rollback()
        logger.exception("Error de MySQL durante la ingestión")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No fue posible almacenar los datos en MySQL.",
        ) from error


@router.get("/ingestion-runs", response_model=list[IngestionRunOut])
def ingestion_runs(
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_session),
) -> list[IngestionRun]:
    return recent_ingestion_runs(session, limit)


app.include_router(router)
