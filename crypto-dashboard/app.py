import os
from datetime import date, timedelta

import pandas as pd
import streamlit as st

from api_client import ApiClientError, NestApiClient
from charts import (
    cumulative_return_chart,
    market_cap_chart,
    moving_average_chart,
    normalized_chart,
    price_chart,
    returns_chart,
    returns_histogram,
    volume_chart,
)
from indicators import add_moving_average, calculate_indicators, prepare_market_data

st.set_page_config(page_title="CryptoInsight", page_icon="₿", layout="wide")
client = NestApiClient()
default_coins = [
    coin.strip()
    for coin in os.getenv("DEFAULT_COINS", "bitcoin,ethereum,solana").split(",")
    if coin.strip()
]
default_currency = os.getenv("DEFAULT_CURRENCY", "usd").lower()


def format_number(value: float | int | None, currency: str = "") -> str:
    if value is None or pd.isna(value):
        return "Sin datos"
    return f"{currency} {value:,.2f}".strip()


def load_service_status() -> None:
    try:
        health = client.health()
        st.sidebar.success("NestJS: disponible")
        if health.get("status") == "healthy":
            st.sidebar.success("FastAPI: disponible")
            st.sidebar.success("MySQL: conectado")
        else:
            st.sidebar.warning("FastAPI o MySQL no están saludables.")
    except ApiClientError as error:
        st.sidebar.error("NestJS / FastAPI: no disponible")
        st.sidebar.caption(str(error))


st.title("CryptoInsight")
st.caption(
    "Exploración académica de datos históricos de criptomonedas "
    "obtenidos mediante CoinGecko."
)
st.warning(
    "Proyecto académico. La información presentada no constituye asesoría financiera."
)
load_service_status()

with st.sidebar:
    st.header("Acceso para ingestión")
    email = st.text_input("Correo de usuario", key="login_email")
    password = st.text_input("Contraseña", type="password", key="login_password")
    if st.button("Iniciar sesión"):
        try:
            login = client.login(email, password)
            token = login.get("token")
            if not token:
                st.error("La respuesta de inicio de sesión no incluyó un token.")
            else:
                st.session_state["jwt_token"] = token
                st.success("Sesión iniciada.")
        except ApiClientError as error:
            st.error(str(error))
    if st.session_state.get("jwt_token"):
        st.caption("Sesión autenticada para solicitar una ingestión.")
        if st.button("Cerrar sesión"):
            st.session_state.pop("jwt_token", None)
            st.rerun()

try:
    registered_coins = client.coins()
    available_coins = sorted(
        set(default_coins)
        | {coin["coin_id"] for coin in registered_coins if coin.get("coin_id")}
    )
except ApiClientError as error:
    registered_coins = []
    available_coins = default_coins
    st.error(f"No se pudo cargar la lista de criptomonedas: {error}")

if "extra_coins" not in st.session_state:
    st.session_state["extra_coins"] = []
with st.sidebar:
    st.header("Criptomonedas")
    new_coin_id = st.text_input("Agregar coin_id", placeholder="dogecoin")
    if st.button("Agregar identificador") and new_coin_id.strip():
        normalized_coin = new_coin_id.strip().lower()
        if normalized_coin not in available_coins:
            st.session_state["extra_coins"] = sorted(
                set(st.session_state["extra_coins"]) | {normalized_coin}
            )
            st.rerun()
    available_coins = sorted(
        set(available_coins) | set(st.session_state["extra_coins"])
    )
    selected_coins = st.multiselect(
        "Selecciona una o más criptomonedas",
        options=available_coins,
        default=[coin for coin in default_coins if coin in available_coins],
        key="selected_coins",
    )
    currency = st.text_input(
        "Moneda de cotización", value=default_currency, key="currency"
    ).strip().lower()
    start_date = st.date_input(
        "Fecha inicial", value=date.today() - timedelta(days=30), key="start_date"
    )
    end_date = st.date_input("Fecha final", value=date.today(), key="end_date")
    moving_window = st.slider(
        "Ventana del promedio móvil", 2, 90, 7, key="moving_window"
    )
    st.button("Recargar datos")

    if st.button("Actualizar desde CoinGecko", type="primary"):
        token = st.session_state.get("jwt_token")
        if not token:
            st.error("Inicia sesión antes de solicitar una ingestión.")
        elif not selected_coins:
            st.error("Selecciona al menos una criptomoneda.")
        elif end_date < start_date:
            st.error("La fecha final debe ser igual o posterior a la inicial.")
        else:
            try:
                outcome = client.ingest(
                    selected_coins,
                    currency,
                    start_date.isoformat(),
                    end_date.isoformat(),
                    token,
                )
                for result in outcome.get("results", []):
                    if result.get("status") == "success":
                        st.success(
                            f"{result['coin_id']}: {result['records_received']} registros "
                            "recibidos y almacenados/actualizados."
                        )
                    else:
                        st.warning(
                            f"{result.get('coin_id', 'Criptomoneda')}: "
                            f"{result.get('message', 'ingestión fallida')}"
                        )
                st.rerun()
            except ApiClientError as error:
                st.error(str(error))

st.subheader("Resumen del periodo")
if not selected_coins:
    st.info("Selecciona criptomonedas para consultar sus datos.")
