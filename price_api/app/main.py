from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import os, asyncio
from datetime import datetime

from .db import Base, engine, SessionLocal
from .models import ExchangeInfo
from .schemas import RawOut
from .cache import get_cached_price, set_cached_price
from .binance_client import get_price

SYMBOLS = [s.strip() for s in os.getenv("SYMBOLS", "BTCUSDT,ETHBTC,ETHUSDT").split(",")]
REFRESH_INTERVAL = int(os.getenv("REFRESH_INTERVAL_SECONDS", "60"))  # อ่านค่าจาก config/env

app = FastAPI(title="price_api", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def verify_internal(x_api_key: Optional[str] = Header(None, alias="X-API-Key")):
    expected = os.getenv("INTERNAL_API_KEY", "")
    if not expected or x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

async def get_price_with_cache_persist(symbol: str, db: Session) -> RawOut:
    symbol = symbol.upper()

    cached = get_cached_price(symbol)
    if cached is None:
        raw = await get_price(symbol)
        set_cached_price(symbol, raw)
        rec = ExchangeInfo(symbol=symbol, exchange_info=raw)
        db.add(rec)
        db.commit()
        db.refresh(rec)
        return {
            "id": rec.id,
            "symbol": rec.symbol,
            "called_at": rec.called_at.isoformat(),
            "exchange_info": rec.exchange_info,
        }
    else:
        rec = (
            db.query(ExchangeInfo)
            .filter(ExchangeInfo.symbol == symbol)
            .order_by(ExchangeInfo.id.desc())
            .first()
        )
        if rec is None:
            rec = ExchangeInfo(symbol=symbol, exchange_info=cached)
            db.add(rec)
            db.commit()
            db.refresh(rec)
            return {
                "id": rec.id,
                "symbol": rec.symbol,
                "called_at": rec.called_at.isoformat(),
                "exchange_info": cached,
            }
        else:
            return {
                "id": rec.id,
                "symbol": rec.symbol,
                "called_at": rec.called_at.isoformat(),
                "exchange_info": cached,
            }

@app.get("/internal/price", response_model=List[RawOut], tags=["internal"])
async def internal_current_all(
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal)
):
    results: List[RawOut] = []
    for sym in SYMBOLS:
        try:
            results.append(await get_price_with_cache_persist(sym, db))
        except Exception as e:
            continue
    return results

@app.get("/internal/price/{symbol}", response_model=List[RawOut], tags=["internal"])
async def internal_current_by_symbol(
    symbol: str,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal),
):
    return [await get_price_with_cache_persist(symbol, db)]

async def refresh_loop():
    await asyncio.sleep(3)
    while True:
        for sym in SYMBOLS:
            try:
                raw = await get_price(sym)
                set_cached_price(sym, raw)
                db = SessionLocal()
                db.add(ExchangeInfo(symbol=sym, exchange_info=raw))
                db.commit()
                db.close()
            except Exception:
                pass
        await asyncio.sleep(REFRESH_INTERVAL)

@app.on_event("startup")
async def start_bg():
    asyncio.create_task(refresh_loop())