from src.utils.logger import app_logger

class PortfolioManager:
    def __init__(self, api_wrapper):
        self.api = api_wrapper
        self.portfolio_data = []
        self.total_value_usdt = 0.0

    def update_portfolio(self):
        """Calculates total portfolio value and individual asset distribution."""
        try:
            balances = self.api.get_all_balances()
            if not balances:
                app_logger.warning("No assets found in Binance account or API keys have no permissions.")
                return []
            
            app_logger.info(f"Syncing Portfolio: Found {len(balances)} assets.")

            detailed_portfolio = []
            total_usdt = 0.0

            # Aggregate assets (handles same asset in Spot + Funding)
            aggregated = {}
            for b in balances:
                asset = b['asset']
                free = float(b['free'])
                locked = float(b['locked'])
                total_qty = free + locked
                aggregated[asset] = aggregated.get(asset, 0) + total_qty

            detailed_portfolio = []
            total_usdt = 0.0

            for asset, total_qty in aggregated.items():
                if asset == 'USDT':
                    value_usdt = total_qty
                else:
                    price = self.api.get_symbol_ticker(f"{asset}USDT")
                    value_usdt = total_qty * price if price else 0.0

                if value_usdt > 0.1: # Threshold to ignore dust
                    detailed_portfolio.append({
                        'asset': asset,
                        'qty': total_qty,
                        'value_usdt': value_usdt
                    })
                    total_usdt += value_usdt

            # Calculate percentages
            for item in detailed_portfolio:
                item['percentage'] = (item['value_usdt'] / total_usdt * 100) if total_usdt > 0 else 0

            self.portfolio_data = sorted(detailed_portfolio, key=lambda x: x['value_usdt'], reverse=True)
            self.total_value_usdt = total_usdt
            return self.portfolio_data
        except Exception as e:
            app_logger.error(f"Portfolio Update Error: {e}")
            return []

    def check_risk_alerts(self):
        """Analyzes portfolio for critical risk exposures."""
        alerts = []
        try:
            # 1. Concentration Risk (Max 30% per non-USDT asset)
            for item in self.portfolio_data:
                if item['asset'] != 'USDT' and item['percentage'] > 30:
                    alerts.append(f"⚠️ HIGH EXPOSURE: {item['asset']} is {item['percentage']:.1f}% of portfolio. Consider rebalancing.")
            
            # 2. Diversification Check
            if len(self.portfolio_data) < 3:
                alerts.append("ℹ️ LOW DIVERSIFICATION: Portfolio holds very few assets.")
                
            return alerts
        except Exception as e:
            app_logger.error(f"Risk Shield Error: {e}")
            return []

    def get_summary(self):
        return {
            'total_value': self.total_value_usdt,
            'assets': self.portfolio_data,
            'alerts': self.check_risk_alerts()
        }
