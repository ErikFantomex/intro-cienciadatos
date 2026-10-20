from datetime import date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ingestion_service import Cryptocurrency, IngestionRun, MarketPrice


def list_coins(session: Session) -> list[Cryptocurrency]:
    return list(
        session.scalars(
            select(Cryptocurrency)
            .where(Cryptocurrency.active.is_(True))
            .order_by(Cryptocurrency.name)
        )
    )


def get_market_rows(
    session: Session,
    coin_ids: list[str] | None,
    currency: str,
    start_date: date | None,
    end_date: date | None,
) -> list[tuple[MarketPrice, Cryptocurrency]]:
    statement = (
        select(MarketPrice, Cryptocurrency)
        .join(Cryptocurrency, MarketPrice.cryptocurrency_id == Cryptocurrency.id)
        .where(MarketPrice.currency == currency.lower())
    )
    if coin_ids:
        statement = statement.where(Cryptocurrency.coin_id.in_(coin_ids))
    if start_date:
        statement = statement.where(
            MarketPrice.observed_at >= datetime.combine(start_date, time.min)
        )
    if end_date:
        statement = statement.where(
            MarketPrice.observed_at
            < datetime.combine(end_date + timedelta(days=1), time.min)
        )
    return list(
        session.execute(statement.order_by(MarketPrice.observed_at, Cryptocurrency.coin_id))
    )


def market_data_response(
    rows: list[tuple[MarketPrice, Cryptocurrency]],
) -> list[dict]:
    return [
        {
            "coin_id": coin.coin_id,
            "symbol": coin.symbol,
            "name": coin.name,
            "observed_at": price.observed_at,
            "currency": price.currency,
            "price": price.price,
            "market_cap": price.market_cap,
            "total_volume": price.total_volume,
            "source": price.source,
        }
        for price, coin in rows
    ]


def market_summary_response(
    rows: list[tuple[MarketPrice, Cryptocurrency]],
) -> list[dict]:
    groups: dict[tuple[str, str], list[tuple[MarketPrice, Cryptocurrency]]] = {}
    for row in rows:
        price, coin = row
        groups.setdefault((coin.coin_id, price.currency), []).append(row)

    summaries = []
    for (_, currency), observations in groups.items():
        observations.sort(key=lambda row: row[0].observed_at)
        first_price, coin = observations[0]
        last_price, _ = observations[-1]
        prices = [row[0].price for row in observations]
        percentage_change = (
            (last_price.price - first_price.price) * Decimal(100) / first_price.price
            if first_price.price != 0
            else None
        )
        summaries.append(
            {
                "coin_id": coin.coin_id,
                "symbol": coin.symbol,
                "name": coin.name,
                "currency": currency,
                "first_price": first_price.price,
                "last_price": last_price.price,
                "max_price": max(prices),
                "min_price": min(prices),
                "average_price": sum(prices) / len(prices),
                "percentage_change": percentage_change,
                "latest_market_cap": next(
                    (row[0].market_cap for row in reversed(observations) if row[0].market_cap is not None),
                    None,
                ),
                "latest_total_volume": next(
                    (row[0].total_volume for row in reversed(observations) if row[0].total_volume is not None),
                    None,
                ),
                "observations": len(observations),
                "first_observed_at": first_price.observed_at,
                "last_observed_at": last_price.observed_at,
            }
        )
    return summaries


def recent_ingestion_runs(session: Session, limit: int = 50) -> list[IngestionRun]:
    return list(
        session.scalars(
            select(IngestionRun)
            .order_by(IngestionRun.started_at.desc(), IngestionRun.id.desc())
            .limit(limit)
        )
    )
