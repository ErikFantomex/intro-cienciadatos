import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def price_chart(frame: pd.DataFrame) -> go.Figure:
    return px.line(
        frame,
        x="observed_at",
        y="price",
        color="coin_id",
        title="Evolución histórica del precio",
        labels={"observed_at": "Fecha", "price": "Precio", "coin_id": "Criptomoneda"},
    )


def moving_average_chart(frame: pd.DataFrame) -> go.Figure:
    figure = px.line(
        frame,
        x="observed_at",
        y="price",
        color="coin_id",
        title="Precio y promedio móvil",
        labels={"observed_at": "Fecha", "price": "Precio", "coin_id": "Criptomoneda"},
    )
    for coin_id, group in frame.groupby("coin_id"):
        figure.add_scatter(
            x=group["observed_at"],
            y=group["moving_average"],
            mode="lines",
            name=f"{coin_id} · promedio móvil",
            line={"dash": "dash"},
        )
    return figure


def volume_chart(frame: pd.DataFrame) -> go.Figure:
    return px.line(
        frame,
        x="observed_at",
        y="total_volume",
        color="coin_id",
        title="Volumen histórico",
        labels={"observed_at": "Fecha", "total_volume": "Volumen", "coin_id": "Criptomoneda"},
    )


def market_cap_chart(frame: pd.DataFrame) -> go.Figure:
    return px.line(
        frame,
        x="observed_at",
        y="market_cap",
        color="coin_id",
        title="Capitalización histórica",
        labels={"observed_at": "Fecha", "market_cap": "Capitalización", "coin_id": "Criptomoneda"},
    )


def cumulative_return_chart(frame: pd.DataFrame) -> go.Figure:
    return px.line(
        frame,
        x="observed_at",
        y="cumulative_return_pct",
        color="coin_id",
        title="Rendimiento acumulado",
        labels={"observed_at": "Fecha", "cumulative_return_pct": "Rendimiento (%)", "coin_id": "Criptomoneda"},
    )


def normalized_chart(frame: pd.DataFrame) -> go.Figure:
    return px.line(
        frame,
        x="observed_at",
        y="base_100",
        color="coin_id",
        title="Comparación normalizada (base 100)",
        labels={"observed_at": "Fecha", "base_100": "Índice base 100", "coin_id": "Criptomoneda"},
    )


def returns_chart(frame: pd.DataFrame) -> go.Figure:
    return px.line(
        frame,
        x="observed_at",
        y="return_pct",
        color="coin_id",
        title="Retornos porcentuales",
        labels={"observed_at": "Fecha", "return_pct": "Retorno (%)", "coin_id": "Criptomoneda"},
    )


def returns_histogram(frame: pd.DataFrame) -> go.Figure:
    return px.histogram(
        frame.dropna(subset=["return_pct"]),
        x="return_pct",
        color="coin_id",
        barmode="overlay",
        opacity=0.65,
        title="Distribución de retornos porcentuales",
        labels={"return_pct": "Retorno (%)", "coin_id": "Criptomoneda"},
    )
