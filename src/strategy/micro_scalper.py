"""
micro_scalper.py — PROSOFT Micro-Scalper v2
يعمل على الأطر القصيرة (1m / 5m) فقط عندما يكون السوق صحياً.
هدف: 0.4% – 0.8% ربح لكل صفقة بسرعة عالية.
"""

import pandas as pd
from src.utils.logger import app_logger
from datetime import datetime


class MicroScalper:
    def __init__(self, api_client, min_volume_usdt=300_000):
        self.api                = api_client
        self.min_volume_usdt    = min_volume_usdt
        self.profit_target_pct  = 0.006   # 0.6%
        self.stop_loss_pct      = 0.003   # 0.3%
        self.min_trade_amount   = 11.0    # Binance minimum

        # Stats for self-tuning
        self._scalp_wins   = 0
        self._scalp_losses = 0

    # ── Market scan ───────────────────────────────────────────────────────

    async def find_volatile_candidates(self, limit=8):
        """
        Finds USDT pairs with high volume AND significant recent move.
        Adds a liquidity filter to avoid manipulation-prone micro-caps.
        """
        try:
            info           = self.api.client.get_exchange_info()
            active_symbols = {
                s['symbol'] for s in info['symbols'] if s['status'] == 'TRADING'
            }

            tickers    = self.api.client.get_ticker()
            candidates = []

            for t in tickers:
                sym = t['symbol']
                if not sym.endswith('USDT') or sym not in active_symbols:
                    continue

                quote_volume     = float(t['quoteVolume'])
                price_change_pct = abs(float(t['priceChangePercent']))
                last_price       = float(t['lastPrice'])

                # Minimum liquidity AND minimum move
                if (quote_volume  > self.min_volume_usdt
                        and price_change_pct > 1.5
                        and last_price > 0.00001):          # filter dust coins
                    candidates.append({
                        'symbol':     sym,
                        'volatility': price_change_pct,
                        'volume':     quote_volume,
                        'price':      last_price,
                    })

            candidates.sort(key=lambda x: x['volatility'], reverse=True)
            return candidates[:limit]

        except Exception as e:
            app_logger.error(f"[SCALPER] Candidate scan error: {e}")
            return []

    # ── Signal check ──────────────────────────────────────────────────────

    def check_scalp_signal(self, df, symbol='ASSET'):
        """
        Four scalp entry conditions — first match wins.
        Requires EMA_20, EMA_50, RSI (calculated upstream).
        """
        if df is None or len(df) < 20:
            return None

        try:
            curr = df.iloc[-1]
            prev = df.iloc[-2]

            rsi       = float(curr.get('RSI',     50))
            rsi_prev  = float(prev.get('RSI',     50))
            close     = float(curr['close'])
            ema_20    = float(curr.get('EMA_20',  0))
            ema_50    = float(curr.get('EMA_50',  0))
            atr       = float(curr.get('ATR',     0))
            macd_hist = float(curr.get('MACD_HIST', 0))

            reason = None
            conf   = 0.0

            # ── Condition 1: RSI Bounce from oversold ──
            if rsi_prev < 38 and rsi > rsi_prev and close > ema_50:
                reason = "RSI Bounce"
                conf   = 0.82

            # ── Condition 2: Momentum Burst ──
            elif (close > ema_20 > ema_50
                  and 52 < rsi < 72
                  and macd_hist > 0):
                reason = "Momentum Burst"
                conf   = 0.78

            # ── Condition 3: MACD zero-line cross (bullish) ──
            elif (float(prev.get('MACD_HIST', 0)) < 0
                  and macd_hist > 0
                  and close > ema_50):
                reason = "MACD Cross"
                conf   = 0.75

            # ── Condition 4: Volume squeeze break ──
            elif (float(curr.get('BB_WIDTH', 1)) < 0.012
                  and close > ema_20
                  and rsi > 50):
                reason = "Squeeze Break"
                conf   = 0.76

            if not reason:
                return None

            # Dynamic TP/SL using ATR if available
            if atr > 0:
                tp_price = close * (1 + self.profit_target_pct) + atr * 0.5
                sl_price = close * (1 - self.stop_loss_pct)     - atr * 0.3
            else:
                tp_price = close * (1 + self.profit_target_pct)
                sl_price = close * (1 - self.stop_loss_pct)

            app_logger.info(
                f"⚡ [SCALPER] Signal on {symbol}: {reason} | "
                f"RSI={rsi:.1f} | conf={conf:.2f}"
            )
            return {
                'entry':      close,
                'tp':         tp_price,
                'sl':         sl_price,
                'confidence': conf,
                'reason':     reason,
            }

        except Exception as e:
            app_logger.error(f"[SCALPER] Signal check error: {e}")
            return None

    # ── Self-tuning ────────────────────────────────────────────────────────

    def record_result(self, won: bool):
        if won:
            self._scalp_wins   += 1
        else:
            self._scalp_losses += 1

    @property
    def win_rate(self):
        total = self._scalp_wins + self._scalp_losses
        return self._scalp_wins / total if total > 0 else 0.5

    def should_be_active(self, market_health: float, timeframe: str) -> bool:
        """
        MicroScalper should only run on short TFs with healthy market.
        Gate: TF ∈ {1m, 5m} AND health > 55 AND (no model or winrate > 45%).
        """
        if timeframe not in ('1m', '5m'):
            return False
        if market_health < 55:
            return False
        total = self._scalp_wins + self._scalp_losses
        if total >= 10 and self.win_rate < 0.40:
            app_logger.warning(
                f"[SCALPER] Auto-disabled: win rate {self.win_rate:.1%} < 40%"
            )
            return False
        return True
