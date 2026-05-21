import pytest
import respx
from httpx import Response
from app.services.openrouter_client import (
    chat_completion_sync,
    OpenRouterClient,
    OpenRouterNetworkError,
    OpenRouterAPIError,
    OpenRouterError,
)


class TestOpenRouterClient:
    """Интеграционные тесты OpenRouter клиента."""
    
    @pytest.fixture
    def mock_openrouter_success(self):
        """Мок успешного ответа OpenRouter."""
        mock_response = {
            "id": "chatcmpl-test123",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "stepfun/step-3.5-flash:free",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Привет! Я AI ассистент. Чем могу помочь?"
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30
            }
        }
        
        with respx.mock(
            base_url="https://openrouter.ai",
            assert_all_called=False,
            assert_all_mocked=False,
        ) as respx_mock:
            respx_mock.post("/api/v1/chat/completions").mock(
                return_value=Response(200, json=mock_response)
            )
            yield respx_mock
    
    @pytest.fixture
    def mock_openrouter_error(self):
        """Мок ошибочного ответа OpenRouter."""
        error_response = {
            "error": {
                "message": "Invalid API key",
                "code": 401
            }
        }
        
        with respx.mock(
            base_url="https://openrouter.ai",
            assert_all_called=False,
            assert_all_mocked=False,
        ) as respx_mock:
            respx_mock.post("/api/v1/chat/completions").mock(
                return_value=Response(401, json=error_response)
            )
            yield respx_mock
    
    @pytest.fixture
    def mock_openrouter_timeout(self):
        """Мок таймаута OpenRouter."""
        with respx.mock(
            base_url="https://openrouter.ai",
            assert_all_called=False,
            assert_all_mocked=False,
        ) as respx_mock:
            respx_mock.post("/api/v1/chat/completions").mock(
                side_effect=Exception("Connection timeout")
            )
            yield respx_mock
    
    def test_chat_completion_success(self, mock_openrouter_success):
        """
        Тест: успешный запрос к OpenRouter возвращает текст ответа.
        """
        response = chat_completion_sync(
            prompt="Привет!",
            temperature=0.7,
            max_tokens=100
        )
        
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
        assert "Привет" in response or "ассистент" in response
        
        # Проверяем, что запрос был сделан
        assert mock_openrouter_success["/api/v1/chat/completions"].called
    
    def test_chat_completion_with_system_prompt(self, mock_openrouter_success):
        """
        Тест: запрос с системным промптом.
        """
        client = OpenRouterClient()
        response = client.chat_completion_sync(
            prompt="Расскажи о себе",
            system_prompt="Ты - полезный ассистент, отвечай кратко",
            temperature=0.5,
            max_tokens=50
        )
        
        assert response is not None
        assert isinstance(response, str)
    
    def test_chat_completion_api_error(self, mock_openrouter_error):
        """
        Тест: ошибка API (401, 404, 500) вызывает OpenRouterAPIError.
        """
        with pytest.raises(OpenRouterAPIError) as exc_info:
            chat_completion_sync(prompt="Hello")
        
        assert exc_info.value.status_code == 401
        assert "Invalid API key" in exc_info.value.message
    
    def test_chat_completion_network_error(self, mock_openrouter_timeout):
        """
        Тест: ошибка сети вызывает OpenRouterNetworkError.
        """
        with pytest.raises(OpenRouterNetworkError):
            chat_completion_sync(prompt="Hello")
    
    def test_payload_format(self):
        """
        Тест: проверка правильного формирования payload.
        """
        client = OpenRouterClient()
        payload = client._build_payload(
            prompt="User question",
            system_prompt="System instruction",
            temperature=0.8,
            max_tokens=200
        )
        
        assert "model" in payload
        assert "messages" in payload
        assert len(payload["messages"]) == 2
        assert payload["messages"][0]["role"] == "system"
        assert payload["messages"][0]["content"] == "System instruction"
        assert payload["messages"][1]["role"] == "user"
        assert payload["messages"][1]["content"] == "User question"
        assert payload["temperature"] == 0.8
        assert payload["max_tokens"] == 200
    
    def test_parse_response_success(self):
        """
        Тест: парсинг успешного ответа извлекает правильный текст.
        """
        client = OpenRouterClient()
        response_data = {
            "choices": [
                {
                    "message": {
                        "content": "Это ответ от AI"
                    }
                }
            ]
        }
        
        result = client._parse_response(response_data)
        assert result == "Это ответ от AI"
    
    def test_parse_response_missing_choices(self):
        """
        Тест: отсутствие поля choices вызывает ошибку.
        """
        client = OpenRouterClient()
        response_data = {}
        
        with pytest.raises(OpenRouterError):
            client._parse_response(response_data)
    
    def test_parse_response_empty_choices(self):
        """
        Тест: пустой choices вызывает ошибку.
        """
        client = OpenRouterClient()
        response_data = {"choices": []}
        
        with pytest.raises(OpenRouterError):
            client._parse_response(response_data)
    
    def test_parse_response_missing_content(self):
        """
        Тест: отсутствие content в сообщении вызывает ошибку.
        """
        client = OpenRouterClient()
        response_data = {
            "choices": [
                {"message": {}}
            ]
        }
        
        with pytest.raises(OpenRouterError):
            client._parse_response(response_data)
