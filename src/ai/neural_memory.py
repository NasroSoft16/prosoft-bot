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
                    strategy_used  TEXT,
                    highest_peak   REAL
                )
            """)
            
            # --- PHASE 4: PAPER TRADES TABLE ---
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS paper_trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT,
                    status TEXT,
                    timestamp TEXT
                )
            """)

            # --- AUTO MIGRATION LOGIC ---
            # Check for missing columns and add them to prevent DB insert failures
            cursor.execute("PRAGMA table_info(trade_memory)")
            columns = [info[1] for info in cursor.fetchall()]
            
            missing_cols = {
                'entry_time': 'TEXT',
                'exit_time': 'TEXT',
                'strategy_used': 'TEXT',
                'highest_peak': 'REAL'
            }
            
            for col, col_type in missing_cols.items():
                if col not in columns:
                    app_logger.info(f"💾 DATABASE MIGRATION: Adding missing column {col} to trade_memory")
                    try:
                        cursor.execute(f"ALTER TABLE trade_memory ADD COLUMN {col} {col_type}")
                    except Exception as alt_err:
                        app_logger.warning(f"Migration for {col} failed: {alt_err}")
            
            # --- PAPER TRADES MIGRATION LOGIC ---
            cursor.execute("PRAGMA table_info(paper_trades)")
            paper_cols = [info[1] for info in cursor.fetchall()]
            paper_missing_cols = {
                'side': 'TEXT',
                'entry_price': 'REAL',
                'exit_price': 'REAL',
                'profit_loss': 'REAL',
                'market_health': 'REAL',
                'ai_confidence': 'REAL'
            }
            for col, col_type in paper_missing_cols.items():
                if col not in paper_cols:
                    app_logger.info(f"💾 DATABASE MIGRATION: Adding missing column {col} to paper_trades")
                    try:
                        cursor.execute(f"ALTER TABLE paper_trades ADD COLUMN {col} {col_type}")
                    except: pass

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
                  strategy_used='', highest_peak=0.0):
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
                 lesson_learned, strategy_used, highest_peak)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (symbol, side, entry, exit_p, entry_t, exit_t,
                  pnl, conf, health, sentiment, lesson, strategy_used, highest_peak))
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
        Vetoes a trade if past failures on this symbol happened recently
        at similar or higher market health conditions.
        --- NEURAL FORGIVENESS (v31.0) ---
        If the last failure was more than 12 hours ago, the "Grudge" is lifted.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            # Fetch last 8 losses with their exit times
            df   = pd.read_sql_query(
                """
                SELECT id, profit_loss, market_health, exit_time FROM trade_memory
                WHERE symbol=? AND profit_loss < 0
                ORDER BY id DESC LIMIT 8
                """,
                conn, params=(symbol,)
            )

            if df.empty or len(df) < 1:
                conn.close()
                return False, ""

            # --- PHASE 4: ACTIVE NEURAL FORGIVENESS (PAPER TRADING) ---
            df_paper = pd.read_sql_query(
                "SELECT status FROM paper_trades WHERE symbol=? ORDER BY id DESC LIMIT 3",
                conn, params=(symbol,)
            )
            # If the last 3 virtual trades were WIN, lift the grudge!
            if len(df_paper) == 3 and (df_paper['status'] == 'WIN').all():
                cursor = conn.cursor()
                cursor.execute("DELETE FROM paper_trades WHERE symbol=?", (symbol,))
                conn.commit()
                conn.close()
                return False, ""

            # --- TIME-DECAY FORGIVENESS ---
            # Check if the MOST RECENT loss is older than 12 hours
            try:
                last_loss_time_str = df['exit_time'].iloc[0]
                if last_loss_time_str:
                    # Clean the string for parsing (Binance likes 2026-04-01T12:00:00.000)
                    dt_str = last_loss_time_str.split('.')[0].replace('T', ' ')
                    last_loss_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                    hours_since_last_fail = (datetime.now() - last_loss_dt).total_seconds() / 3600
                    
                    # If last failure was > 12 hours ago, forgive the coin (Give it a fresh start)
                    if hours_since_last_fail > 12.0:
                        app_logger.info(f"🧊 [FORGIVENESS] {symbol} last failed {hours_since_last_fail:.1f}h ago. Veto lifted.")
                        conn.close()
                        return False, ""
            except Exception as time_err:
                app_logger.warning(f"Forgiveness time parse error: {time_err}")

            # --- TRADITIONAL HEALTH VETO ---
            avg_loss_health = float(df['market_health'].mean())
            health_diff = current_market_health - avg_loss_health
            
            # If current health is MUCH BETTER (e.g. +20%), we forgive even if recent
            if health_diff > 20.0:
                app_logger.info(f"🌟 [RECOVERY VETO] {symbol} forgiven because Market Health improved by {health_diff:+.0f}%")
                conn.close()
                return False, ""

            # If conditions are similar or worse AND we lost 2+ times recently
            conditions_similar_or_worse = health_diff <= 10.0
            if conditions_similar_or_worse and len(df) >= 2:
                reason = (
                    f"NEURAL GRUDGE: {symbol} failed {len(df)}× recently "
                    f"at health≈{avg_loss_health:.0f}% "
                    f"(current={current_market_health:.0f}%)"
                )
                app_logger.warning(f"🧠 {reason}")
                conn.close()
                return True, reason

            conn.close()
            return False, ""

        except Exception as e:
            app_logger.error(f"Veto check error: {e}")
            return False, ""

    def record_paper_trade(self, symbol: str, is_win: bool, trade_data: dict = None):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            status = 'WIN' if is_win else 'LOSS'
            
            if trade_data:
                cursor.execute(
                    """INSERT INTO paper_trades 
                       (symbol, status, timestamp, side, entry_price, exit_price, profit_loss, market_health, ai_confidence) 
                       VALUES (?,?,?,?,?,?,?,?,?)""",
                    (
                        symbol, 
                        status, 
                        datetime.now().isoformat(),
                        trade_data.get('side', 'BUY'),
                        trade_data.get('entry_price', 0.0),
                        trade_data.get('exit_price', 0.0),
                        trade_data.get('profit_loss', 0.0),
                        trade_data.get('market_health', 0.0),
                        trade_data.get('ai_confidence', 0.0)
                    )
                )
            else:
                cursor.execute(
                    "INSERT INTO paper_trades (symbol, status, timestamp) VALUES (?,?,?)",
                    (symbol, status, datetime.now().isoformat())
                )
            conn.commit()
            conn.close()
        except Exception as e:
            app_logger.error(f"Paper trade log error: {e}")

    def get_paper_trades_report(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # Fetch the last 3 paper trades for each unique symbol that has been paper traded
            cursor.execute("SELECT DISTINCT symbol FROM paper_trades")
            symbols = [row[0] for row in cursor.fetchall()]
            
            report = []
            for sym in symbols:
                cursor.execute(
                    "SELECT status FROM paper_trades WHERE symbol=? ORDER BY id DESC LIMIT 3",
                    (sym,)
                )
                statuses = [row[0] for row in cursor.fetchall()]
                wins = statuses.count('WIN')
                
                # The requirement to unban is 3 consecutive wins or 3 wins out of last 3.
                # In should_veto_trade we unban if the last 3 are WIN.
                if len(statuses) == 3 and all(s == 'WIN' for s in statuses):
                    state = "READY TO UNBAN"
                else:
                    needed = 3 - wins
                    state = f"TRAINING (Needs {needed} more wins)"
                    
                report.append({
                    "symbol": sym,
                    "last_status": statuses[0] if statuses else "UNKNOWN",
                    "wins_in_last_3": wins,
                    "state": state
                })
            conn.close()
            return report
        except Exception as e:
            app_logger.error(f"Error fetching paper trades report: {e}")
            return []

    def analyze_past_mistakes(self, symbol: str) -> str:
        try:
            conn = sqlite3.connect(self.db_path)
            # Real losses
            df = pd.read_sql_query(
                "SELECT * FROM trade_memory WHERE symbol=? AND profit_loss < 0 ORDER BY id DESC LIMIT 5",
                conn, params=(symbol,)
            )
            # Simulated losses
            try:
                sim_df = pd.read_sql_query(
                    "SELECT * FROM paper_trades WHERE symbol=? AND status='LOSS' ORDER BY id DESC LIMIT 5",
                    conn, params=(symbol,)
                )
            except Exception:
                sim_df = pd.DataFrame()
                
            conn.close()
            
            warning_msg = ""
            if not df.empty:
                avg_health = df['market_health'].mean()
                warning_msg += f"Warning: {len(df)} recent real losses on {symbol} when market_health≈{avg_health:.0f}%. "
                
            if not sim_df.empty:
                # To prevent errors if the migration hasn't run yet, check if market_health exists
                if 'market_health' in sim_df.columns and not sim_df['market_health'].isnull().all():
                    avg_sim_health = sim_df['market_health'].mean()
                    warning_msg += f"[SIMULATION WARNING] The AI recently suffered {len(sim_df)} virtual losses on this coin under market_health≈{avg_sim_health:.0f}%. Proceed with extreme caution and learn from these simulated patterns. "
                else:
                    warning_msg += f"[SIMULATION WARNING] The AI recently suffered {len(sim_df)} virtual losses on this coin. Proceed with extreme caution. "

            if warning_msg:
                return warning_msg.strip()
                
            return "Historical data clean."
        except Exception:
            return "System optimal."

    # ── Meme Lab Analytics ────────────────────────────────────────────────────────
    
    def get_meme_lab_report(self):
        """
        Fetches detailed analytics comparing EARLY_IGNITION vs previous methods.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            # Fetch all trades to compute lab stats
            df = pd.read_sql_query("SELECT symbol, profit_loss, entry_price, strategy_used, exit_time FROM trade_memory ORDER BY id DESC", conn)
            conn.close()
            
            if df.empty:
                return {"status": "No data"}
            
            # v2: EARLY_IGNITION
            df_v2 = df[df['strategy_used'] == 'EARLY_IGNITION']
            v2_total = len(df_v2)
            v2_wins = len(df_v2[df_v2['profit_loss'] > 0])
            v2_winrate = (v2_wins / v2_total * 100) if v2_total > 0 else 0.0
            v2_avg = df_v2['profit_loss'].mean() if v2_total > 0 else 0.0
            
            # v1: anything else (quantum alpha, empty, etc) treated as general benchmark
            df_v1 = df[df['strategy_used'] != 'EARLY_IGNITION']
            v1_total = len(df_v1)
            v1_wins = len(df_v1[df_v1['profit_loss'] > 0])
            v1_winrate = (v1_wins / v1_total * 100) if v1_total > 0 else 0.0
            v1_avg = df_v1['profit_loss'].mean() if v1_total > 0 else 0.0

            # Last 5 Early Ignition trades
            last_5 = df_v2.head(5).to_dict('records')

            return {
                "v2": {
                    "total": v2_total,
                    "win_rate": v2_winrate,
                    "avg_pnl": float(v2_avg) if not pd.isna(v2_avg) else 0.0
                },
                "v1": {
                    "total": v1_total,
                    "win_rate": v1_winrate,
                    "avg_pnl": float(v1_avg) if not pd.isna(v1_avg) else 0.0
                },
                "last_5": [
                    {
                        "symbol": t['symbol'], 
                        "pnl": float(t['profit_loss']) if not pd.isna(t['profit_loss']) else 0.0,
                        "time": t['exit_time']
                    } 
                    for t in last_5
                ]
            }
        except Exception as e:
            app_logger.error(f"Meme Lab Report Error: {e}")
            return {"error": str(e)}

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
