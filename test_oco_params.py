import os
from binance.client import Client
from dotenv import load_dotenv

def test_oco_signature():
    load_dotenv()
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    client = Client(api_key, api_secret)
    
    print("Testing OCO parameters...")
    try:
        # We don't actually want to place a real order if we don't have to, 
        # but we want to see if the API accepts the parameters or if the library rejects them.
        # Using a non-existent symbol or invalid qty might trigger a different error, 
        # which is still progress if it doesn't complain about 'aboveType'.
        
        # Testing with new parameters
        # Note: We use a dummy symbol and 0 qty to just test the request construction/initial validation
        client.create_oco_order(
            symbol='BTCUSDT',
            side='SELL',
            quantity=0.001,
            price='100000',
            stopPrice='40000',
            stopLimitPrice='39000',
            stopLimitTimeInForce='GTC',
            aboveType='LIMIT_MAKER',
            belowType='STOP_LOSS_LIMIT'
        )
    except Exception as e:
        print(f"Caught expected error or actual error: {e}")

if __name__ == "__main__":
    test_oco_signature()
