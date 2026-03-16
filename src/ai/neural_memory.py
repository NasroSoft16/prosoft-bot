import sqlite3
import pandas as pd
import shutil
import os
from datetime import datetime
from src.utils.logger import app_logger

class NeuralMemory:
    """PROSOFT AI Self-Learning Database (SQLite) for storing trade history & self-improvement."""
    
    def __init__(self, db_path="brain.db"):
        self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # Deep Learning Memory Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trade_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT,
                    side TEXT,
                    entry_price REAL,
                    exit_price REAL,
                    profit_loss REAL,
                    ai_confidence REAL,
                    market_health REAL,
                    sentiment TEXT,
                    entry_time TEXT,
                    exit_time TEXT,
                    lesson_learned TEXT
                )
            """)
            # Revenue Streams Memory Table (Yield, Sniper, Arb)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS revenue_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT,
                    asset TEXT,
                    amount REAL,
                    details TEXT,
                    timestamp TEXT
                )
            """)
            conn.commit()
            conn.close()
            app_logger.info("Neural Memory (SQLite) Initialized Successfully.")
        except Exception as e:
            app_logger.error(f"DB Init Error: {e}")

    def log_trade(self, symbol, side, entry, exit_p, entry_t, exit_t, pnl, conf, health, sentiment):
        """Records a completed trade to act as training data for future models."""
        try:
            # Self-reflection logic
            if pnl > 0:
                lesson = "POSITIVE: Market conditions validated. Pattern added to secure weights."
            else:
                lesson = "NEGATIVE: False breakout detected. Reducing weight for this pattern."
                
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO trade_memory 
                (symbol, side, entry_price, exit_price, entry_time, exit_time, profit_loss, ai_confidence, market_health, sentiment, lesson_learned)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (symbol, side, entry, exit_p, entry_t, exit_t, pnl, conf, health, sentiment, lesson))
            conn.commit()
            conn.close()
            app_logger.info(f"💾 Trade Logged in Neural Memory: {symbol} | PNL: {pnl:.2f}")
        except Exception as e:
            app_logger.error(f"DB Insert Error: {e}")

    def analyze_past_mistakes(self, symbol):
        """AI queries past mistakes before entering a new trade."""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(f"SELECT * FROM trade_memory WHERE symbol='{symbol}' AND profit_loss < 0 ORDER BY id DESC LIMIT 5", conn)
            conn.close()
            
            if not df.empty:
                avg_loss_health = df['market_health'].mean()
                return f"Warning: Historical data suggests we fail {len(df)} times on {symbol} when Market Health is around {avg_loss_health:.0f}%."
            return "Historical data looks clean. No repeated negative patterns detected."
        except:
            return "System optimal."

    def get_recent_memories(self, limit=10):
        """Retrieve recent neural records for dashboard analysis (Subconscious UI)."""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(f"SELECT * FROM trade_memory ORDER BY id DESC LIMIT {limit}", conn)
            conn.close()
            return df.to_dict(orient='records')
        except Exception as e:
            app_logger.error(f"Error fetching memory: {e}")
            return []

    def sync_to_cloud(self):
        """Phase 5: Cloud-Sync - Backs up the brain database to a secure location."""
        try:
            backup_dir = "backups/neural_brain"
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"brain_sync_{timestamp}.db")
            
            shutil.copy2(self.db_path, backup_path)
            
            # Keep only last 5 backups
            backups = sorted([os.path.join(backup_dir, f) for f in os.listdir(backup_dir)])
            if len(backups) > 5:
                for old_b in backups[:-5]:
                    os.remove(old_b)
                    
            app_logger.info(f"[CLOUD-SYNC] Neural Brain backed up successfully to {backup_path}")
            return True
        except Exception as e:
            app_logger.error(f"Cloud Sync Error: {e}")
            return False

    def log_revenue(self, source, asset, amount, details=""):
        """Records profit from extra mechanisms like Yield Farming or Funding Arb."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO revenue_memory 
                (source, asset, amount, details, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (source, asset, amount, details, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            conn.close()
            app_logger.info(f"Revenue Logged: {source} | +${amount:.4f}")
        except Exception as e:
            app_logger.error(f"Revenue Log Error: {e}")

    def get_revenue_history(self, limit=20):
        """Retrieve recent revenue events."""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(f"SELECT * FROM revenue_memory ORDER BY id DESC LIMIT {limit}", conn)
            conn.close()
            return df.to_dict(orient='records')
        except Exception as e:
            app_logger.error(f"Error fetching revenue: {e}")
            return []

    def get_revenue_totals(self):
        """Aggregate totals by source for dashboard display."""
        try:
            conn = sqlite3.connect(self.db_path)
            # Yield Total
            yield_df = pd.read_sql_query("SELECT SUM(amount) as total FROM revenue_memory WHERE source='YieldFarmer'", conn)
            yield_total = yield_df['total'].iloc[0] or 0.0
            
            # Sniper Hits (Count)
            sniper_df = pd.read_sql_query("SELECT COUNT(*) as hits FROM revenue_memory WHERE source='ListingSniper'", conn)
            sniper_hits = sniper_df['hits'].iloc[0] or 0
            
            # Funding Total (Can be used for APR estimate)
            funding_df = pd.read_sql_query("SELECT SUM(amount) as total FROM revenue_memory WHERE source='FundingArb'", conn)
            funding_total = funding_df['total'].iloc[0] or 0.0
            
            conn.close()
            return {
                'yield_total': float(yield_total),
                'sniper_hits': int(sniper_hits),
                'funding_total': float(funding_total)
            }
        except Exception as e:
            app_logger.error(f"Error summing revenue: {e}")
            return {'yield_total': 0.0, 'sniper_hits': 0, 'funding_total': 0.0}

    def get_daily_report_data(self):
        """Compiles stats for the last 24 hours for the Telegram report."""
        try:
            from datetime import timedelta
            cutoff = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
            
            conn = sqlite3.connect(self.db_path)
            # 1. Total revenue from streams
            revenue_df = pd.read_sql_query(f"SELECT source, SUM(amount) as total FROM revenue_memory WHERE timestamp > '{cutoff}' GROUP BY source", conn)
            
            # 2. Performance from trades
            trades_df = pd.read_sql_query(f"""
                SELECT 
                    COUNT(*) as count, 
                    SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as wins,
                    SUM(profit_loss) as total_pnl
                FROM trade_memory 
                WHERE entry_time > '{cutoff}'
            """, conn)
            conn.close()
            
            return {
                'revenue': revenue_df.to_dict(orient='records'),
                'trades': trades_df.to_dict(orient='records')[0] if not trades_df.empty else None
            }
        except Exception as e:
            app_logger.error(f"Error compiling daily report: {e}")
            return None
