import pytest
from unittest.mock import AsyncMock
from aiogram.fsm.context import FSMContext

from app.bot.handlers import cmd_save_token, cmd_login, cmd_reset_token


class TestAuthHandlers:
    
    @pytest.mark.asyncio
    async def test_cmd_save_token_success(self, mock_telegram_message, mock_redis_get_handlers, mock_jwt_valid):
        mock_telegram_message.text = "/token valid_jwt_token"
        await cmd_save_token(mock_telegram_message)
        mock_telegram_message.answer.assert_called_once()
        assert "✅" in mock_telegram_message.answer.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_cmd_save_token_without_token(self, mock_telegram_message, mock_redis_get_handlers):
        mock_telegram_message.text = "/token"
        await cmd_save_token(mock_telegram_message)
        mock_telegram_message.answer.assert_called_once()
        assert "❌" in mock_telegram_message.answer.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_cmd_save_token_invalid_token(self, mock_telegram_message, mock_redis_get_handlers, mock_jwt_invalid):
        mock_telegram_message.text = "/token invalid_token_123"
        await cmd_save_token(mock_telegram_message)
        mock_telegram_message.answer.assert_called_once()
        assert "❌" in mock_telegram_message.answer.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_cmd_login_sets_state(self, mock_telegram_message):
        mock_state = AsyncMock(spec=FSMContext)
        await cmd_login(mock_telegram_message, mock_state)
        mock_state.set_state.assert_called_once()
        mock_telegram_message.answer.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cmd_reset_token_without_session(self, mock_telegram_message, mock_redis_get_handlers):
        await cmd_reset_token(mock_telegram_message)
        mock_telegram_message.answer.assert_called_once()
        assert "не найдена" in mock_telegram_message.answer.call_args[0][0]
