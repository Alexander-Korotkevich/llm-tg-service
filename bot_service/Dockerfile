# bot_service/Dockerfile
# Вариант с правильной установкой uv

FROM python:3.11-slim

WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копируем pyproject.toml
COPY pyproject.toml ./

# Устанавливаем uv через официальный скрипт (более надёжный способ)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Добавляем uv в PATH
ENV PATH="/root/.local/bin:$PATH"

# Создаём виртуальное окружение и устанавливаем зависимости через uv
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Устанавливаем зависимости проекта
RUN uv pip install --no-cache-dir .

# Копируем код приложения
COPY . .

# Создаём директорию для логов
RUN mkdir -p /app/logs

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
