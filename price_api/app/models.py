from sqlalchemy import Column, Integer, String, DateTime, JSON, func
from .db import Base

class ExchangeInfo(Base):
    __tablename__ = "exchange_info"
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), index=True, nullable=False)
    exchange_info = Column(JSON, nullable=False)
    called_at = Column(DateTime(timezone=True), server_default=func.now())