import json
import logging
import subprocess
import shutil
import re
from typing import Optional, Dict, Any, List
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
        full_context = f"{system_prompt}\n\nUser Request: {prompt}"
        
        try:
            logger.info(f"Delegating generation to '{self.provider}' CLI...")
            
            if self.provider == "gemini":
                return self._call_gemini_cli(full_context)
            elif self.provider == "claude":
                return self._call_claude_cli(full_context)
            else:
                raise LLMError(f"Delegation not implemented for provider: {self.provider}")
                
        except subprocess.TimeoutExpired:
            raise LLMError("AI Agent timed out (180s).")
        except subprocess.CalledProcessError as e:
            logger.error(f"CLI process failed: {e}")
            raise LLMError(f"CLI returned error: {e.stderr or e.stdout}")
        except Exception as e:
            logger.error(f"Delegated execution failure: {e}")
            raise LLMError(f"CLI delegation error: {e}")

    def _call_gemini_cli(self, prompt: str) -> AlphaGeneration:
        # Using output-format json to get structured session output
        cmd = ["gemini", "--prompt", prompt, "--output-format", "json"]
        
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            check=True,
            timeout=180
        )
        
        content = result.stdout.strip()
        if not content:
            raise LLMError("Gemini CLI returned empty output.")
            
        json_data = self._extract_json(content)
        return AlphaGeneration(**json_data)

    def _call_claude_cli(self, prompt: str) -> AlphaGeneration:
        cmd = ["claude"]
        result = subprocess.run(
            cmd, 
            input=prompt, 
            capture_output=True, 
            text=True, 
            check=True,
            timeout=180
        )
        content = result.stdout.strip()
        json_data = self._extract_json(content)
        return AlphaGeneration(**json_data)

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """
        Surgically extracts the AlphaGeneration object.
        Supports un-nesting stringified JSON from CLI metadata wrappers.
        """
        # 1. Clean markdown if present
        cleaned_text = re.sub(r'```json\s*', '', text, flags=re.IGNORECASE)
        cleaned_text = re.sub(r'```', '', cleaned_text)

        # 2. Extract all JSON objects using stack-based matching
        candidates = []
        stack = []
        start = -1
        for i, char in enumerate(cleaned_text):
            if char == '{':
                if not stack: start = i
                stack.append(char)
            elif char == '}':
                if stack:
                    stack.pop()
                    if not stack: candidates.append(cleaned_text[start:i+1])

        # 3. Validation and Deep Un-nesting
        for candidate in candidates:
            try:
                data = json.loads(candidate)
                
                # Check if this object contains our target keys
                if isinstance(data, dict):
                    if 'expression' in data and 'thesis' in data:
                        return data
                    
                    # LEARNING: Handle Gemini-CLI specific nesting (data['response'] is stringified JSON)
                    if 'response' in data and isinstance(data['response'], str):
                        try:
                            nested_data = json.loads(data['response'])
                            if isinstance(nested_data, dict) and 'expression' in nested_data:
                                return nested_data
                        except json.JSONDecodeError:
                            # If response string isn't pure JSON, try extracting from it recursively
                            return self._extract_json(data['response'])
                            
            except (json.JSONDecodeError, TypeError):
                continue

        raise LLMError(f"Isolator failure: AlphaGeneration keys not found in output. Preview: {text[:150]}...")
