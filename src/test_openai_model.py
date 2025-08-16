import pytest
from unittest.mock import patch, MagicMock
from src.minisweagent.models.openai_model import OpenAIModel, OpenAIAPIError, OpenAIAuthenticationError, OpenAIRateLimitError, OpenAIContextLengthError

def test_init_with_config():
    model = OpenAIModel(model_name="gpt-3.5-turbo", api_key="test_key")
    assert model.config.model_name == "gpt-3.5-turbo"
    assert model.config.api_key == "test_key"
    assert model.n_calls == 0
    assert model.cost == 0.0

def test_init_with_env():
    with patch.dict("os.environ", {"OPENAI_API_KEY": "env_key", "OPENAI_API_BASE": "https://custom.com"}):
        model = OpenAIModel(model_name="gpt-4")
        assert model.config.api_key == "env_key"
        assert model.config.base_url == "https://custom.com/v1"

def test_query_success():
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Hello, world!"
                    }
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5}
        }
        mock_post.return_value = mock_response

        model = OpenAIModel(model_name="gpt-3.5-turbo", cost_per_1k_input_tokens=0.001, cost_per_1k_output_tokens=0.002)
        result = model.query([{"role": "user", "content": "Hello"}])
        assert result["content"] == "Hello, world!"
        assert model.n_calls == 1
        assert model.cost > 0

def test_query_auth_error():
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.return_value = mock_response

        model = OpenAIModel(model_name="gpt-3.5-turbo")
        with pytest.raises(OpenAIAuthenticationError) as exc:
            model.query([{"role": "user", "content": "Hello"}])
        assert "Authentication failed" in str(exc.value)

def test_query_rate_limit_error():
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        mock_post.return_value = mock_response

        model = OpenAIModel(model_name="gpt-3.5-turbo")
        with pytest.raises(OpenAIRateLimitError) as exc:
            model.query([{"role": "user", "content": "Hello"}])
        assert "Rate limit exceeded" in str(exc.value)

def test_query_context_length_error():
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 413
        mock_response.text = "Context length exceeded"
        mock_post.return_value = mock_response

        model = OpenAIModel(model_name="gpt-3.5-turbo")
        with pytest.raises(OpenAIContextLengthError) as exc:
            model.query([{"role": "user", "content": "Hello"}])
        assert "Context length exceeded" in str(exc.value)

def test_cost_calculation():
    model = OpenAIModel(model_name="gpt-3.5-turbo", cost_per_1k_input_tokens=0.001, cost_per_1k_output_tokens=0.002)
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Test response"
                    }
                }
            ],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50}
        }
        mock_post.return_value = mock_response
        result = model.query([{"role": "user", "content": "Hello"}])
        assert model.cost > 0.0
        assert model.cost == 0.0002  # 100*0.001/1000 + 50*0.002/1000 = 0.0001 + 0.0001

def test_get_template_vars():
    model = OpenAIModel(model_name="gpt-3.5-turbo")
    vars = model.get_template_vars()
    assert "n_model_calls" in vars
    assert "model_cost" in vars
    assert vars["n_model_calls"] == 0
    assert vars["model_cost"] == 0.0
