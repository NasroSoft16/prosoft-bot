import sqlite3
import pandas as pd
import os
from src.utils.logger import app_logger

class StrategyOptimizer:
    """PROSOFT AI: The Scientist - Self-Refactoring Strategy Logic."""
    
    def __init__(self, db_path="brain.db"):
        self.db_path = db_path
        
    def run_optimization_cycle(self):
        """Analyzes memory and updates strategy parameters for maximum efficiency."""
        try:
            conn = sqlite3.connect(self.db_path)
            query = "SELECT * FROM trade_memory ORDER BY id DESC LIMIT 100"
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            if df.empty or len(df) < 5:
                app_logger.info("🧠 [STRATEGY OPTIMIZER] Insufficient data to start refactoring (Need at least 5 trades).")
                return None
            
            # Analyze Win Rate
            wins = df[df['profit_loss'] > 0]
            losses = df[df['profit_loss'] <= 0]
            win_rate = len(wins) / len(df)
            
            app_logger.info(f"🧠 [STRATEGY OPTIMIZER] Current Session Win Rate: {win_rate:.2%}")
            
            # 1. AI Confidence Threshold Optimization
            # If win rate is low, increase the required confidence
            if win_rate < 0.6 and len(df) > 10:
                current_threshold = float(os.getenv('AI_CONFIDENCE_THRESHOLD', 0.55))
                new_threshold = min(0.85, current_threshold + 0.05)
                # Note: We can't easily write back to .env from here in a clean way without a helper
                app_logger.warning(f"🧠 [STRATEGY OPTIMIZER] Low win rate detected. Recommending AI Confidence increase: {current_threshold} -> {new_threshold}")
                # For now, let's just log the recommendation. In a real 'Money Machine', we'd update variables.
                return {"type": "ADJUST_THRESHOLD", "value": new_threshold}

            # 2. Market Health Correlation
            avg_health_wins = wins['market_health'].mean() if not wins.empty else 0
            avg_health_losses = losses['market_health'].mean() if not losses.empty else 0
            
            if avg_health_losses > avg_health_wins:
                app_logger.info(f"🧠 [STRATEGY OPTIMIZER] Optimization Insight: Losses occur at higher market health ({avg_health_losses:.1f}%) than wins ({avg_health_wins:.1f}%). Logic adjustment required.")

            return {"win_rate": win_rate, "total_trades": len(df)}
            
        except Exception as e:
            app_logger.error(f"Optimization Cycle Error: {e}")
            return None
