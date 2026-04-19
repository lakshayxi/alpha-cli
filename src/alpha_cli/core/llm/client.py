import json
import logging
from typing import Optional, List, Dict, Any
from alpha_cli.core.llm.schema import AlphaGeneration
from alpha_cli.config.settings import Credentials

# Direct SDK imports
import openai
import anthropic
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

class LLMError(Exception):
    """Raised when the cloud LLM fails to generate a valid response."""
    pass

class LLMClient:
    """
    Interface for interacting with cloud-based Large Language Models.
    Standardizes generation across different providers using direct SDKs.
    Supports both explicit API keys and native web-based (OAuth) authentication.
    """
    
    PROVIDER_MODEL_MAP = {
        "OpenAI": "gpt-4o",
        "Anthropic": "claude-3-5-sonnet-20240620",
        "Gemini": "gemini-1.5-pro"
    }
    
    def __init__(self, creds: Credentials):
        self.provider = creds.llm_provider
        self.model = self.PROVIDER_MODEL_MAP.get(self.provider, "gpt-4o")
        self.api_key = creds.llm_api_key
        self.use_cli_auth = creds.use_cli_auth
        self.oauth_token_json = creds.oauth_token_json
        
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initializes the specific provider's client or configuration."""
        try:
            if self.provider == "OpenAI":
                self.client = openai.OpenAI(api_key=self.api_key)
            elif self.provider == "Anthropic":
                self.client = anthropic.Anthropic(api_key=self.api_key)
            elif self.provider == "Gemini":
                if self.use_cli_auth and self.oauth_token_json:
                    from google.oauth2.credentials import Credentials as OAuthCredentials
                    # Load the serialized tokens from the setup process
                    creds_dict = json.loads(self.oauth_token_json)
                    google_creds = OAuthCredentials.from_authorized_user_info(creds_dict)
                    logger.info("Initializing Gemini client with captured OAuth session.")
                    self.client = genai.Client(credentials=google_creds)
                else:
                    # Fallback to standard API key
                    self.client = genai.Client(api_key=self.api_key)
        except Exception as e:
            raise LLMError(f"Failed to initialize {self.provider} client: {e}")

    def generate_alpha(self, prompt: str, system_prompt: str) -> AlphaGeneration:
        """Requests the LLM to generate a new alpha ideation."""
        try:
            logger.debug(f"Sending request to {self.provider} ({self.model})...")
            
            if self.provider == "OpenAI":
                return self._call_openai(prompt, system_prompt)
            elif self.provider == "Anthropic":
                return self._call_anthropic(prompt, system_prompt)
            elif self.provider == "Gemini":
                return self._call_gemini(prompt, system_prompt)
            else:
                raise LLMError(f"Unsupported provider: {self.provider}")
                
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise LLMError(f"LLM provider error: {e}")

    def _call_openai(self, prompt: str, system_prompt: str) -> AlphaGeneration:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            timeout=120
        )
        content = response.choices[0].message.content
        return AlphaGeneration(**json.loads(content))

    def _call_anthropic(self, prompt: str, system_prompt: str) -> AlphaGeneration:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            system=system_prompt,
            messages=[
                {"role": "user", "content": prompt}
            ],
            timeout=120
        )
        content = response.content[0].text
        json_data = self._extract_json(content)
        return AlphaGeneration(**json_data)

    def _call_gemini(self, prompt: str, system_prompt: str) -> AlphaGeneration:
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json"
            )
        )
        return AlphaGeneration(**json.loads(response.text))

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Helper to find and parse JSON block in case of conversational prefixes."""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end > 0:
                return json.loads(text[start:end])
            raise LLMError("Could not extract valid JSON from LLM response.")
