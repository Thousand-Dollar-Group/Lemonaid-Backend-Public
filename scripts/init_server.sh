#!/usr/bin/env bash
set -euo pipefail

echo "🔹 Chekcing if database is ready to be used..."
if [ -f /app/init/check_database.py ]; then
python3 /app/init/check_database.py
fi

echo "🔹 Running CSV ingestion..."
if [ -f /app/init/csv_ingestion.py ]; then
python3 /app/init/csv_ingestion.py
fi

echo "🔹 Creating user table..."
if [ -f /app/init/create_user_table.py ]; then
python3 /app/init/create_user_table.py
fi

echo "🔹 Creating conversation table..."
if [ -f /app/init/create_conversation_table.py ]; then
python3 /app/init/create_conversation_table.py
fi

echo "✅ Initialization done. Starting Uvicorn..."
# exec to hand PID 1 to uvicorn so signals work correctly
exec uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
