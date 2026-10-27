#!/usr/bin/env bash
# Construye el frontend y recolecta los estaticos de Django.
# Uso: ./build.sh
set -e

cd "$(dirname "$0")"

if command -v bun >/dev/null 2>&1; then
    echo "==> Usando Bun"
    bun install
    bun run build
else
    echo "==> Bun no disponible; usando npm"
    npm install
    npm run build
fi

echo "==> collectstatic"
python manage.py collectstatic --noinput
echo "==> Build completo"
