import asyncio
import time
from src.utils.logger import app_logger

class SentinelAgent:
    """
    PROSOFT SWARM: Sentinel Agent (The Macro Sentry).
    Background worker that continuously monitors macro trends, funding rates,
    whales orderflow, and Federal Reserve/market news.
    """
    def __init__(self, bot, shared_state):
        self.bot = bot
        self.state = shared_state
        self.is_running = False
        self.poll_interval = 60  # Check macro trends every 60 seconds
        
    async def start(self):
        self.is_running = True
        asyncio.create_task(self._run_loop())
        app_logger.info("🕵️ Sentinel Agent (Macro-Sentry) STARTED successfully.")
        
    async def stop(self):
        self.is_running = False
        
    async def _fetch_yahoo_finance(self, ticker):
        """Asynchronously fetch chart data for a single ticker from Yahoo Finance."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.0.0 Safari/537.36"
        }
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=1d&interval=1m"
        import aiohttp
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status != 200:
                        return None
                    data = await response.json()
                    result = data.get("chart", {}).get("result", [])
                    if not result:
                        return None
                    meta = result[0].get("meta", {})
                    price = meta.get("regularMarketPrice")
                    prev_close = meta.get("previousClose")
                    
                    pct_change = 0.0
                    if price and prev_close:
                        pct_change = ((price - prev_close) / prev_close) * 100.0
                    return {"price": price, "pct_change": pct_change}
        except Exception as e:
            app_logger.error(f"[SENTINEL] Yahoo Finance error for {ticker}: {e}")
            return None

    async def _run_loop(self):
        while self.is_running:
            try:
                # 1. Fetch current Market Health
                mkt_health = self.bot.stats.get('market_health', 50.0)
                
                # 2. Fetch Fear & Greed Index safely
                raw_fgi = self.bot.stats.get('fear_greed_index', 50)
                try:
                    fgi = int(raw_fgi) if raw_fgi is not None and raw_fgi != "N/A" else 50
                except Exception:
                    fgi = 50
                    
                # 3. Fetch BTC Dominance
                btc_dom = self.bot.stats.get('btc_dominance', 50.0)
                
                # 4. Fetch Orderflow Sentiment bias
                sentiment = self.bot.stats.get('sentiment', 'NEUTRAL')
                
                # 5. Fetch Yahoo Finance macro indices asynchronously
                # Defaults if fetch fails
                vix_val = getattr(self.state, 'vix', 18.0)
                dxy_chg = getattr(self.state, 'dxy_change', 0.0)
                ndq_chg = getattr(self.state, 'ndq_change', 0.0)
                
                vix_task = self._fetch_yahoo_finance("^VIX")
                dxy_task = self._fetch_yahoo_finance("DX-Y.NYB")
                ndq_task = self._fetch_yahoo_finance("^IXIC")
                
                vix_data, dxy_data, ndq_data = await asyncio.gather(vix_task, dxy_task, ndq_task, return_exceptions=True)
                
                if isinstance(vix_data, dict) and vix_data is not None:
                    vix_val = vix_data["price"]
                if isinstance(dxy_data, dict) and dxy_data is not None:
                    dxy_chg = dxy_data["pct_change"]
                if isinstance(ndq_data, dict) and ndq_data is not None:
                    ndq_chg = ndq_data["pct_change"]
                
                # Update global shared state
                await self.state.update_macro(
                    health=mkt_health,
                    fgi=fgi,
                    btc_dom=btc_dom,
                    sentiment=sentiment,
                    vix=vix_val,
                    dxy_change=dxy_chg,
                    ndq_change=ndq_chg
                )
                
                # Whale Wallet Alert / Funding Rate logic could be fetched here
                # Log macro state in debug mode
                app_logger.debug(
                    f"[SENTINEL] Macro Update: Health={mkt_health:.1f}% | "
                    f"FGI={fgi} | BTC-Dom={btc_dom:.1f}% | Sentiment={sentiment} | "
                    f"VIX={vix_val:.2f} | DXY={dxy_chg:+.2f}% | NDQ={ndq_chg:+.2f}%"
                )
                
            except Exception as e:
                app_logger.error(f"[SENTINEL ERROR] Failed in macro scan: {e}")
                
            await asyncio.sleep(self.poll_interval)
