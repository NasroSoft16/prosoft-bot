import os
import sys
import asyncio
from dotenv import load_dotenv

# Add libs to path
sys.path.append(os.getcwd())

async def check_permissions():
    print("--- PROSOFT API DIAGNOSTICS ---")
    load_dotenv()
    
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    
    if not api_key or not api_secret:
        print("❌ ERROR: API keys not found in .env file.")
        return

    try:
        from binance.client import Client
        client = Client(api_key, api_secret)
        
        # 1. Basic Connection
        client.ping()
        print("✅ Connection: Binance Link Stable.")
        
        # 2. Permissions Check
        info = client.get_api_key_permissions()
        print("\n--- API Restrictions Checked ---")
        print(f"Reading: {'✅' if info['enableReading'] else '❌'}")
        print(f"Spot Trading: {'✅' if info['enableSpotAndMarginTrading'] else '❌'}")
        print(f"Futures: {'✅' if info.get('enableFutures', False) else '❌'}")
        print(f"Universal Transfer: {'✅' if info.get('permitsUniversalTransfer', False) else '❌'}")
        
        # 3. Yield Farming (Simple Earn) Check
        print("\n--- Feature Readiness ---")
        try:
            # Try to fetch current USDT earn position
            positions = client.simple_earn_flexible_position(asset='USDT')
            print("✅ Simple Earn: Accessible.")
        except Exception as e:
            if "API key does not have permission" in str(e):
                print("❌ Simple Earn: Permission Denied (Needs Universal Transfer + Accepted Terms).")
            else:
                print(f"⚠️ Simple Earn: {e}")

        # 4. Futures Check
        try:
            client.futures_account_balance()
            print("✅ Futures: Accessible.")
        except Exception as e:
            print(f"❌ Futures: {e}")

    except Exception as e:
        print(f"❌ CRITICAL ERROR during diagnostics: {e}")

if __name__ == "__main__":
    asyncio.run(check_permissions())
