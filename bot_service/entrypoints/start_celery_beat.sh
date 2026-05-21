# bot_service/entrypoints/start_celery_beat.sh
#!/bin/bash
# Скрипт запуска Celery beat (для периодических задач, опционально)

echo "Starting Celery beat..."
exec celery -A app.infra.celery_app beat \
    --loglevel=info \
    --scheduler django_celery_beat.schedulers:DatabaseScheduler
