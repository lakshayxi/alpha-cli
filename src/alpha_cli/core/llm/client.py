import json
import logging
import subprocess
import shutil
import re
from typing import Optional, Dict, Any
from alpha_cli.core.llm.schema import AlphaGeneration
from alpha_cli.config.settings import Credentials

logger = logging.getLogger(__name__)

class LLMError(Exception):
    """Raised when the delegated CLI tool fails to return a valid response."""
    pass

class LLMClient:
    """
    Orchestrates alpha generation by delegating to specialized agent CLIs.
    """
    
    def __init__(self, creds: Credentials):
        self.provider = creds.llm_provider.lower()
        self._verify_installation()

    def _verify_installation(self) -> None:
        if not shutil.which(self.provider):
            error_msg = f"Delegated CLI '{self.provider}' not found in system PATH."
            logger.error(error_msg)
            raise LLMError(error_msg)

    def generate_alpha(self, prompt: str, system_prompt: str) -> AlphaGeneration:
        full_context = f"{system_prompt}\n\n{prompt}"
        
        try:
            logger.info(f"Delegating generation to '{self.provider}' CLI...")
            
            if self.provider == "gemini":
                return self._call_gemini_cli(full_context)
            elif self.provider == "claude":
                return self._call_claude_cli(full_context)
            else:
                raise LLMError(f"Delegation not implemented for provider: {self.provider}")
                
        except Exception as e:
            logger.error(f"Delegated execution failure: {e}")
            raise LLMError(f"CLI delegation error: {e}")

    def _call_gemini_cli(self, prompt: str) -> AlphaGeneration:
        # Request plain text first as the 'json' format in gemini-cli can be verbose/unpredictable
        cmd = ["gemini", "--prompt", prompt]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        content = result.stdout.strip()
        
        if not content:
            raise LLMError("Gemini CLI returned empty output.")
            
        json_data = self._extract_json(content)
        return AlphaGeneration(**json_data)

    def _call_claude_cli(self, prompt: str) -> AlphaGeneration:
        cmd = ["claude", "-p", prompt]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        content = result.stdout.strip()
        if not content:
            raise LLMError("Claude CLI returned empty output.")
        json_data = self._extract_json(content)
        return AlphaGeneration(**json_data)

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """
        Robust JSON extraction. 
        Filters out markdown code blocks and internal session metadata.
        """
        # 1. Try cleaning markdown code blocks if present
        json_block_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL | re.IGNORECASE)
        if json_block_match:
            try:
                return json.loads(json_block_match.group(1))
            except json.JSONDecodeError:
                pass

        # 2. Find the largest substring that starts with { and ends with }
        # This bypasses session IDs, diff logs, and other conversational noise
        braces_match = re.search(r'(\{.*\})', text, re.DOTALL)
        if braces_match:
            # We try a greedy match first, but if it fails, we'll try a more surgical approach
            potential_json = braces_match.group(1)
            
            # Step-down cleaning: find the last occurrence of }
            # and verify it's the end of a valid JSON object
            try:
                # Basic attempt
                return json.loads(potential_json)
            except json.JSONDecodeError:
                # If greedy failed, try to find the earliest closing brace that makes a valid object
                for i in range(len(potential_json), 0, -1):
                    if potential_json[i-1] == '}':
                        try:
                            return json.loads(potential_json[:i])
                        except json.JSONDecodeError:
                            continue

        raise LLMError(f"Output verification failed. The CLI agent did not return a valid AlphaGeneration JSON object. Raw preview: {text[:200]}...")
