# bot_service/entrypoints/start_bot.sh
#!/bin/bash
# Скрипт запуска aiogram бота

echo "Starting aiogram bot..."
exec python -m app.bot.run
