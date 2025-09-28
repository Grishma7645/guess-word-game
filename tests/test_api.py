import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import Base, engine, SessionLocal
from backend.models import Word

client = TestClient(app)

# Reset DB for tests
@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.add_all([
        Word(text="CRANE"),
        Word(text="PLANT"),
        Word(text="STONE")
    ])
    db.commit()
    db.close()
    yield

def test_register_and_login():
    res = client.post("/register", json={"username": "TestUser", "password": "Pass1@"})
    assert res.status_code == 200

    res = client.post("/login", json={"username": "TestUser", "password": "Pass1@"})
    assert res.status_code == 200
    data = res.json()
    assert "token" in data
    global token
    token = data["token"]

def test_start_game():
    res = client.post("/start_game", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert "game_id" in data
    global game_id
    game_id = data["game_id"]

def test_guess_word():
    res = client.post("/guess", json={"game_id": game_id, "guess": "CRANE"},
                      headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert "feedback" in data
    assert len(data["feedback"]) == 5

def test_admin_report():
    res = client.get("/admin/report/day?date=2025-09-28", headers={"Authorization": f"Bearer {token}"})
    # Since TestUser is not admin, should fail
    assert res.status_code in (401, 403)
