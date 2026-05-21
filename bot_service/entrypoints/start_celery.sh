# bot_service/entrypoints/start_celery.sh
#!/bin/bash
# Скрипт запуска Celery worker

echo "Starting Celery worker..."
exec celery -A app.infra.celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --max-tasks-per-child=100 \
    --time-limit=300 \
    --soft-time-limit=240
