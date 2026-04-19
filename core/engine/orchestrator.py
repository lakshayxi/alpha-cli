import time
import logging
from typing import List, Dict, Any, Optional
from rich.console import Console
from alpha_cli.core.llm.client import LLMClient, LLMError
from alpha_cli.core.llm.prompt import PromptBuilder
from alpha_cli.core.brain.simulator import BrainSimulator, SimulationError
from alpha_cli.core.brain.fetcher import BrainFetcher
from alpha_cli.core.brain.models import SimulationResult
from alpha_cli.core.validation.syntax import SyntaxValidator
from alpha_cli.core.validation.semantic import SemanticValidator
from alpha_cli.core.validation.corrector import AlphaCorrector
from alpha_cli.core.engine.decision import DecisionEngine, Action
from alpha_cli.core.engine.optimizer import SettingsOptimizer
from alpha_cli.core.storage.db import DatabaseManager
from alpha_cli.core.storage.cache import ExpressionCache
from alpha_cli.core.storage.memory import PatternAnalyzer

logger = logging.getLogger(__name__)

class MiningOrchestrator:
    """
    Coordinates the discovery pipeline with an integrated reflective learning loop.
    Simulates human observation by analyzing historical data to synthesize heuristics.
    """
    
    def __init__(self, llm_client: LLMClient, simulator: BrainSimulator, fetcher: BrainFetcher, db: DatabaseManager):
        self.llm = llm_client
        self.simulator = simulator
        self.fetcher = fetcher
        self.db = db
        self.console = Console()
        
        # Core discovery and validation components
        self.prompt_builder = PromptBuilder()
        self.syntax_val = SyntaxValidator()
        self.semantic_val = SemanticValidator()
        self.corrector = AlphaCorrector()
        self.decision_engine = DecisionEngine()
        self.optimizer = SettingsOptimizer()
        self.cache = ExpressionCache()
        
        # Reflective Memory components
        self.pattern_analyzer = PatternAnalyzer(db)

    def prepare_context(self, region: str, universe: str) -> None:
        """Synchronizes context from remote APIs and internal reflective memory."""
        with self.console.status("[bold blue]Synthesizing historical patterns and market data...[/bold blue]"):
            operators = self.fetcher.fetch_operators()
            fields = self.fetcher.fetch_data_fields(region, universe)
            
            # Retrieve learned heuristics and patterns
            winners = self.db.get_winning_alphas()
            failed = self.db.get_failed_expressions()
            heuristics = self.db.get_active_heuristics()
            
            self.prompt_builder.set_context(operators, fields, winners, failed, heuristics)

    def run_iteration(self, region: str, universe: str) -> None:
        """Executes a single mining cycle with post-execution reflection."""
        
        prompt = self.prompt_builder.build_mining_prompt(region, universe)
        try:
            with self.console.status("[bold cyan]Consulting memory and LLM for strategy...[/bold cyan]"):
                gen_alpha = self.llm.generate_alpha(prompt, self.prompt_builder.system_prompt)
        except LLMError as e:
            self.console.print(f"[red]LLM error: {e}[/red]")
            return

        expression = gen_alpha.expression
        settings = gen_alpha.recommended_settings.dict()
        
        self.console.print(f"\n[bold]Hypothesis:[/bold] {gen_alpha.thesis}")
        self.console.print(f"[bold]Expression:[/bold] {expression}")

        if self.cache.contains(expression):
            self.console.print("[yellow]Redundant pattern. Skipping simulation.[/yellow]")
            return
        self.cache.add(expression)

        # Apply surgical corrections
        expression, swap_fixes = self.corrector.swap_event_operators(expression)
        if swap_fixes:
            self.console.print(f"[yellow]Auto-correcting for event field compatibility: {swap_fixes}[/yellow]")

        current_opt_attempt = 0
        while current_opt_attempt <= 3:
            try:
                with self.console.status(f"[bold magenta]Simulation effort {current_opt_attempt}...[/bold magenta]"):
                    sim_url = self.simulator.submit_simulation(expression, settings)
                    sim_data = self.simulator.poll_simulation(sim_url)
                
                # Determine error category for learning
                error_cat = self._categorize_error(sim_data)
                sim_result = self._process_simulation_response(expression, sim_data, region, universe, settings)
                
                # Persist simulation telemetry with categorized errors
                if current_opt_attempt == 0:
                    self.db.store_alpha(sim_result.alpha_id, expression, gen_alpha.thesis, self.llm.provider)
                self.db.store_simulation(sim_result.alpha_id, sim_result, error_category=error_cat)

                if sim_result.status != "COMPLETE":
                    fixed_expr, count_fixes = self.corrector.fix_input_count_error(expression, sim_result.error_message or "")
                    if count_fixes:
                        self.console.print(f"[yellow]Surgically repaired parameter mismatch: {count_fixes}[/yellow]")
                        expression = fixed_expr
                        continue
                    break

                action = self.decision_engine.decide(sim_result)
                self._report_metrics(sim_result, action)

                if action == Action.PUSH: break
                elif action == Action.ITERATE and current_opt_attempt < 3:
                    current_opt_attempt += 1
                    settings = self.optimizer.optimize(settings, current_opt_attempt)
                elif action == Action.FLIP and current_opt_attempt == 0:
                    expression = f"-({expression})"
                    current_opt_attempt += 1
                else: break

            except SimulationError as e:
                self.console.print(f"[red]Simulation system error: {e}[/red]")
                break
        
        # REFLECTION PHASE: System updates its heuristics based on the latest result
        self.pattern_analyzer.synthesize_learnings()

    def _categorize_error(self, data: Dict) -> Optional[str]:
        """Categorizes API errors for systemic pattern observation."""
        status = data.get('status')
        msg = data.get('message', '').lower()
        
        if status in ['FAILED', 'ERROR', 'FAIL']:
            if 'event input' in msg: return "EVENT_INCOMPATIBILITY"
            if 'number of inputs' in msg: return "PARAMETER_MISMATCH"
            if 'lookback' in msg: return "PARAMETER_MISMATCH"
            return "UNKNOWN_FAILURE"
        return None

    def _process_simulation_response(self, expression: str, data: Dict, region: str, universe: str, settings: Dict) -> SimulationResult:
        alpha_id = data.get('alpha', '')
        if not alpha_id and 'alpha' in data: alpha_id = str(data['alpha'])
        
        if data.get('status') == 'COMPLETE' and alpha_id:
            details = self.simulator.get_alpha_details(alpha_id)
            is_data = details.get('is', {})
            return SimulationResult(
                alpha_id=alpha_id, expression=expression, region=region, universe=universe,
                sharpe=is_data.get('sharpe', 0.0), fitness=is_data.get('fitness', 0.0),
                turnover=is_data.get('turnover', 0.0), returns=is_data.get('returns', 0.0),
                drawdown=is_data.get('drawdown', 0.0), status="COMPLETE", settings=settings, timestamp=time.time()
            )
        
        return SimulationResult(
            alpha_id=alpha_id or "failed_submission", expression=expression, region=region, universe=universe,
            status=data.get('status', 'FAILED'), error_message=data.get('message', 'Unknown error state.'),
            settings=settings, timestamp=time.time()
        )

    def _report_metrics(self, result: SimulationResult, action: Action) -> None:
        metrics = f"Sharpe: {result.sharpe:.2f} | Fitness: {result.fitness:.2f}"
        style = "green" if action == Action.PUSH else "yellow" if action == Action.ITERATE else "red"
        self.console.print(f"[{style}]Reflective Evaluation: {metrics} | Result: {action.value}[/{style}]")
