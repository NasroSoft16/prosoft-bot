import sqlite3
import pandas as pd
import os
from src.utils.logger import app_logger


class StrategyOptimizer:
    """
    PROSOFT AI: Self-Refactoring Strategy Engine.
    Analyses win/loss history and APPLIES parameter changes — not just logs them.
    """

    def __init__(self, db_path=None):
        self.db_path = db_path or os.environ.get("DB_PATH", "brain.db")
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        # Live parameters that get updated by the optimizer
        self.ai_confidence_threshold = float(os.getenv('AI_CONFIDENCE_THRESHOLD', 0.55))
        self.tp_multiplier           = float(os.getenv('ATR_TP_MULTIPLIER',       5.0))
        self.sl_multiplier           = float(os.getenv('ATR_SL_MULTIPLIER',       2.2))
        self.max_concurrent_trades   = int(os.getenv('MAX_CONCURRENT_TRADES',     3))

    # ── Main optimization cycle ────────────────────────────────────────────

    def run_optimization_cycle(self, bot_instance=None):
        """
        Analyse last 100 trades and apply parameter changes immediately.
        Pass bot_instance so we can update its live thresholds.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            df   = pd.read_sql_query(
                "SELECT * FROM trade_memory ORDER BY id DESC LIMIT 100", conn
            )
            conn.close()
        except Exception as e:
            app_logger.error(f"[OPTIMIZER] DB read error: {e}")
            return None

        if df.empty or len(df) < 5:
            app_logger.info("🧠 [OPTIMIZER] Not enough trades yet (need ≥ 5).")
            return None

        wins     = df[df['profit_loss'] > 0]
        losses   = df[df['profit_loss'] <= 0]
        win_rate = len(wins) / len(df)

        app_logger.info(f"🧠 [OPTIMIZER] Win rate: {win_rate:.2%} over {len(df)} trades")

        changes = {}

        # ── Rule 1: AI confidence threshold ──────────────────────────────
        if win_rate < 0.55 and len(df) >= 10:
            new_thresh = min(0.82, self.ai_confidence_threshold + 0.04)
            self.ai_confidence_threshold = new_thresh
            if bot_instance and hasattr(bot_instance, 'ai_confidence_threshold'):
                bot_instance.ai_confidence_threshold = new_thresh
            app_logger.warning(
                f"🧠 [OPTIMIZER] ✅ APPLIED: confidence threshold → {new_thresh:.2f}"
            )
            changes['confidence_threshold'] = new_thresh

        elif win_rate > 0.72 and self.ai_confidence_threshold > 0.50:
            # Good win rate — can relax threshold slightly for more trades
            new_thresh = max(0.50, self.ai_confidence_threshold - 0.02)
            self.ai_confidence_threshold = new_thresh
            if bot_instance and hasattr(bot_instance, 'ai_confidence_threshold'):
                bot_instance.ai_confidence_threshold = new_thresh
            app_logger.info(
                f"🧠 [OPTIMIZER] ✅ APPLIED: relaxing threshold → {new_thresh:.2f}"
            )
            changes['confidence_threshold'] = new_thresh

        # ── Rule 2: TP multiplier vs average profit per win ───────────────
        if not wins.empty:
            avg_win_pnl  = wins['profit_loss'].mean()
            avg_loss_pnl = losses['profit_loss'].mean() if not losses.empty else 0

            if avg_loss_pnl != 0:
                rr_ratio = abs(avg_win_pnl / avg_loss_pnl)
                if rr_ratio < 1.5 and self.tp_multiplier < 7.0:
                    # Losses bigger than wins: push TP further
                    self.tp_multiplier = min(7.0, self.tp_multiplier + 0.3)
                    if bot_instance and hasattr(bot_instance, 'strategy'):
                        bot_instance.strategy.atr_multiplier_tp = self.tp_multiplier
                    app_logger.warning(
                        f"🧠 [OPTIMIZER] ✅ APPLIED: TP multiplier → {self.tp_multiplier:.1f}"
                    )
                    changes['tp_multiplier'] = self.tp_multiplier

        # ── Rule 3: Market health correlation ────────────────────────────
        if not wins.empty and not losses.empty and 'market_health' in df.columns:
            avg_health_wins   = wins['market_health'].mean()
            avg_health_losses = losses['market_health'].mean()
            if avg_health_losses > avg_health_wins + 10:
                app_logger.info(
                    f"🧠 [OPTIMIZER] Insight: losses occur at market health "
                    f"{avg_health_losses:.0f}% vs wins at {avg_health_wins:.0f}%. "
                    f"Consider raising market health entry gate."
                )
                changes['market_health_warning'] = True
                if bot_instance and hasattr(bot_instance, 'min_market_health'):
                    bot_instance.min_market_health = min(55, avg_health_wins + 5)

        # ── Rule 4: Consecutive losses → reduce position sizing ───────────
        recent_10 = df.head(10)['profit_loss'].tolist()
        consec_losses = 0
        for pnl in recent_10:
            if pnl <= 0:
                consec_losses += 1
            else:
                break

        if consec_losses >= 4:
            if bot_instance and hasattr(bot_instance, 'risk_manager'):
                bot_instance.risk_manager.risk_per_trade = max(
                    0.005, bot_instance.risk_manager.risk_per_trade * 0.75
                )
            app_logger.warning(
                f"🧠 [OPTIMIZER] ⚠️ {consec_losses} consecutive losses detected. "
                f"Position size reduced by 25%."
            )
            changes['position_size_reduced'] = True

        return {
            "win_rate":   win_rate,
            "total_trades": len(df),
            "changes_applied": changes
        }

    # ── Weekly deep review ────────────────────────────────────────────────

    def generate_weekly_review(self, bot_instance=None):
        """
        Reviews weekly performance, identifies toxic assets,
        and optionally adds them to the bot's blacklist.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            df   = pd.read_sql_query(
                "SELECT symbol, profit_loss FROM trade_memory ORDER BY id DESC LIMIT 500",
                conn
            )
            conn.close()
        except Exception as e:
            app_logger.error(f"[OPTIMIZER] Weekly review DB error: {e}")
            return None

        if df.empty or len(df) < 10:
            return None

        sym_stats = (
            df.groupby('symbol')['profit_loss']
            .agg(['count', 'sum', lambda x: (x > 0).mean()])
            .reset_index()
        )
        sym_stats.columns = ['symbol', 'trade_count', 'total_pnl', 'win_rate']

        # Toxic: ≥3 trades AND win rate < 30%
        toxic_assets = sym_stats[
            (sym_stats['trade_count'] >= 3) & (sym_stats['win_rate'] < 0.30)
        ]['symbol'].tolist()

        pnl_total    = df['profit_loss'].sum()
        win_rate_all = (df['profit_loss'] > 0).mean()
        best_asset   = sym_stats.nlargest(1, 'total_pnl')['symbol'].values[0] \
                       if not sym_stats.empty else "N/A"
        worst_asset  = sym_stats.nsmallest(1, 'total_pnl')['symbol'].values[0] \
                       if not sym_stats.empty else "N/A"

        # Auto-blacklist toxic assets
        if toxic_assets and bot_instance:
            for asset in toxic_assets:
                token = asset.replace('USDT', '')
                if hasattr(bot_instance, 'blacklist') and token not in bot_instance.blacklist:
                    bot_instance.blacklist.append(token)
                    app_logger.warning(
                        f"🧠 [WEEKLY REVIEW] Auto-blacklisted toxic asset: {token} "
                        f"(added to BLACKLISTED_COINS)"
                    )

        report = {
            'total_pnl':    pnl_total,
            'win_rate':     win_rate_all * 100,
            'toxic_assets': toxic_assets,
            'best_asset':   best_asset,
            'worst_asset':  worst_asset,
        }
        app_logger.info(
            f"📊 [WEEKLY REVIEW] PnL: {pnl_total:.2f} | Win rate: {win_rate_all:.1%} | "
            f"Toxic: {toxic_assets} | Best: {best_asset} | Worst: {worst_asset}"
        )
        return report
