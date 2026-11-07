#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 -m venv "$ROOT_DIR/.venv"
"$ROOT_DIR/.venv/bin/python" -m pip install -q -r "$ROOT_DIR/crypto-api/requirements.txt" -r "$ROOT_DIR/crypto-dashboard/requirements.txt"

export DATABASE_URL="sqlite:///$ROOT_DIR/cryptoinsight.db"
export CRYPTO_API_URL="http://127.0.0.1:8000"
export DEFAULT_COINS="${DEFAULT_COINS:-bitcoin,ethereum,solana}"
export DEFAULT_CURRENCY="${DEFAULT_CURRENCY:-usd}"

cleanup() {
  kill "$API_PID" "$DASHBOARD_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

(
  cd "$ROOT_DIR/crypto-api"
  "$ROOT_DIR/.venv/bin/uvicorn" app.main:app --host 127.0.0.1 --port 8000
) &
API_PID=$!

for _ in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:8000/health >/dev/null 2>&1; then break; fi
  sleep 1
done

(
  cd "$ROOT_DIR/crypto-dashboard"
  "$ROOT_DIR/.venv/bin/streamlit" run app.py --server.address 127.0.0.1 --server.port 8501
) &
DASHBOARD_PID=$!

echo "CryptoInsight disponible en http://127.0.0.1:8501"
wait "$DASHBOARD_PID"
