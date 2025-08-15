import pytest

class OpenAIModel:
    def generate(self, prompt, max_tokens=100):
        if not prompt:
            raise ValueError("Prompt cannot be empty")
        if not isinstance(prompt, str):
            raise TypeError("Prompt must be a string")
        return f"Generated response for: {prompt}"

def test_openai_model_initialization():
    model = OpenAIModel()
    assert model is not None

def test_openai_model_generate_success():
    model = OpenAIModel()
    result = model.generate("Hello, how are you?")
    assert "Generated response for: Hello, how are you?" in result

def test_openai_model_generate_empty_prompt():
    model = OpenAIModel()
    with pytest.raises(ValueError):
        model.generate("")

def test_openai_model_generate_invalid_input():
    model = OpenAIModel()
    with pytest.raises(TypeError):
        model.generate(123)
