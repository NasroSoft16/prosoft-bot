import sqlite3
import pandas as pd
import shutil
import os
import numpy as np
from datetime import datetime
from src.utils.logger import app_logger


class NeuralMemory:
    """
    PROSOFT Self-Learning Database.
    Stores trade history, learns from mistakes, vetoes repeated failures.
    """

    def __init__(self, db_path=None):
        self.db_path = db_path or os.environ.get("DB_PATH", "brain.db")
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        
        # Diagnostic Log
        app_logger.info(f"🧠 NEURAL MEMORY: Persistent storage active at {os.path.abspath(self.db_path)}")
        self._initialize_db()

    # ── Schema ────────────────────────────────────────────────────────────

    def _initialize_db(self):
        try:
            conn   = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trade_memory (
                    id             INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol         TEXT,
                    side           TEXT,
                    entry_price    REAL,
                    exit_price     REAL,
                    profit_loss    REAL,
                    ai_confidence  REAL,
                    market_health  REAL,
                    sentiment      TEXT,
                    entry_time     TEXT,
                    exit_time      TEXT,
                    lesson_learned TEXT,
                    strategy_used  TEXT
                )
            """)

            # --- AUTO MIGRATION LOGIC ---
            # Check for missing columns and add them to prevent DB insert failures
            cursor.execute("PRAGMA table_info(trade_memory)")
            columns = [info[1] for info in cursor.fetchall()]
            
            missing_cols = {
                'entry_time': 'TEXT',
                'exit_time': 'TEXT',
                'strategy_used': 'TEXT'
            }
            
            for col, col_type in missing_cols.items():
                if col not in columns:
                    app_logger.info(f"💾 DATABASE MIGRATION: Adding missing column {col} to trade_memory")
                    try:
                        cursor.execute(f"ALTER TABLE trade_memory ADD COLUMN {col} {col_type}")
                    except Exception as alt_err:
                        app_logger.warning(f"Migration for {col} failed: {alt_err}")

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS revenue_memory (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    source    TEXT,
                    asset     TEXT,
                    amount    REAL,
                    details   TEXT,
                    timestamp TEXT
                )
            """)
            # Index for fast symbol lookups
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_trade_symbol ON trade_memory(symbol)"
            )
            conn.commit()
            conn.close()
            app_logger.info("Neural Memory (SQLite) initialised.")
        except Exception as e:
            app_logger.error(f"DB Init Error: {e}")

    # ── Logging ───────────────────────────────────────────────────────────

    def log_trade(self, symbol, side, entry, exit_p,
                  entry_t, exit_t, pnl, conf, health, sentiment,
                  strategy_used=''):
        try:
            lesson = (
                "POSITIVE: Pattern reinforced."
                if pnl > 0
                else "NEGATIVE: False signal — reduce weight for this pattern."
            )
            conn   = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO trade_memory
                (symbol, side, entry_price, exit_price, entry_time, exit_time,
                 profit_loss, ai_confidence, market_health, sentiment,
                 lesson_learned, strategy_used)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """, (symbol, side, entry, exit_p, entry_t, exit_t,
                  pnl, conf, health, sentiment, lesson, strategy_used))
            conn.commit()
            trade_id = cursor.lastrowid
            conn.close()
            app_logger.info(
                f"💾 [TRADE #{trade_id}] {symbol} | PnL: {pnl:+.4f} | {strategy_used}"
            )
        except Exception as e:
            app_logger.error(f"DB Insert Error: {e}")

    def log_revenue(self, source, asset, amount, details=''):
        try:
            conn   = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO revenue_memory (source,asset,amount,details,timestamp) VALUES (?,?,?,?,?)",
                (source, asset, amount, details, datetime.now().isoformat())
            )
            conn.commit()
            conn.close()
        except Exception as e:
            app_logger.error(f"Revenue log error: {e}")

    # ── Smart veto ────────────────────────────────────────────────────────

    def should_veto_trade(self, symbol: str, current_market_health: float) -> tuple:
        """
        Returns (veto: bool, reason: str).
        Vetoes a trade if past failures on this symbol happened at
        similar or higher market health conditions.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            df   = pd.read_sql_query(
                """
                SELECT profit_loss, market_health FROM trade_memory
                WHERE symbol=? AND profit_loss < 0
                ORDER BY id DESC LIMIT 8
                """,
                conn, params=(symbol,)
            )
            conn.close()

            if df.empty or len(df) < 1:
                return False, ""

            avg_loss_health = float(df['market_health'].mean())

            # Veto if losses typically happen at health HIGHER than current
            # i.e., the market looks good but historically we lose here
            if (avg_loss_health < current_market_health + 12
                    and len(df) >= 4):
                reason = (
                    f"MEMORY VETO: {symbol} lost {len(df)}× "
                    f"when health≈{avg_loss_health:.0f}% "
                    f"(current={current_market_health:.0f}%)"
                )
                app_logger.warning(f"🧠 {reason}")
                return True, reason

            return False, ""

        except Exception as e:
            app_logger.error(f"Veto check error: {e}")
            return False, ""

    def analyze_past_mistakes(self, symbol: str) -> str:
        try:
            conn = sqlite3.connect(self.db_path)
            df   = pd.read_sql_query(
                "SELECT * FROM trade_memory WHERE symbol=? AND profit_loss < 0 "
                "ORDER BY id DESC LIMIT 5",
                conn, params=(symbol,)
            )
            conn.close()
            if not df.empty:
                avg_health = df['market_health'].mean()
                return (
                    f"Warning: {len(df)} recent losses on {symbol} "
                    f"when market_health≈{avg_health:.0f}%."
                )
            return "Historical data clean."
        except Exception:
            return "System optimal."

    # ── Stats ─────────────────────────────────────────────────────────────

    def get_recent_memories(self, limit=10):
        try:
            conn = sqlite3.connect(self.db_path)
            df   = pd.read_sql_query(
                f"SELECT * FROM trade_memory ORDER BY id DESC LIMIT {limit}", conn
            )
            conn.close()
            return df.replace({np.nan: None, np.inf: None, -np.inf: None}).to_dict('records')
        except Exception:
            return []

    def get_total_revenue(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(amount) FROM revenue_memory")
            total = cursor.fetchone()[0] or 0.0
            conn.close()
            return float(total)
        except Exception:
            return 0.0

    def get_revenue_totals(self):
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query("SELECT source, amount FROM revenue_memory", conn)
            conn.close()
            
            mapping = {
                "YieldFarmer": "yield_total",
                "ListingSniper": "sniper_hits",
                "FundingArb": "funding_total"
            }
            
            res = {"yield_total": 0.0, "sniper_hits": 0, "funding_total": 0.0}
            if not df.empty:
                for src, key in mapping.items():
                    sub = df[df['source'] == src]
                    if key == "sniper_hits":
                        res[key] = len(sub)
                    else:
                        res[key] = float(sub['amount'].sum())
            return res
        except Exception:
            return {"yield_total": 0.0, "sniper_hits": 0, "funding_total": 0.0}

    def get_daily_report_data(self):
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            conn = sqlite3.connect(self.db_path)
            # Use SQLite date function to filter by today (assuming ISO format timestamp)
            rev_df = pd.read_sql_query(
                "SELECT source, SUM(amount) as total FROM revenue_memory WHERE timestamp LIKE ? GROUP BY source",
                conn, params=(f"{today}%",)
            )
            conn.close()
            
            return {
                'revenue': rev_df.replace({np.nan: None, np.inf: None, -np.inf: None}).to_dict('records') if not rev_df.empty else []
            }
        except Exception:
            return None

    def get_today_detailed_trades(self):
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(
                "SELECT * FROM trade_memory WHERE exit_time LIKE ? ORDER BY id DESC",
                conn, params=(f"{today}%",)
            )
            conn.close()
            # FIX: Ensure JSON compliance by replacing NaN/Infinity with None (null)
            df = df.replace({np.nan: None, np.inf: None, -np.inf: None})
            return df.to_dict('records') if not df.empty else []
        except Exception:
            return []

    def get_revenue_history(self, limit=20):
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(f"SELECT * FROM revenue_memory ORDER BY id DESC LIMIT {limit}", conn)
            conn.close()
            return df.replace({np.nan: None, np.inf: None, -np.inf: None}).to_dict('records')
        except Exception:
            return []

    def backup(self, backup_path='data/brain_backup.db'):
        try:
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            shutil.copy2(self.db_path, backup_path)
            app_logger.info(f"Brain DB backed up → {backup_path}")
        except Exception as e:
            app_logger.error(f"Backup failed: {e}")
