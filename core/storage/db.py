import sqlite3
import time
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from alpha_cli.core.brain.models import SimulationResult

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Manages persistent storage for alpha discovery.
    Includes advanced telemetry for self-learning, including failure signatures 
    and performance motifs.
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        if not db_path:
            db_path = Path.home() / ".alpha-cli" / "alpha_mining.db"
        
        self.db_path = db_path
        self._initialize_schema()

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _initialize_schema(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Core expression storage
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS alphas (
                        id TEXT PRIMARY KEY,
                        expression TEXT UNIQUE,
                        thesis TEXT,
                        provider TEXT,
                        created_at REAL
                    )
                ''')
                
                # Performance and API telemetry
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS simulations (
                        alpha_id TEXT,
                        simulation_id TEXT PRIMARY KEY,
                        region TEXT,
                        universe TEXT,
                        sharpe REAL,
                        fitness REAL,
                        turnover REAL,
                        returns REAL,
                        drawdown REAL,
                        status TEXT,
                        error_category TEXT,
                        error_message TEXT,
                        settings_json TEXT,
                        timestamp REAL,
                        FOREIGN KEY(alpha_id) REFERENCES alphas(id)
                    )
                ''')
                
                # Learned Heuristics: Stores summarized patterns observed by the system
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learned_heuristics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        heuristic_type TEXT, -- 'SUCCESS_PATTERN', 'FAILURE_PATTERN', 'FIELD_PREFERENCE'
                        content TEXT,
                        confidence_score REAL,
                        last_updated REAL
                    )
                ''')
                
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Schema initialization failure: {e}")

    def store_simulation(self, alpha_id: str, sim_result: SimulationResult, error_category: Optional[str] = None) -> None:
        """Records simulation metrics with optional failure categorization for learning."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO simulations 
                    (alpha_id, simulation_id, region, universe, sharpe, fitness, turnover, returns, drawdown, status, error_category, error_message, settings_json, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    alpha_id,
                    sim_result.alpha_id,
                    sim_result.region,
                    sim_result.universe,
                    sim_result.sharpe,
                    sim_result.fitness,
                    sim_result.turnover,
                    sim_result.returns,
                    sim_result.drawdown,
                    sim_result.status,
                    error_category,
                    sim_result.error_message,
                    json.dumps(sim_result.settings),
                    sim_result.timestamp
                ))
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Failed to persist simulation telemetry: {e}")

    def get_performance_insights(self) -> Dict[str, Any]:
        """Retrieves raw data for pattern analysis."""
        insights = {
            "top_performers": [],
            "frequent_errors": [],
            "successful_fields": []
        }
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Top 10 successful expressions
                cursor.execute('''
                    SELECT a.expression, s.sharpe, s.fitness 
                    FROM alphas a JOIN simulations s ON a.id = s.alpha_id 
                    WHERE s.status = 'COMPLETE' AND s.sharpe > 1.0 
                    ORDER BY s.sharpe DESC LIMIT 10
                ''')
                insights["top_performers"] = cursor.fetchall()
                
                # Error distribution
                cursor.execute('''
                    SELECT error_category, COUNT(*) as count 
                    FROM simulations 
                    WHERE status != 'COMPLETE' AND error_category IS NOT NULL
                    GROUP BY error_category ORDER BY count DESC
                ''')
                insights["frequent_errors"] = cursor.fetchall()
                
            return insights
        except sqlite3.Error as e:
            logger.error(f"Insight retrieval failure: {e}")
            return insights

    def store_heuristic(self, h_type: str, content: str, confidence: float) -> None:
        """Stores a synthesized insight for use in future prompts."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO learned_heuristics (heuristic_type, content, confidence_score, last_updated)
                    VALUES (?, ?, ?, ?)
                ''', (h_type, content, confidence, time.time()))
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Heuristic storage failure: {e}")

    def get_active_heuristics(self) -> List[str]:
        """Retrieves highly confident learned patterns."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT content FROM learned_heuristics 
                    WHERE confidence_score > 0.7 
                    ORDER BY last_updated DESC LIMIT 5
                ''')
                return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Heuristic retrieval failure: {e}")
            return []
            
    # Keep existing helper methods (store_alpha, get_winning_alphas, etc.) with similar cleanup
    def store_alpha(self, alpha_id: str, expression: str, thesis: str, provider: str) -> None:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT OR IGNORE INTO alphas VALUES (?, ?, ?, ?, ?)', 
                             (alpha_id, expression, thesis, provider, time.time()))
                conn.commit()
        except sqlite3.Error: pass

    def get_winning_alphas(self) -> List[str]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT a.expression FROM alphas a JOIN simulations s ON a.id = s.alpha_id WHERE s.sharpe >= 1.25')
                return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error: return []

    def get_failed_expressions(self) -> List[str]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT expression FROM alphas a JOIN simulations s ON a.id = s.alpha_id WHERE s.status != "COMPLETE"')
                return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error: return []

    def get_all_results(self) -> List[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT a.expression, s.* FROM simulations s JOIN alphas a ON s.alpha_id = a.id ORDER BY s.timestamp DESC')
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error: return []
