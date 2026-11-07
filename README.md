# CryptoInsight MVP

Dashboard académico para consultar y visualizar precios históricos de
criptomonedas. La aplicación consume la API pública de Binance, guarda las
observaciones en SQLite y presenta indicadores y gráficas con Streamlit.

> La información es únicamente educativa y no constituye asesoría financiera.

## Alcance actual

El MVP permite:

- Consultar velas diarias públicas de Binance sin API key ni autenticación.
- Seleccionar Bitcoin, Ethereum, Solana u otro símbolo compatible con Binance.
- Elegir moneda (`usd`, `usdt` o `eur`) y un rango de fechas.
- Guardar precios y volumen en una base SQLite local.
- Evitar duplicados al repetir una ingestión.
- Mostrar precio inicial, final, máximo, mínimo, promedio y variación.
- Mostrar gráficas de precio, volumen, rendimientos y promedio móvil.
- Consultar los datos guardados mediante una API FastAPI documentada con Swagger.

## Fuera del alcance

Esta entrega no incluye:

- Compra, venta, órdenes ni conexión a cuentas de Binance.
- Portafolios, alertas, predicciones o recomendaciones de inversión.
- Usuarios, login, JWT, pagos o roles.
- MySQL, PostgreSQL, NestJS o el módulo de productos de la versión anterior.
- Un dashboard Python ejecutándose dentro de GitHub Pages.

GitHub Pages solo sirve archivos estáticos; no puede ejecutar FastAPI, SQLite ni
Streamlit. Por eso se incluye una página pública de presentación en
[`docs/index.html`](./docs/index.html), mientras que el dashboard interactivo
se ejecuta localmente. Para publicar el dashboard en internet se necesita un
servicio que ejecute Python, como Streamlit Community Cloud, Render o Railway.

## Arquitectura

```text
Usuario
  └── Streamlit (:8501)
        └── FastAPI (:8000)
              ├── Binance Spot API pública
              └── SQLite (cryptoinsight.db)
```

| Componente | Función |
|---|---|
| `crypto-dashboard` | Interfaz, filtros, métricas y visualizaciones |
| `crypto-api` | Validación, ingestión, persistencia y consultas |
| Binance | Fuente externa de velas públicas |
| SQLite | Persistencia local sin configuración adicional |

## Ejecutar localmente

Requisitos: Python 3.10 o superior y `curl`.

```bash
chmod +x run-mvp.sh
./run-mvp.sh
```

El script crea `.venv`, instala las dependencias, inicia FastAPI y después
Streamlit. Abre:

- Dashboard: <http://127.0.0.1:8501>
- Swagger: <http://127.0.0.1:8000/docs>
- Healthcheck: <http://127.0.0.1:8000/health>

La base se crea como `cryptoinsight.db` en la raíz del proyecto. Para detener
la aplicación presiona `Ctrl+C`.

## Ejecutar con Docker

Si Docker está instalado:

```bash
docker compose up --build
```

Los mismos puertos quedan publicados en `8501` y `8000`. Docker usa un volumen
llamado `crypto_data` para conservar la base SQLite.

## Uso del dashboard

1. Selecciona una o más monedas.
2. Selecciona `usd`, `usdt` o `eur`.
3. Define las fechas inicial y final.
4. Presiona **Actualizar desde Binance** para descargar y guardar datos.
5. Revisa las métricas y gráficas.

Los identificadores se convierten a mercados de Binance. Por ejemplo,
`bitcoin` se consulta como `BTCUSDT`, `ethereum` como `ETHUSDT` y `solana` como
`SOLUSDT`. También puedes usar directamente `btc`, `eth` o `sol`. Si un
identificador no existe, la API muestra un error claro y no crea datos
ficticios.

## API principal

FastAPI se documenta automáticamente en `/docs`.

| Método | Ruta | Uso |
|---|---|---|
| `GET` | `/health` | Comprueba que la API y SQLite estén disponibles |
| `GET` | `/api/coins` | Lista las monedas ya guardadas |
| `GET` | `/api/market-data` | Devuelve observaciones históricas |
| `GET` | `/api/market-summary` | Devuelve indicadores agregados |
| `POST` | `/api/ingest` | Descarga y guarda velas desde Binance |
| `GET` | `/api/ingestion-runs` | Muestra ejecuciones recientes |

Ejemplo:

```bash
curl -X POST http://127.0.0.1:8000/api/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "coin_ids": ["btc"],
    "currency": "usd",
    "start_date": "2026-10-01",
    "end_date": "2026-10-07"
  }'
```

La API no requiere encabezados de autenticación en el MVP local.

## Publicar la página de proyecto en GitHub Pages

La carpeta `docs/` contiene una página estática que GitHub Pages puede servir.
Los enlaces de la página están configurados para
`github.com/Erikafantomex/intro-cienciadatos`.

1. Sube el repositorio a GitHub.
2. En **Settings → Pages**, selecciona **Deploy from a branch**.
3. Elige la rama principal y la carpeta `/docs`.
4. Guarda la configuración.

La URL tendrá esta forma:

```text
https://Erikafantomex.github.io/intro-cienciadatos/
```

Esa página documenta el MVP y enlaza al código. No reemplaza el dashboard
interactivo: para mostrar el dashboard en línea hay que desplegar también
`crypto-api` y `crypto-dashboard` en un servicio con ejecución de Python.

## Estructura relevante

```text
crypto-api/
  app/
    main.py                 API FastAPI
    coingecko_client.py     Adaptador público de Binance
    ingestion_service.py    Persistencia e idempotencia
    market_service.py       Consultas y resúmenes
crypto-dashboard/
  app.py                    Interfaz Streamlit
  api_client.py             Cliente HTTP de FastAPI
  charts.py                 Gráficas
  indicators.py             Indicadores
docs/
  index.html                Página para GitHub Pages
compose.yaml                Despliegue de dos servicios
run-mvp.sh                  Arranque local
```

## Limitaciones de datos

Binance puede limitar solicitudes, bloquear regiones o no disponer de todos los
pares. El MVP conserva los datos anteriores si una descarga falla y registra
el error en `ingestion_runs`. Los resultados dependen de la disponibilidad y
exactitud de la fuente externa.
