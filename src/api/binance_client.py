import os
import pandas as pd
from binance.client import Client
from binance.exceptions import BinanceAPIException
from dotenv import load_dotenv
from src.utils.logger import app_logger

load_dotenv()

class BinanceClientWrapper:
    def __init__(self, api_key=None, api_secret=None, testnet=False):
        self.api_key = api_key or os.getenv('BINANCE_API_KEY')
        self.api_secret = api_secret or os.getenv('BINANCE_API_SECRET')
        
        try:
            self.client = Client(self.api_key, self.api_secret, testnet=testnet)
            # Basic connectivity test
            self.client.ping()
            app_logger.info("Successfully connected to Binance API.")
        except (BinanceAPIException, ConnectionError, Exception) as e:
            self.client = None # Set to None to handle gracefully elsewhere
            app_logger.error(f"⚠️ PROSOFT GATEWAY WARNING: Could not connect to Binance. Check Internet/VPN. Error: {e}")
            # We don't raise here so the dashboard can still start
            if "getaddrinfo failed" in str(e):
                app_logger.error("💡 TIP: This looks like a DNS/Connection issue. Try connecting to a VPN.")

    def get_historical_klines(self, symbol, interval, limit=500):
        """Fetches historical OHLCV data."""
        if not self.client: return None
        try:
            klines = self.client.get_klines(symbol=symbol, interval=interval, limit=limit)
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            # Convert to numeric
            numeric_cols = ['open', 'high', 'low', 'close', 'volume']
            df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric)
            
            # Format timestamp
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return df
        except BinanceAPIException as e:
            app_logger.error(f"Binance API Error fetching klines for {symbol}: {e}")
            return None
        except Exception as e:
            app_logger.error(f"Error fetching klines for {symbol}: {e}")
            return None

    def get_account_balance(self, asset='USDT', include_locked=False):
        """Fetches account balance for a specific asset (Spot + Funding)."""
        if not self.client: return 0.0
        total = 0.0
        try:
            # 1. Check Spot
            spot_balance = self.client.get_asset_balance(asset=asset)
            if spot_balance:
                total += float(spot_balance['free'])
                if include_locked:
                    total += float(spot_balance['locked'])
            
            # 2. Check Funding (SAPI)
            try:
                funding_assets = self.client.get_funding_asset()
                for f in funding_assets:
                    if f['asset'] == asset:
                        total += float(f['free'])
                        # Note: Funding assets usually don't have 'locked' in the same way spot does
            except Exception as e:
                # Funding API might be restricted or throw error on some accounts
                pass
                
            return total
        except Exception as e:
            app_logger.error(f"Error fetching aggregate balance for {asset}: {e}")
            return total

    def get_all_balances(self):
        """Fetches all non-zero account balances (Spot + Funding)."""
        if not self.client: return []
        try:
            # 1. Fetch Spot Balances
            account = self.client.get_account()
            spot_balances = [
                {'asset': b['asset'], 'free': b['free'], 'locked': b['locked'], 'source': 'SPOT'} 
                for b in account['balances'] if float(b['free']) > 0 or float(b['locked']) > 0
            ]
            
            # 2. Fetch Funding Balances
            try:
                funding_raw = self.client.get_funding_asset()
                funding_balances = [
                    {'asset': f['asset'], 'free': f['free'], 'locked': f.get('freeze', 0), 'source': 'FUNDING'}
                    for f in funding_raw if float(f['free']) > 0 or float(f.get('freeze', 0)) > 0
                ]
            except:
                funding_balances = []
                
            return spot_balances + funding_balances
        except Exception as e:
            app_logger.error(f"Error fetching all balances (Spot+Funding): {e}")
            return []

    def get_symbol_ticker(self, symbol):
        """Fetches the latest price for a symbol."""
        if not self.client: return None
        try:
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        except Exception as e:
            app_logger.error(f"Error fetching ticker for {symbol}: {e}")
            return None

    def convert_dust_to_bnb(self, assets):
        """Phase 3: Dust-to-Gold - Converts small balances to BNB with recursion/fallback."""
        if not self.client: return False
        if not assets: return True
        
        try:
            # 1. Try joining as a string if it's a list (some API versions prefer this)
            asset_str = ",".join(assets) if isinstance(assets, list) else assets
            self.client.transfer_dust(asset=asset_str)
            app_logger.info(f"✨ [DUST-TO-GOLD] Successfully converted {len(assets)} assets to BNB.")
            return True
        except Exception as e:
            # 2. Fallback: If bulk fails (illegal parameter?), try one by one to find the culprit
            if len(assets) > 1:
                app_logger.warning(f"⚠️ Dust Bulk failed ({e}), attempting individual conversion...")
                success_count = 0
                for a in assets:
                    try:
                        self.client.transfer_dust(asset=a)
                        success_count += 1
                    except: pass
                return success_count > 0
            
            app_logger.error(f"Dust Conversion Error: {e}")
            return False

    def get_simple_earn_rewards(self, asset='USDT', limit=10):
        """Phase 12.0: Fetches interest rewards from Flexible Simple Earn."""
        if not self.client: return []
        try:
            # Check for both singular and plural method names (compatibility with different python-binance versions)
            methods = ['get_simple_earn_flexible_reward_history', 'get_simple_earn_flexible_rewards_history']
            for method_name in methods:
                if hasattr(self.client, method_name):
                    rewards = getattr(self.client, method_name)(asset=asset, size=limit)
                    return rewards.get('rows', [])
            return []
        except Exception as e:
            app_logger.error(f"Error fetching Simple Earn Rewards: {e}")
            return []

    async def get_funding_fee_history(self, limit=10):
        """Phase 12.0: Fetches Funding Fee history from Futures account."""
        if not self.client: return []
        try:
            # SAPI endpoint for Futures Income History (checks for FUNDING_FEE type)
            # Use loop.run_in_executor if calling a sync method from async context if needed, 
            # but binance-python client is usually used sync in this project's structure.
            income = self.client.futures_income_history(incomeType="FUNDING_FEE", limit=limit)
            return income
        except Exception as e:
            app_logger.error(f"Error fetching Funding Fees: {e}")
            return []

    def simple_earn_subscribe(self, asset, amount):
        """Subscribes asset to Flexible Simple Earn."""
        if not self.client: return False
        try:
            if hasattr(self.client, 'simple_earn_flexible_subscribe'):
                res = self.client.simple_earn_flexible_subscribe(productId=f"{asset}001", amount=amount)
                return True
            return False
        except Exception as e:
            app_logger.error(f"Simple Earn Subscribe Error: {e}")
            return False

    def simple_earn_redeem(self, asset, amount=None):
        """Redeems asset from Flexible Simple Earn."""
        if not self.client: return False
        try:
            if hasattr(self.client, 'simple_earn_flexible_redeem'):
                res = self.client.simple_earn_flexible_redeem(productId=f"{asset}001", amount=amount)
                return True
            return False
        except Exception as e:
            app_logger.error(f"Simple Earn Redeem Error: {e}")
            return False
