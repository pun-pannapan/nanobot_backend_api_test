import pytest
from fastapi.testclient import TestClient

@pytest.fixture(scope="session", autouse=True)
def set_env():
    mp = pytest.MonkeyPatch()
    mp.setenv("SYMBOLS", "BTCUSDT,ETHUSDT")
    mp.setenv("INTERNAL_API_KEY", "punapiinternalkey")
    yield
    mp.undo()

@pytest.fixture(scope="session")
def app_module():
    from app import main as app_main
    return app_main

@pytest.fixture(autouse=True)
def stub_binance_and_bg(monkeypatch, app_module):
    async def _fake_get_price(symbol: str):
        return {"symbol": symbol.upper(), "price": "68000.12"}
    monkeypatch.setattr(app_module, "get_price", _fake_get_price, raising=True)

    async def _noop_refresh_loop():
        return
    async def _noop_start_bg():
        return
    monkeypatch.setattr(app_module, "refresh_loop", _noop_refresh_loop, raising=True)
    monkeypatch.setattr(app_module, "start_bg", _noop_start_bg, raising=True)
    yield

@pytest.fixture(scope="session")
def client(app_module):
    with TestClient(app_module.app) as c:
        yield c

def test_internal_requires_api_key(client):
    r = client.get("/internal/price", params={"limit": 2})
    assert r.status_code in (401, 403)

    r = client.get(
        "/internal/price",
        params={"limit": 2},
        headers={"X-API-Key": "punapiinternalkey"},
    )
    assert r.status_code == 200, r.text
    rows = r.json()
    assert isinstance(rows, list)

def test_internal_price_returns_all_symbols(client, app_module):
    r = client.get("/internal/price", headers={"X-API-Key": "punapiinternalkey"})
    assert r.status_code == 200, r.text
    data = r.json()
    expected = set(s.upper() for s in app_module.SYMBOLS)
    got = {row["symbol"] for row in data}
    assert got == expected
    for row in data:
        assert {"id", "symbol", "called_at", "exchange_info"} <= row.keys()
        assert "price" in row["exchange_info"]

def test_internal_price_by_symbol_list_wrapper(client):
    r = client.get("/internal/price/BTCUSDT", headers={"X-API-Key": "punapiinternalkey"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data, list) and len(data) == 1
    one = data[0]
    assert one["symbol"] == "BTCUSDT"
    assert one["exchange_info"]["price"] == "68000.12"

def test_internal_price_latest_returns_object(client):
    r = client.get("/internal/price/ETHUSDT", headers={"X-API-Key": "punapiinternalkey"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data, list) and len(data) == 1
    one = data[0]
    assert one["symbol"] == "ETHUSDT"
    assert one["exchange_info"]["price"] == "68000.12"