else:
    try:
        summary = client.market_summary(
            selected_coins,
            currency,
            start_date.isoformat(),
            end_date.isoformat(),
        )
        if summary:
            summary_frame = pd.DataFrame(summary).set_index("coin_id")
            for coin_id in selected_coins:
                if coin_id not in summary_frame.index:
                    continue
                row = summary_frame.loc[coin_id]
                st.markdown(f"### {coin_id}")
                metrics = st.columns(5)
                metrics[0].metric("Último precio", format_number(row["last_price"], currency.upper()))
                change = float(row["percentage_change"]) if pd.notna(row["percentage_change"]) else None
                metrics[1].metric(
                    "Variación del periodo",
                    f"{change:.2f}%" if change is not None else "Sin datos",
                )
                metrics[2].metric("Máximo", format_number(float(row["max_price"]), currency.upper()))
                metrics[3].metric("Mínimo", format_number(float(row["min_price"]), currency.upper()))
                metrics[4].metric("Promedio", format_number(float(row["average_price"]), currency.upper()))
                details = st.columns(5)
                details[0].metric("Capitalización reciente", format_number(float(row["latest_market_cap"]) if pd.notna(row["latest_market_cap"]) else None, currency.upper()))
                details[1].metric("Volumen reciente", format_number(float(row["latest_total_volume"]) if pd.notna(row["latest_total_volume"]) else None, currency.upper()))
                details[2].metric("Observaciones", int(row["observations"]))
                details[3].metric("Primera observación", str(row["first_observed_at"]))
                details[4].metric("Última observación", str(row["last_observed_at"]))
        else:
            st.info("No hay datos almacenados para este periodo. Inicia sesión y solicita una ingestión.")
    except ApiClientError as error:
        st.error(f"No se pudo cargar el resumen: {error}")

st.subheader("Datos históricos y visualizaciones")
try:
    records = client.market_data(
        selected_coins,
        currency,
        start_date.isoformat(),
        end_date.isoformat(),
    ) if selected_coins else []
    market_frame = prepare_market_data(records)
    if market_frame.empty:
        st.info("No hay observaciones almacenadas para los filtros seleccionados.")
    else:
        market_frame = add_moving_average(market_frame, moving_window)
        for coin_id, coin_frame in market_frame.groupby("coin_id"):
            indicators = calculate_indicators(coin_frame)
            st.markdown(f"### Indicadores de {coin_id}")
            cols = st.columns(4)
            volatility = indicators.get("volatility")
            cols[0].metric(
                "Volatilidad (retornos)",
                f"{volatility:.2f}%" if volatility is not None else "Sin datos",
            )
            cols[1].metric("Observaciones", indicators.get("observations", 0))
            cols[2].metric("Última fecha observada", str(indicators.get("last_observed_at", "Sin datos")))
            cols[3].metric("Precio último", format_number(indicators.get("last_price"), currency.upper()))

        tab_price, tab_market, tab_return, tab_table = st.tabs(
            ["Precios", "Volumen y capitalización", "Rendimientos", "Tabla histórica"]
        )
        with tab_price:
            st.plotly_chart(price_chart(market_frame), use_container_width=True)
            st.plotly_chart(moving_average_chart(market_frame), use_container_width=True)
        with tab_market:
            st.plotly_chart(volume_chart(market_frame), use_container_width=True)
            st.plotly_chart(market_cap_chart(market_frame), use_container_width=True)
        with tab_return:
            st.plotly_chart(cumulative_return_chart(market_frame), use_container_width=True)
            st.plotly_chart(normalized_chart(market_frame), use_container_width=True)
            st.plotly_chart(returns_chart(market_frame), use_container_width=True)
            st.plotly_chart(returns_histogram(market_frame), use_container_width=True)
        with tab_table:
            st.dataframe(
                market_frame.sort_values("observed_at", ascending=False),
                use_container_width=True,
                hide_index=True,
            )
except ApiClientError as error:
    st.error(f"No se pudieron cargar los datos históricos: {error}")

st.subheader("Historial de ingestiones")
try:
    runs = client.ingestion_runs()
    if runs:
        runs_frame = pd.DataFrame(runs)
        latest = runs_frame.iloc[0]
        st.info(
            f"Última ejecución: {latest['coin_id']} · "
            f"{ {'success': 'completada', 'failed': 'fallida', 'running': 'en curso'}.get(latest['status'], 'desconocida') } · "
            f"{latest['started_at']}"
        )
        runs_frame["status"] = runs_frame["status"].map(
            {"success": "completada", "failed": "fallida", "running": "en curso"}
        ).fillna("desconocida")
        runs_frame = runs_frame.rename(
            columns={
                "coin_id": "Criptomoneda",
                "currency": "Moneda",
                "start_date": "Fecha inicial",
                "end_date": "Fecha final",
                "records_received": "Registros recibidos",
                "records_stored": "Registros guardados o actualizados",
                "status": "Estado",
                "error_message": "Error",
                "started_at": "Inicio",
                "finished_at": "Fin",
            }
        )
        st.dataframe(runs_frame, use_container_width=True, hide_index=True)
    else:
        st.info("Todavía no hay ejecuciones de ingestión.")
except ApiClientError as error:
    st.error(f"No se pudo cargar el historial de ingestiones: {error}")
