# bot_service/entrypoints/start_fastapi.sh
#!/bin/bash
# Скрипт запуска FastAPI сервера

echo "Starting FastAPI server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level info
