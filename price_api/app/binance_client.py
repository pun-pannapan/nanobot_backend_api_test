import os
import httpx

BASE = os.getenv("BINANCE_BASE_URL", "https://testnet.binance.vision")

async def get_price(symbol: str):
    url = f"{BASE}/api/v3/ticker/price"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, params={"symbol": symbol})
        resp.raise_for_status()
        return resp.json()