import json
import logging
import os
import time
from dataclasses import asdict, dataclass, field
from typing import Any

import requests
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_not_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from minisweagent.models import GLOBAL_MODEL_STATS

logger = logging.getLogger("openai_model")


@dataclass
class OpenAIModelConfig:
    model_name: str
    base_url: str = "https://api.openai.com/v1"
    api_key: str = ""
    model_kwargs: dict[str, Any] = field(default_factory=dict)
    timeout: int = 120
    max_retries: int = 3
    cost_per_1k_input_tokens: float = 0.0
    cost_per_1k_output_tokens: float = 0.0


class OpenAIAPIError(Exception):
    """Base exception for OpenAI API errors."""


class OpenAIAuthenticationError(OpenAIAPIError):
    """Authentication failed."""


class OpenAIRateLimitError(OpenAIAPIError):
    """Rate limit exceeded."""


class OpenAIContextLengthError(OpenAIAPIError):
    """Context length exceeded."""


class OpenAIModel:
    def __init__(self, **kwargs):
        self.config = OpenAIModelConfig(**kwargs)
        self.cost = 0.0
        self.n_calls = 0
        
        # Set API key from environment if not provided
        if not self.config.api_key:
            self.config.api_key = os.getenv("OPENAI_API_KEY", "")
        
        # Override base_url from environment if set
        if base_url_env := os.getenv("OPENAI_API_BASE"):
            self.config.base_url = base_url_env
        
        # Ensure base_url ends with /v1
        if not self.config.base_url.endswith("/v1"):
            self.config.base_url = self.config.base_url.rstrip("/") + "/v1"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        retry=retry_if_not_exception_type((
            OpenAIAuthenticationError,
            OpenAIRateLimitError,
            OpenAIContextLengthError,
            OpenAIAPIError,
            KeyboardInterrupt,
        )),
    )
    def _make_request(self, messages: list[dict[str, str]], **kwargs) -> dict:
        """Make HTTP request to OpenAI-compatible API."""
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        
        # Prepare request payload
        payload = {
            "model": self.config.model_name,
            "messages": messages,
            **self.config.model_kwargs,
            **kwargs,
        }
        
        # Make request
        response = requests.post(
            f"{self.config.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=self.config.timeout,
        )
        
        # Handle HTTP errors
        if response.status_code == 401:
            raise OpenAIAuthenticationError(f"Authentication failed: {response.text}")
        elif response.status_code == 429:
            raise OpenAIRateLimitError(f"Rate limit exceeded: {response.text}")
        elif response.status_code == 413 or "context_length_exceeded" in str(response.text):
            raise OpenAIContextLengthError(f"Context length exceeded: {response.text}")
        elif not response.ok:
            raise OpenAIAPIError(f"API error {response.status_code}: {response.text}")
        
        try:
            return response.json()
        except json.JSONDecodeError as e:
            raise OpenAIAPIError(f"Invalid JSON response: {e}")

    def _calculate_cost(self, response: dict) -> float:
        """Calculate cost based on token usage or fallback to estimate."""
        if "usage" not in response:
            # Fallback: rough estimate based on message length
            total_chars = sum(len(str(msg.get("content", ""))) for msg in response.get("messages", []))
            estimated_tokens = total_chars // 4  # Rough estimate: 4 chars per token
            return estimated_tokens / 1000 * max(self.config.cost_per_1k_input_tokens, 0.001)
        
        usage = response["usage"]
        input_cost = usage.get("prompt_tokens", 0) / 1000 * self.config.cost_per_1k_input_tokens
        output_cost = usage.get("completion_tokens", 0) / 1000 * self.config.cost_per_1k_output_tokens
        return input_cost + output_cost

    def query(self, messages: list[dict[str, str]], **kwargs) -> dict:
        """Query the OpenAI-compatible API and return response."""
        try:
            response = self._make_request(messages, **kwargs)
        except OpenAIAuthenticationError as e:
            # Add helpful message about setting API key
            raise OpenAIAuthenticationError(f"{e}. Set OPENAI_API_KEY or use mini-extra config.")
        
        # Extract content from response
        if "choices" not in response or not response["choices"]:
            raise OpenAIAPIError("No choices in API response")
        
        content = response["choices"][0].get("message", {}).get("content", "")
        
        # Update statistics
        cost = self._calculate_cost(response)
        self.n_calls += 1
        self.cost += cost
        GLOBAL_MODEL_STATS.add(cost)
        
        return {"content": content}

    def get_template_vars(self) -> dict[str, Any]:
        """Return template variables for configuration."""
        return asdict(self.config) | {"n_model_calls": self.n_calls, "model_cost": self.cost}