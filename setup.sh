#!/bin/bash

echo "========================================="
echo "   Iniciando entorno Django + PostgreSQL"
echo "========================================="
echo ""

# 1) Levantar (primero docker-compose, luego docker compose)
if ! docker-compose up -d --build 2>/dev/null; then
  docker compose up -d --build
fi

if [ $? -ne 0 ]; then
    echo "Error al construir los contenedores"
    exit 1
fi

# 2) Esperar a que Postgres este listo
echo "=========================================="
echo "Esperando a que la base de datos inicie..."
echo "=========================================="

until docker compose exec -T db pg_isready -U "$DB_USER" >/dev/null 2>&1; do
  echo "  ...aún no, reintentando en 2s"
  sleep 2
done
echo "PostgreSQL listo"

# 3) Esperar a que las migraciones de Django terminen
echo ""
echo "==========================================="
echo "Esperando a que las migraciones terminen..."
echo "==========================================="

APPS=("accounts" "teams" "courses" "learning_paths" "enrollments" "notifications" "administration")

for app in "${APPS[@]}"; do
  docker compose exec -T web python manage.py makemigrations "$app" || true
done

docker compose exec -T web python manage.py migrate --noinput

echo ""
echo "=========================================="
echo "  Entorno listo en http://localhost:8000"
echo "=========================================="
read -p "Presiona Enter para continuar..."