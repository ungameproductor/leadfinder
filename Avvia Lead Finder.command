#!/bin/bash
# Doppio clic in Finder: avvia Lead Finder e apre il browser.
set -euo pipefail
cd "$(dirname "$0")"
ROOT="$(pwd)"
URL="http://127.0.0.1:8000"
HEALTH="$URL/api/health"
UVICORN="$ROOT/.venv/bin/uvicorn"

already_up() {
  curl -sf "$HEALTH" >/dev/null 2>&1
}

needs_frontend_build() {
  local dist="$ROOT/frontend/dist/index.html"
  [[ ! -f "$dist" ]] && return 0
  find "$ROOT/frontend/src" "$ROOT/frontend/index.html" "$ROOT/frontend/package.json" "$ROOT/frontend/vite.config.ts" \
    -newer "$dist" 2>/dev/null | grep -q .
}

if [[ ! -x "$UVICORN" ]]; then
  echo "Ambiente Python non trovato (.venv)."
  echo "Apri un terminale in questa cartella ed esegui:"
  echo "  python3 -m venv .venv && source .venv/bin/activate && pip install -e ."
  echo
  read -r -p "Premi Invio per chiudere…"
  exit 1
fi

if needs_frontend_build; then
  if [[ ! -x "$(command -v npm)" ]]; then
    echo "UI da ricompilare e npm non è disponibile."
    read -r -p "Premi Invio per chiudere…"
    exit 1
  fi
  echo "Compilazione dell'interfaccia…"
  (cd "$ROOT/frontend" && npm install && npm run build)
fi

if already_up; then
  open "$URL"
  exit 0
fi

if lsof -nP -iTCP:8000 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "La porta 8000 è occupata da un altro programma."
  read -r -p "Premi Invio per chiudere…"
  exit 1
fi

echo "Avvio Lead Finder…"
(
  for _ in $(seq 1 60); do
    if already_up; then
      open "$URL"
      exit 0
    fi
    sleep 0.25
  done
) &

exec "$UVICORN" app.main:app --app-dir backend --host 127.0.0.1 --port 8000
