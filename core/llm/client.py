import litellm
import json
import logging
from typing import Optional, List, Dict
from alpha_cli.core.llm.schema import AlphaGeneration
from alpha_cli.config.settings import Credentials

logger = logging.getLogger(__name__)

class LLMError(Exception):
    """Raised when the cloud LLM fails to generate a valid response."""
    pass

class LLMClient:
    """
    Interface for interacting with cloud-based Large Language Models.
    Standardizes generation across different providers using litellm.
    """
    
    PROVIDER_MODEL_MAP = {
        "OpenAI": "gpt-4o",
        "Anthropic": "claude-3-5-sonnet-20240620",
        "Gemini": "gemini/gemini-1.5-pro"
    }
    
    def __init__(self, creds: Credentials):
        self.provider = creds.llm_provider
        self.model = self.PROVIDER_MODEL_MAP.get(self.provider, "gpt-4o")
        
        # Configure API keys for litellm globally within this instance
        self._set_provider_keys(creds.llm_api_key)

    def _set_provider_keys(self, api_key: str) -> None:
        """Configures the necessary environment variables for the selected provider."""
        if self.provider == "OpenAI":
            litellm.openai_key = api_key
        elif self.provider == "Anthropic":
            litellm.anthropic_key = api_key
        elif self.provider == "Gemini":
            litellm.gemini_key = api_key

    def generate_alpha(self, prompt: str, system_prompt: str) -> AlphaGeneration:
        """
        Requests the LLM to generate a new alpha ideation.
        
        Args:
            prompt: The specific request context.
            system_prompt: The core persona and constraints.
            
        Returns:
            A validated AlphaGeneration object.
            
        Raises:
            LLMError: If the response is malformed or the API call fails.
        """
        try:
            logger.debug(f"Sending request to {self.provider} ({self.model})...")
            response = litellm.completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                timeout=120
            )
            
            content = response.choices[0].message.content
            if not content:
                raise LLMError("Empty response received from LLM.")
                
            data = json.loads(content)
            logger.info(f"LLM generation successful for model: {self.model}")
            return AlphaGeneration(**data)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            raise LLMError(f"Malformed JSON from LLM: {e}")
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            raise LLMError(f"LLM provider error: {e}")
