import logging
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
    select,
)
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.coingecko_client import CoinGeckoError, fetch_market_chart
from app.database import Base
from app.schemas import IngestRequest

logger = logging.getLogger(__name__)


class Cryptocurrency(Base):
    __tablename__ = "cryptocurrencies"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    coin_id = Column(String(100), nullable=False, unique=True)
    symbol = Column(String(20))
    name = Column(String(100))
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())


class MarketPrice(Base):
    __tablename__ = "market_prices"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    cryptocurrency_id = Column(
        BigInteger, ForeignKey("cryptocurrencies.id"), nullable=False
    )
    observed_at = Column(DateTime, nullable=False)
    currency = Column(String(10), nullable=False, default="usd")
    price = Column(Numeric(30, 10), nullable=False)
    market_cap = Column(Numeric(36, 2))
    total_volume = Column(Numeric(36, 2))
    source = Column(String(50), nullable=False, default="CoinGecko")
    ingested_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    coin_id = Column(String(100), nullable=False)
    currency = Column(String(10), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    records_received = Column(Integer, nullable=False, default=0)
    records_stored = Column(Integer, nullable=False, default=0)
    status = Column(String(30), nullable=False)
    error_message = Column(Text)
    started_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())
    finished_at = Column(DateTime)


def _series_by_time(values: list[list[float]]) -> dict[int, float]:
    result: dict[int, float] = {}
    for item in values:
        if len(item) == 2 and item[0] is not None and item[1] is not None:
            result[int(item[0])] = float(item[1])
    return result


def _utc_datetime(timestamp_ms: int) -> datetime:
    return datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc).replace(tzinfo=None)


def _save_failure(
    session: Session, run_id: int, received: int, message: str
) -> None:
    session.rollback()
    run = session.get(IngestionRun, run_id)
    if run is not None:
        run.records_received = received
        run.records_stored = 0
        run.status = "failed"
        run.error_message = message
        run.finished_at = datetime.now(timezone.utc).replace(tzinfo=None)
        session.commit()


def ingest_market_data(session: Session, request: IngestRequest) -> dict:
    results = []
    failures = []

    for coin_id in request.coin_ids:
        received = 0
        run = IngestionRun(
            coin_id=coin_id,
            currency=request.currency,
            start_date=request.start_date,
            end_date=request.end_date,
            status="running",
        )
        session.add(run)
        session.commit()
        session.refresh(run)
        run_id = run.id

        try:
            payload = fetch_market_chart(
                coin_id, request.currency, request.start_date, request.end_date
            )
            prices = _series_by_time(payload.get("prices", []))
            received = len(prices)
            market_caps = _series_by_time(payload.get("market_caps", []))
            volumes = _series_by_time(payload.get("total_volumes", []))
            if not prices:
                raise CoinGeckoError(f"CoinGecko no devolvió precios para {coin_id}.")

            coin = session.scalar(
                select(Cryptocurrency).where(Cryptocurrency.coin_id == coin_id)
            )
            if coin is None:
                coin = Cryptocurrency(
                    coin_id=coin_id,
                    symbol=coin_id[:20],
                    name=coin_id.replace("-", " ").title()[:100],
                )
                session.add(coin)
                session.flush()

            rows = [
                {
                    "cryptocurrency_id": coin.id,
                    "observed_at": _utc_datetime(timestamp),
                    "currency": request.currency,
                    "price": Decimal(str(price)),
                    "market_cap": (
                        Decimal(str(market_caps[timestamp]))
                        if timestamp in market_caps
                        else None
                    ),
                    "total_volume": (
                        Decimal(str(volumes[timestamp])) if timestamp in volumes else None
                    ),
                    "source": "CoinGecko",
                }
                for timestamp, price in sorted(prices.items())
            ]

            statement = mysql_insert(MarketPrice).values(rows)
            statement = statement.on_duplicate_key_update(
                price=statement.inserted.price,
                market_cap=statement.inserted.market_cap,
                total_volume=statement.inserted.total_volume,
                source=statement.inserted.source,
                ingested_at=datetime.now(timezone.utc).replace(tzinfo=None),
            )
            session.execute(statement)
            run = session.get(IngestionRun, run_id)
            run.records_received = len(prices)
            run.records_stored = len(rows)
            run.status = "success"
            run.error_message = None
            run.finished_at = datetime.now(timezone.utc).replace(tzinfo=None)
            session.commit()
            results.append(
                {
                    "coin_id": coin_id,
                    "records_received": len(prices),
                    "records_stored": len(rows),
                    "status": "success",
                }
            )
        except CoinGeckoError as error:
            logger.warning("CoinGecko ingestion failed for %s: %s", coin_id, error)
            _save_failure(session, run_id, received, str(error))
            failures.append(error)
            results.append(
                {
                    "coin_id": coin_id,
                    "records_received": 0,
                    "records_stored": 0,
                    "status": "failed",
                    "message": str(error),
                }
            )
        except SQLAlchemyError:
            logger.exception("MySQL ingestion failure for %s", coin_id)
            _save_failure(session, run_id, received, "No fue posible guardar los datos en MySQL.")
            raise
        except Exception as error:
            logger.exception("Unexpected ingestion failure for %s", coin_id)
            _save_failure(session, run_id, received, "Error interno al procesar los datos.")
            failures.append(CoinGeckoError("Error interno al procesar los datos.", 500))
            results.append(
                {
                    "coin_id": coin_id,
                    "records_received": 0,
                    "records_stored": 0,
                    "status": "failed",
                    "message": "Error interno al procesar los datos.",
                }
            )

    if failures and len(failures) == len(request.coin_ids):
        code = 429 if any(error.status_code == 429 for error in failures) else failures[0].status_code
        raise CoinGeckoError("No se pudo completar ninguna ingestión.", code)

    return {
        "currency": request.currency,
        "start_date": request.start_date,
        "end_date": request.end_date,
        "results": results,
    }
