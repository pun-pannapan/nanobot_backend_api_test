from pydantic import BaseModel
from typing import Any

class PriceOut(BaseModel):
    symbol: str
    price: float

class RawOut(BaseModel):
    id: int
    symbol: str
    called_at: str
    exchange_info: Any