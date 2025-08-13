import os
import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_price.db")
os.environ.setdefault("INTERNAL_API_KEY", "local-internal-key")
os.environ.setdefault("REFRESH_INTERVAL_SECONDS", "3600")  # กันไม่ให้ดึงถี่เกินตอนเทส

from app.db import Base, engine
Base.metadata.create_all(bind=engine)

from app.main import app

import fakeredis
from app import cache as cache_mod
cache_mod.r = fakeredis.FakeRedis(decode_responses=True)

@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c