import os
import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_user.db")
os.environ.setdefault("JWT_SECRET", "test_secret")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "5")

from app.db import Base, engine, SessionLocal
from app.main import app

Base.metadata.create_all(bind=engine)

@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()