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
        if self.bot.active_trade:
            self.save_trade_state(self.bot.active_trade)

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
            
            if self.bot.active_trade is not None:
                t = self.bot.active_trade
                if all(k in t for k in ['symbol', 'entry_price', 'sl', 'tp', 'qty']):
                    report['trade_state_ok'] = True
                else:
                    report['errors'].append("Active trade object is malformed — resetting.")
                    self.bot.active_trade = None
            else:
                report['trade_state_ok'] = True  # No trade is also a valid state
        except Exception as e:
            report['errors'].append(f"Trade State Error: {e}")
            self.bot.active_trade = None

        if report['errors']:
            app_logger.warning(f"[Self-Heal] Health Check Issues: {report['errors']}")
        else:
            app_logger.info("[Self-Heal] ✅ Full System Health Check Passed.")

        return report

    async def deep_sync_trade_state(self):
        """
        [PROSOFT DEEP SYNC]
        Verifies if the 'active_trade' in memory actually exists as assets in Binance.
        If not, it clears the ghost trade state.
        """
        if not self.bot.active_trade:
            return

        trade = self.bot.active_trade
        symbol = trade['symbol']
        asset = symbol.replace('USDT', '')
        
        try:
            # 1. Check actual free balance of the asset
            balance = self.bot.api.get_account_balance(asset)
            ticker = self.bot.api.get_symbol_ticker(symbol)
            
            if ticker and ticker > 0:
                usd_value = balance * ticker
                
                # 2. If USD value is less than $1.00, it's effectively gone or 'dust'
                # Binance minimum trade is $10, so $1 is a safe 'non-existent' threshold
                if usd_value < 1.0:
                    app_logger.warning(f"[Deep Sync] GHOST TRADE DETECTED: {symbol} (Value: ${usd_value:.2f}). Clearing state...")
                    self.bot.active_trade = None
                    self.clear_trade_state()
                    # Trigger UI update
                    if hasattr(self.bot, '_force_ui_update'):
                        self.bot._force_ui_update()
                else:
                    app_logger.info(f"[Deep Sync] Active trade verified: {asset} balance ~${usd_value:.2f}")
        except Exception as e:
            app_logger.error(f"[Deep Sync] Failed to verify balance for {asset}: {e}")

    def save_trade_state(self, trade_data):
        """Saves active trade to disk to recover after cloud restarts."""
        import json
        try:
            with open('data/active_trade.json', 'w') as f:
                json.dump(trade_data, f)
        except Exception as e:
            app_logger.error(f"[Self-Heal] Failed to save state: {e}")

    def load_trade_state(self):
        """Loads trade state from disk if exists."""
        import json
        import os
        path = 'data/active_trade.json'
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    state = json.load(f)
                app_logger.info(f"[Self-Heal] 💾 Cloud Recovery: Found active trade for {state['symbol']}. Restoring...")
                # Verify if still valid on Binance (optional but good)
                return state
            except Exception as e:
                app_logger.error(f"[Self-Heal] Failed to load state: {e}")
                return None
        return None

    def clear_trade_state(self):
        """Removes the state file when a trade is closed."""
        import os
        path = 'data/active_trade.json'
        if os.path.exists(path):
            try:
                os.remove(path)
                app_logger.info("[Self-Heal] Trade state cleared.")
            except: pass
