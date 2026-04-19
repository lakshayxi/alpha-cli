from typing import List, Dict, Any
import json
import random
import logging

logger = logging.getLogger(__name__)

class PromptBuilder:
    """
    Constructs rich context prompts for the LLM.
    Dynamically integrates 'Learned Heuristics' synthesized from previous sessions.
    """
    
    BASE_SYSTEM_PROMPT = """You are a Senior Quantitative Researcher. Your objective is to design high-conviction mathematical trading signals (alphas) for the WorldQuant Brain platform using the FASTEXPR syntax.

CORE DOMAIN PRINCIPLES:
1. MARKET BIAS: For the USA region, focus on price reversal and mean-reversion signals.
2. NORMALIZATION: Signals must be bounded using `ts_rank` or `ts_scale`.
3. RISK NEUTRALIZATION: Signal will be industry-neutralized; avoid redundant cross-sectional rank wrappers.
"""

    def __init__(self):
        self.operators: List[Dict] = []
        self.fields: List[Dict] = []
        self.winning_alphas: List[str] = []
        self.failed_expressions: List[str] = []
        self.heuristics: List[str] = []

    def set_context(self, 
                   operators: List[Dict], 
                   fields: List[Dict], 
                   winners: List[str], 
                   failed: List[str],
                   heuristics: List[str]) -> None:
        """Hydrates the builder with market data and synthesized patterns."""
        self.operators = operators
        self.fields = fields
        self.winning_alphas = winners
        self.failed_expressions = failed
        self.heuristics = heuristics

    def _get_dynamic_system_prompt(self) -> str:
        """Synthesizes the system prompt with active heuristics."""
        prompt = self.BASE_SYSTEM_PROMPT
        
        if self.heuristics:
            prompt += "\nLEARNED PATTERNS AND HEURISTICS (Apply these strictly based on past experience):\n"
            for h in self.heuristics:
                prompt += f"- {h}\n"
        
        prompt += """
OUTPUT SPECIFICATION:
You MUST return a valid JSON object ONLY. Do not include any conversational text, explanations, or thinking blocks before or after the JSON.

Schema: 
{ 
    "expression": str, 
    "thesis": str, 
    "recommended_settings": { 
        "universe": str, 
        "decay": int, 
        "truncation": float, 
        "neutralization": str, 
        "lookback": int 
    } 
}
"""
        return prompt

    def build_mining_prompt(self, region: str, universe: str) -> str:
        """Generates a prompt incorporating current state and historical knowledge."""
        prompt_lines = [f"Design a high-performing alpha for {region}:{universe}."]
        
        if self.winning_alphas:
            prompt_lines.append("\nHISTORICAL REFERENCE (Patterns that previously worked):")
            for winner in self.winning_alphas[:5]:
                prompt_lines.append(f"- {winner}")
            
        if self.failed_expressions:
            prompt_lines.append("\nFAILED EXPRESSIONS (Do not repeat these exact structures):")
            for fail in self.failed_expressions[:5]:
                prompt_lines.append(f"- {fail}")
            
        if self.fields:
            prompt_lines.append(f"\nDATA CONTEXT (Sample of {min(len(self.fields), 30)} fields):")
            sampled_fields = random.sample(self.fields, min(len(self.fields), 30))
            for field in sampled_fields:
                desc = field.get('description', 'No description available').replace('\n', ' ')
                prompt_lines.append(f"- {field['id']}: {desc}")

        if self.operators:
            prompt_lines.append(f"\nOPERATOR CATALOG (Sample of {min(len(self.operators), 20)} operators):")
            sampled_operators = random.sample(self.operators, min(len(self.operators), 20))
            for op in sampled_operators:
                name = op.get('name', 'Unknown')
                desc = op.get('description', 'No description available').replace('\n', ' ')
                prompt_lines.append(f"- {name}: {desc}")
            
        return "\n".join(prompt_lines)

    @property
    def system_prompt(self) -> str:
        return self._get_dynamic_system_prompt()
