import pandas as pd


NUMERIC_COLUMNS = ["price", "market_cap", "total_volume"]


def prepare_market_data(records: list[dict]) -> pd.DataFrame:
    frame = pd.DataFrame(records)
    if frame.empty:
        return frame

    frame["observed_at"] = pd.to_datetime(frame["observed_at"], utc=True, errors="coerce")
    for column in NUMERIC_COLUMNS:
        if column not in frame:
            frame[column] = pd.NA
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna(subset=["observed_at", "price"])
    frame = frame.sort_values(["coin_id", "observed_at"]).reset_index(drop=True)
    frame["return_pct"] = frame.groupby("coin_id")["price"].pct_change() * 100
    frame["cumulative_return_pct"] = frame.groupby("coin_id")["price"].transform(
        lambda prices: (prices / prices.iloc[0] - 1) * 100
        if not prices.empty and prices.iloc[0] != 0
        else pd.Series(float("nan"), index=prices.index)
    )
    frame["base_100"] = frame.groupby("coin_id")["price"].transform(
        lambda prices: prices / prices.iloc[0] * 100
        if not prices.empty and prices.iloc[0] != 0
        else pd.Series(float("nan"), index=prices.index)
    )
    return frame


def add_moving_average(frame: pd.DataFrame, window: int) -> pd.DataFrame:
    result = frame.copy()
    result["moving_average"] = result.groupby("coin_id")["price"].transform(
        lambda prices: prices.rolling(window=window, min_periods=1).mean()
    )
    return result


def calculate_indicators(frame: pd.DataFrame) -> dict[str, float | int | str | None]:
    if frame.empty:
        return {}
    frame = frame.sort_values("observed_at")
    prices = frame["price"].dropna()
    returns = frame["return_pct"].dropna()
    if prices.empty:
        return {}
    return {
        "last_price": float(prices.iloc[-1]),
        "percentage_change": (
            float((prices.iloc[-1] / prices.iloc[0] - 1) * 100)
            if prices.iloc[0] != 0
            else None
        ),
        "max_price": float(prices.max()),
        "min_price": float(prices.min()),
        "average_price": float(prices.mean()),
        "volatility": float(returns.std()) if len(returns) > 1 else None,
        "latest_market_cap": (
            float(frame["market_cap"].dropna().iloc[-1])
            if frame["market_cap"].notna().any()
            else None
        ),
        "latest_total_volume": (
            float(frame["total_volume"].dropna().iloc[-1])
            if frame["total_volume"].notna().any()
            else None
        ),
        "observations": int(len(prices)),
        "last_observed_at": frame["observed_at"].iloc[-1].isoformat(),
    }
