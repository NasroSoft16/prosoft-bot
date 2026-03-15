from src.utils.logger import app_logger

class LiquidityHeatmap:
    """
    PROSOFT AI: War Room - Real-time Liquidity Heatmap (Cycle 4)
    عرض الخريطة الحرارية للسيولة العالمية. 
    يحلل عمق السوق لكشف مناطق السيولة الكثيفة والفراغات.
    """

    def __init__(self, api_client):
        self.api = api_client
        self.heatmap_data = {}

    def generate_heatmap(self, symbol, depth=50):
        """
        توليد بيانات الخريطة الحرارية لدفتر الطلبات.
        كل مستوى سعري يحصل على "حرارة" بناءً على حجم السيولة الموجودة.
        """
        if not self.api.client:
            return None

        try:
            book = self.api.client.get_order_book(symbol=symbol, limit=depth)
            
            bids = [(float(b[0]), float(b[1])) for b in book['bids']]
            asks = [(float(a[0]), float(a[1])) for a in book['asks']]
            
            all_volumes = [b[1] for b in bids] + [a[1] for a in asks]
            max_vol = max(all_volumes) if all_volumes else 1
            
            # Generate heatmap zones
            bid_zones = []
            for price, vol in bids:
                intensity = (vol / max_vol) * 100  # 0-100 heat
                zone = 'COLD'
                if intensity > 70:
                    zone = 'INFERNO'
                elif intensity > 40:
                    zone = 'HOT'
                elif intensity > 15:
                    zone = 'WARM'
                
                bid_zones.append({
                    'price': price,
                    'volume': round(vol, 4),
                    'intensity': round(intensity, 1),
                    'zone': zone,
                    'side': 'BID'
                })

            ask_zones = []
            for price, vol in asks:
                intensity = (vol / max_vol) * 100
                zone = 'COLD'
                if intensity > 70:
                    zone = 'INFERNO'
                elif intensity > 40:
                    zone = 'HOT'
                elif intensity > 15:
                    zone = 'WARM'

                ask_zones.append({
                    'price': price,
                    'volume': round(vol, 4),
                    'intensity': round(intensity, 1),
                    'zone': zone,
                    'side': 'ASK'
                })

            # Find critical support/resistance from heatmap
            support_levels = [z for z in bid_zones if z['zone'] in ['HOT', 'INFERNO']]
            resistance_levels = [z for z in ask_zones if z['zone'] in ['HOT', 'INFERNO']]

            self.heatmap_data = {
                'symbol': symbol,
                'bid_zones': bid_zones[:10],  # Top 10
                'ask_zones': ask_zones[:10],
                'support_walls': support_levels[:3],
                'resistance_walls': resistance_levels[:3],
                'total_bid_liquidity': round(sum(b[1] for b in bids), 2),
                'total_ask_liquidity': round(sum(a[1] for a in asks), 2),
                'dominance': 'BUYERS' if sum(b[1] for b in bids) > sum(a[1] for a in asks) else 'SELLERS'
            }
            
            app_logger.info(
                f"🗺️ [WAR ROOM] Heatmap generated for {symbol} | "
                f"Support walls: {len(support_levels)} | "
                f"Resistance walls: {len(resistance_levels)} | "
                f"Dominance: {self.heatmap_data['dominance']}"
            )
            
            return self.heatmap_data
            
        except Exception as e:
            app_logger.error(f"[WAR ROOM] Heatmap generation error: {e}")
            return None
