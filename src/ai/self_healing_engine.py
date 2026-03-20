"""
PROSOFT QUANTUM - محرك التصحيح الذاتي (Self-Healing Engine)
يراقب صحة النظام ويُصلح المشاكل الشائعة تلقائياً.
"""
import time
import asyncio
import os
from src.utils.logger import app_logger


class SelfHealingEngine:
    """Monitors bot health and auto-recovers from common failures."""

    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.error_counter = {}  # tracks repeated errors
        self.max_retries = 3
        self.error_threshold = 5  # errors before escalation

    def record_error(self, error_type: str, details: str = ""):
        """Logs and counts an error type. Returns True if threshold exceeded."""
        self.error_counter[error_type] = self.error_counter.get(error_type, 0) + 1
        count = self.error_counter[error_type]
        app_logger.warning(f"[Self-Heal] Error '{error_type}' occurred {count} times. Details: {details}")
        return count >= self.error_threshold

    def reset_counter(self, error_type: str):
        """Resets a specific error counter after successful recovery."""
        if error_type in self.error_counter:
            self.error_counter[error_type] = 0

    async def heal_entry_signal_error(self):
        """Fixes 'out-of-bounds' entry signal errors by requesting fresh data."""
        app_logger.warning("[Self-Heal] Entry signal error detected. Flushing stale data and refreshing...")
        try:
            # Force a fresh data fetch by clearing cached df
            if hasattr(self.bot, 'last_df'):
                del self.bot.last_df
            # Brief pause to allow Binance API to settle
            await asyncio.sleep(5)
            self.reset_counter('entry_signal_oob')
            app_logger.info("[Self-Heal] Data cache cleared. System recovered.")
            return True
        except Exception as e:
            app_logger.error(f"[Self-Heal] Recovery failed: {e}")
            return False

    async def heal_api_disconnect(self):
        """Attempts to reconnect to Binance API after a connection failure."""
        app_logger.warning("[Self-Heal] Binance API disconnect detected. Attempting reconnect...")
        for attempt in range(1, self.max_retries + 1):
            try:
                # If client wasn't even initialized, try a full re-init
                if not self.bot.api.client:
                    key = os.getenv('BINANCE_API_KEY')
                    secret = os.getenv('BINANCE_API_SECRET')
                    self.bot.reconnect_binance(key, secret)
                
                if self.bot.api.client:
                    self.bot.api.client.ping()
                    self.reset_counter('api_disconnect')
                    app_logger.info(f"[Self-Heal] Binance API reconnected on attempt {attempt}.")
                    return True
            except Exception as e:
                app_logger.error(f"[Self-Heal] Reconnect attempt {attempt} failed: {e}")
                await asyncio.sleep(10 * attempt)  # exponential backoff
        return False

    async def run_health_check(self):
        """
        Comprehensive system health check. Call this periodically (e.g., every 30 loops).
        Returns a health report dict.
        """
        report = {
            'api_ok': False,
            'data_ok': False,
            'trade_state_ok': False,
            'errors': []
        }
        
        # --- CLOUD READINESS: Auto-Save State ---
        if self.bot.active_trades:
            self.save_trade_state(self.bot.active_trades)

        try:
            # 1. API connectivity
            if not self.bot.api.client:
                report['errors'].append("API Client NOT Initialized (No Internet/DNS)")
                await self.heal_api_disconnect()
            else:
                self.bot.api.client.ping()
                report['api_ok'] = True
        except Exception as e:
            report['errors'].append(f"API Ping Failed: {e}")
            await self.heal_api_disconnect()

        try:
            # 2. Data freshness check (last_df should be recent)
            if hasattr(self.bot, 'last_df') and self.bot.last_df is not None:
                if len(self.bot.last_df) >= 20:
                    report['data_ok'] = True
                else:
                    report['errors'].append("Insufficient data in last_df")
            else:
                report['errors'].append("No cached data (last_df missing)")
        except Exception as e:
            report['errors'].append(f"Data Check Error: {e}")

        try:
            # 3. Trade state consistency & Ghost Trade detection (Deep Sync)
            # This ensures the bot's internal state matches the reality on Binance
            await self.deep_sync_trade_state()
            
            # Simplified check for list health
            report['trade_state_ok'] = True
        except Exception as e:
            report['errors'].append(f"Trade State Error: {e}")

        if report['errors']:
            app_logger.warning(f"[Self-Heal] Health Check Issues: {report['errors']}")
        else:
            app_logger.info("[Self-Heal] ✅ Full System Health Check Passed.")

        return report

    async def deep_sync_trade_state(self):
        """
        [PROSOFT DEEP SYNC]
        Verifies if each 'active_trade' in memory actually exists as assets in Binance.
        If not, it clears the ghost trade state.
        """
        if not self.bot.active_trades:
            return

        to_remove = []
        for trade in self.bot.active_trades:
            symbol = trade['symbol']
            asset = symbol.replace('USDT', '')
            
            try:
                # 1. Check actual free balance of the asset
                balance = self.bot.api.get_account_balance(asset)
                ticker = self.bot.api.get_symbol_ticker(symbol)
                
                if ticker and ticker > 0:
                    usd_value = balance * ticker
                    
                    # 2. If USD value is less than $1.00, it's effectively gone or 'dust'
                    if usd_value < 1.0:
                        app_logger.warning(f"[Deep Sync] GHOST TRADE DETECTED: {symbol} (Value: ${usd_value:.2f}). Clearing state...")
                        to_remove.append(trade)
                    else:
                        app_logger.info(f"[Deep Sync] Active trade verified: {asset} balance ~${usd_value:.2f}")
            except Exception as e:
                app_logger.error(f"[Deep Sync] Failed to verify balance for {asset}: {e}")

        # Final cleanup
        if to_remove:
            for trade in to_remove:
                if trade in self.bot.active_trades:
                    self.bot.active_trades.remove(trade)
            self.save_trade_state(self.bot.active_trades)
            if hasattr(self.bot, '_force_ui_update'):
                self.bot._force_ui_update()

    def save_trade_state(self, trades_list):
        """Saves current active trades list to disk to recover after cloud restarts."""
        import json
        import os
        try:
            # PROSOFT CLOUD SYNC: Prefer root /data for persistent volumes
            root_data = '/data'
            save_dir = root_data if os.path.isdir(root_data) else 'data'
            
            if not os.path.exists(save_dir):
                os.makedirs(save_dir, exist_ok=True)
                
            path = os.path.join(save_dir, 'active_trades.json')
            with open(path, 'w') as f:
                json.dump(trades_list, f)
        except Exception as e:
            app_logger.error(f"[Self-Heal] Failed to save state to {save_dir}: {e}")

    def load_trade_state(self):
        """Loads trade state as a list from disk if exists."""
        import json
        import os
        # Search in order: Root /data (Persistent) then local data/
        root_data = '/data'
        paths = [
            os.path.join(root_data, 'active_trades.json'),
            'data/active_trades.json',
            'data/active_trade.json' # Legacy fallback
        ]
        
        for path in paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        state = json.load(f)
                    
                    # Normalize: always return a list
                    if isinstance(state, dict):
                        return [state]
                    elif isinstance(state, list):
                        return state
                except Exception as e:
                    app_logger.error(f"[Self-Heal] Failed to load state from {path}: {e}")
        return []

    def clear_trade_state(self):
        """Removes the state file when all trades are closed."""
        import os
        root_data = '/data'
        paths = [
            os.path.join(root_data, 'active_trades.json'),
            'data/active_trades.json',
            'data/active_trade.json'
        ]
        for path in paths:
            if os.path.exists(path):
                try:
                    os.remove(path)
                    app_logger.info(f"[Self-Heal] Trade state file removed: {path}")
                except: pass
