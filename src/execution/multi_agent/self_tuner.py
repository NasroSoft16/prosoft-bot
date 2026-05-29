import asyncio
import time
import sqlite3
from src.utils.logger import app_logger

class SelfTunerAgent:
    """
    PROSOFT SWARM: Self-Tuner Agent.
    Background worker that periodically inspects historical results in brain.db
    and dynamically overrides strategy thresholds to maximize overall profitability.
    """
    def __init__(self, bot, shared_state):
        self.bot = bot
        self.state = shared_state
        self.is_running = False
        self.poll_interval = 3600  # Optimize parameters once per hour
        
    async def start(self):
        self.is_running = True
        asyncio.create_task(self._run_loop())
        app_logger.info("🧠 Self-Tuner Agent (Parameter-Optimizer) STARTED successfully.")
        
    async def stop(self):
        self.is_running = False
        
    async def _run_loop(self):
        while self.is_running:
            try:
                # 1. Connect to local/live db
                db_path = self.bot.memory.db_path
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Fetch recent trades count and winrate
                cursor.execute("SELECT COUNT(*), SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) FROM trade_memory;")
                row = cursor.fetchone()
                
                if row and row[0] >= 10:
                    total_trades = row[0]
                    wins = row[1] or 0
                    win_rate = wins / total_trades
                    
                    # 2. Dynamic tuning rule:
                    # If winrate is low (< 45%), raise entry thresholds!
                    if win_rate < 0.45:
                        app_logger.info(f"🧠 [SELF-TUNER] Low winrate detected ({win_rate:.1%}). Raising safety targets dynamically.")
                        self.bot.min_market_health = 48.0  # Tighten macro gate
                        if hasattr(self.bot, 'micro_scalper'):
                            self.bot.micro_scalper.profit_target_pct = 0.009  # Take larger profit
                    else:
                        self.bot.min_market_health = 45.0  # Normal gate
                        
                conn.close()
                
            except Exception as e:
                app_logger.error(f"[SELF-TUNER ERROR] Param optimization failed: {e}")
                
            await asyncio.sleep(self.poll_interval)
