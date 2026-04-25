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
        self.profit_target_pct  = 0.007   # 0.7%
        self.stop_loss_pct      = 0.0015  # 0.15%
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

            # ── Extra fields for Wick Trap (Condition 5) ──
            curr_open    = float(curr.get('open',        close))
            curr_high    = float(curr.get('high',        close))
            curr_low     = float(curr.get('low',         close))
            curr_vol     = float(curr.get('volume',      0))
            vol_sma      = float(curr.get('VOLUME_SMA',  max(curr_vol, 1)))

            # Pre-compute candle geometry
            candle_range = curr_high - curr_low
            lower_wick   = close - curr_low
            candle_body  = abs(close - curr_open)
            wick_ratio   = (lower_wick   / candle_range) if candle_range > 0 else 0
            body_ratio   = (candle_body  / candle_range) if candle_range > 0 else 0
            vol_surge_wt = curr_vol > vol_sma * 1.8    if vol_sma > 0 else False

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

            # ── Condition 5: Long Lower Wick Rejection (Wick Trap) ──
            # ذيل سفلي طويل + إغلاق قوي + حجم = رفض السعر المنخفض → ارتداد سريع
            elif (wick_ratio   >= 0.55              # الذيل > 55% من النطاق الكلي
                  and body_ratio  <= 0.30              # جسم صغير = رفض قوي
                  and close > (curr_low + candle_range * 0.50)  # إغلاق فوق المنتصف
                  and vol_surge_wt                    # حجم تداول يؤكد الرفض
                  and rsi < 62):                      # ليس في منطقة الإرهاق
                reason = "Wick Trap"
                conf   = 0.80

            if not reason:
                return None

            # Dynamic TP/SL using ATR if available
            if atr > 0:
                # Volatility scaling: Snatch profit when volatility expands
                volatility_pct = atr / close
                
                # Dynamic TP scales directly with volatility (Min 0.5%, Max 1.5%)
                dynamic_tp_pct = max(0.005, min(0.015, volatility_pct * 1.8))
                
                # Dynamic SL breathes with volatility but stays tight (Min 0.15%, Max 0.4%)
                dynamic_sl_pct = max(0.0015, min(0.004, volatility_pct * 0.8))
                
                tp_price = close * (1 + dynamic_tp_pct)
                sl_price = close * (1 - dynamic_sl_pct)
                
                app_logger.info(f"🌊 [WAVE RIDER] Dynamic Scalp - TP: {dynamic_tp_pct*100:.2f}% | SL: {dynamic_sl_pct*100:.2f}%")
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
