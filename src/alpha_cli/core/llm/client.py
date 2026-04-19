import json
import logging
import subprocess
import shutil
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
    Supports integration with 'gemini' (Gemini CLI) and 'claude' (Claude Code).
    Leverages existing local authentication sessions in these tools.
    """
    
    def __init__(self, creds: Credentials):
        self.provider = creds.llm_provider.lower()
        self._verify_installation()

    def _verify_installation(self) -> None:
        """Ensures the required delegate CLI is available in the system PATH."""
        if not shutil.which(self.provider):
            error_msg = f"Delegated CLI '{self.provider}' not found in system PATH."
            logger.error(error_msg)
            raise LLMError(error_msg)

    def generate_alpha(self, prompt: str, system_prompt: str) -> AlphaGeneration:
        """
        Spawns a subprocess to call the selected agent CLI with the generation prompt.
        """
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
        """Executes the gemini CLI in non-interactive mode."""
        # Note: -p/--prompt is used for non-interactive (headless) mode in gemini cli
        cmd = ["gemini", "--prompt", prompt, "--output-format", "json"]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        content = result.stdout.strip()
        
        if not content:
            raise LLMError("Gemini CLI returned empty output.")
            
        json_data = self._extract_json(content)
        return AlphaGeneration(**json_data)

    def _call_claude_cli(self, prompt: str) -> AlphaGeneration:
        """Executes the Claude Code CLI (claude) in non-interactive mode."""
        # Claude Code usually accepts prompts as a positional argument
        cmd = ["claude", "-p", prompt]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        content = result.stdout.strip()
        
        if not content:
            raise LLMError("Claude CLI returned empty output.")
            
        json_data = self._extract_json(content)
        return AlphaGeneration(**json_data)

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Surgically extracts and parses the JSON block from the CLI output."""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Handle cases where the CLI outputs conversational text around the JSON
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end > 0:
                return json.loads(text[start:end])
            raise LLMError("Failed to parse valid JSON from CLI output.")
