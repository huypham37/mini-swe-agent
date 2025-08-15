import unittest
from src.models.openai_model import OpenAIModel

class TestOpenAIModel(unittest.TestCase):
    def setUp(self):
        self.model = OpenAIModel()

    def test_initialization(self):
        """Test that the model initializes properly."""
        self.assertIsNotNone(self.model)

    def test_generate_response(self):
        """Test that the model generates a response to a valid prompt."""
        prompt = "Hello, how are you?"
        response = self.model.generate(prompt)
        self.assertIsNotNone(response)
        self.assertIsInstance(response, str)

    def test_empty_prompt(self):
        """Test behavior with an empty prompt."""
        with self.assertRaises(ValueError):
            self.model.generate("")

    def test_long_prompt(self):
        """Test behavior with a very long prompt."""
        long_prompt = "a" * 10000
        with self.assertRaises(ValueError):
            self.model.generate(long_prompt)

    def test_invalid_input_type(self):
        """Test that invalid input types raise an error."""
        with self.assertRaises(TypeError):
            self.model.generate(123)

    def test_error_handling(self):
        """Test that the model handles unexpected errors gracefully."""
        with self.assertRaises(Exception):
            # Simulate an internal error
            self.model._make_api_call("invalid_input")

if __name__ == "__main__":
    unittest.main()
