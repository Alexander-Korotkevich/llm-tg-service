import pytest
from unittest.mock import patch

from app.bot.handlers import handle_text_message


class TestMessageHandlers:
    
    @pytest.mark.asyncio
    async def test_handle_message_no_token(self, mock_telegram_message, no_auth_mocks):
        mock_telegram_message.text = "Привет, как дела?"
        with patch("app.bot.handlers.llm_request") as mock_llm:
            await handle_text_message(mock_telegram_message)
            mock_telegram_message.answer.assert_called_once()
            assert "Доступ запрещён" in mock_telegram_message.answer.call_args[0][0]
            mock_llm.delay.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handle_message_with_valid_token(self, mock_telegram_message, full_handler_mocks, mock_celery_task):
        mock_telegram_message.text = "Привет, как дела?"
        await handle_text_message(mock_telegram_message)
        mock_telegram_message.answer.assert_called_once()
        mock_celery_task.delay.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_message_with_expired_token(self, mock_telegram_message, mock_redis_get_handlers):
        mock_telegram_message.text = "Привет!"
        with patch("app.bot.handlers.decode_and_validate") as mock_decode:
            from app.core.jwt import JWTValidationError
            mock_decode.side_effect = JWTValidationError("Срок действия токена истёк")
            redis_client = await mock_redis_get_handlers.return_value
            await redis_client.set("telegram:123456789:jwt", "expired_token", ex=300)
            with patch("app.bot.handlers.llm_request") as mock_llm:
                await handle_text_message(mock_telegram_message)
                mock_telegram_message.answer.assert_called_once()
                mock_llm.delay.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handle_message_celery_error(self, mock_telegram_message, full_handler_mocks):
        mock_telegram_message.text = "Привет!"
        with patch("app.bot.handlers.llm_request") as mock_llm:
            mock_llm.delay.side_effect = Exception("Celery недоступен")
            await handle_text_message(mock_telegram_message)
            mock_telegram_message.answer.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_empty_message(self, mock_telegram_message, full_handler_mocks):
        mock_telegram_message.text = ""
        with patch("app.bot.handlers.llm_request") as mock_llm:
            await handle_text_message(mock_telegram_message)
            mock_telegram_message.answer.assert_called_once()
            mock_llm.delay.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handle_command_message_not_processed(self, mock_telegram_message, full_handler_mocks):
        """Тест: команды не обрабатываются как обычные сообщения."""
        mock_telegram_message.text = "/help"
        with patch("app.bot.handlers.llm_request") as mock_llm:
            await handle_text_message(mock_telegram_message)
            # Команда должна быть проигнорирована
            mock_llm.delay.assert_not_called()
