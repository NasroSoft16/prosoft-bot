"""
PROSOFT QUANTUM - مصفوفة التنويع (Diversification Matrix)
يوزع رأس المال بذكاء عبر أصول متعددة لتقليل المخاطر.
"""
from src.utils.logger import app_logger


class DiversificationMatrix:
    """
    Manages capital allocation across multiple assets to reduce single-asset risk.
    Ensures no single coin takes more than a defined percentage of the portfolio.
    """

    def __init__(self, max_concentration_pct=40.0, min_usdt_reserve_pct=20.0):
        """
        max_concentration_pct: Max % of portfolio in any ONE asset (default 40%).
        min_usdt_reserve_pct: Always keep this % as USDT cash reserve (default 20%).
        """
        self.max_concentration = max_concentration_pct / 100.0
        self.min_usdt_reserve = min_usdt_reserve_pct / 100.0

    def get_safe_allocation(self, symbol, usdt_balance, total_equity):
        """
        Calculates the maximum safe amount (USDT) to allocate to a new trade,
        respecting diversification rules.
        Returns: float (max USDT to risk in this trade)
        """
        try:
            if total_equity <= 0:
                return usdt_balance * 0.95

            # --- MICRO-ACCOUNT BYPASS (< $100) ---
            # Diversification rules only make sense for larger accounts.
            # For micro-accounts, allow up to 95% of balance per trade.
            if total_equity < 100:
                safe_allocation = usdt_balance * 0.95
                app_logger.info(
                    f"[Diversification Matrix] Micro-account mode (${total_equity:.2f}): "
                    f"Bypassing concentration limits. Safe allocation: ${safe_allocation:.2f}"
                )
                return max(0.0, safe_allocation)

            # Rule 1: Min USDT reserve — always keep this cash available
            reserved_usdt = total_equity * self.min_usdt_reserve
            available_usdt = max(0, usdt_balance - reserved_usdt)

            # Rule 2: No single trade > max_concentration of total equity
            max_by_concentration = total_equity * self.max_concentration

            # Final allocation is the smaller of the two constraints
            safe_allocation = min(available_usdt, max_by_concentration)

            app_logger.info(
                f"[Diversification Matrix] {symbol} — "
                f"Available: ${available_usdt:.2f}, Max by concentration: ${max_by_concentration:.2f}, "
                f"Safe allocation: ${safe_allocation:.2f}"
            )
            return max(0.0, safe_allocation)

        except Exception as e:
            app_logger.error(f"Diversification Matrix Error: {e}")
            return 0.0


    def check_concentration_risk(self, portfolio_assets: list, total_equity: float) -> list:
        """
        Reviews the current portfolio for over-concentration.
        Returns a list of warning strings for any asset exceeding the limit.
        """
        warnings = []
        if not portfolio_assets or total_equity <= 0:
            return warnings

        for asset in portfolio_assets:
            concentration = asset.get('value_usdt', 0) / total_equity
            if asset['asset'] != 'USDT' and concentration > self.max_concentration:
                warnings.append(
                    f"⚠️ OVER-CONCENTRATED: {asset['asset']} is {concentration*100:.1f}% of portfolio "
                    f"(max allowed: {self.max_concentration*100:.0f}%). Consider partial profit-taking."
                )
        return warnings
