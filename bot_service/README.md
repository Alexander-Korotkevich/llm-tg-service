# Bot Service

Сервис Telegram-бота с интеграцией LLM через OpenRouter, JWT-аутентификацией и асинхронной обработкой задач через Celery.

## Назначение

Bot Service предоставляет Telegram-бота, который:
- Принимает сообщения от пользователей
- Проверяет JWT-токены (валидация на стороне бота, без обращения к Auth Service)
- Отправляет запросы к LLM (OpenRouter) асинхронно через Celery
- Возвращает ответы пользователю



## 🚀 Запуск

```
# Установка с использованием uv (рекомендуется)
uv sync

# Или с использованием pip
pip install -e .
```

### Требования

- Docker и Docker Compose
- Python 3.11+ (для локальной разработки)

### Переменные окружения

Создайте файл `.env` в корне проекта:

```bash
# Telegram Bot Token (получить у @BotFather)
TELEGRAM_BOT_TOKEN=7891234567:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw

# JWT Secret (должен совпадать с Auth Service)
JWT_SECRET=your_super_secret_jwt_key_change_me
JWT_ALG=HS256

# OpenRouter API Key (получить на openrouter.ai)
OPENROUTER_API_KEY=sk-or-v1-64e3b3f9c7a1...

# OpenRouter настройки (опционально)
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=stepfun/step-3.5-flash:free
OPENROUTER_SITE_URL=https://example.com
OPENROUTER_APP_NAME=bot-service

# Redis и RabbitMQ (для Docker)
REDIS_URL=redis://redis:6379/0
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672//
```

### Запуск через docker-compose

```
cd bot_service

# Собрать и запустить все сервисы
make up

# Сборка
make build

# Остановить
make down
```

### Тестирование

#### 1. Запуск тестов

![Pytest](./docs/images/bot-service-test.png)

#### 2. Rabbit

![Rabbit](./docs/images/rabbit.png)

#### 3. Telegram

![Telegram](./docs/images/tg.png)
