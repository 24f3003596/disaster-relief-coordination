from models import User
from extensions import db

def test_register_success(client):
    response = client.post("/auth/register", json={
        "name": "Test User", "email": "test@example.com", "password": "safe-pass-123"
    })
    assert response.status_code == 201
    assert response.json["user"]["email"] == "test@example.com"

def test_register_duplicate_email(client):
    payload = {"name": "Test User", "email": "same@example.com", "password": "safe-pass-123"}
    assert client.post("/auth/register", json=payload).status_code == 201
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 400
    assert "already registered" in response.json["error"]

def test_register_short_password(client):
    response = client.post("/auth/register", json={
        "name": "Test User", "email": "short@example.com", "password": "123"
    })
    assert response.status_code == 400

def test_login_success_and_wrong_password(client):
    client.post("/auth/register", json={
        "name": "Test User", "email": "test@example.com", "password": "safe-pass-123"
    })
    good = client.post("/auth/login", json={"email": "test@example.com", "password": "safe-pass-123"})
    assert good.status_code == 200
    client.post("/auth/logout")
    bad = client.post("/auth/login", json={"email": "test@example.com", "password": "wrong-pass"})
    assert bad.status_code == 401

def test_password_is_hashed(app, client):
    client.post("/auth/register", json={
        "name": "Test User", "email": "hash@example.com", "password": "safe-pass-123"
    })
    with app.app_context():
        user = User.query.filter_by(email="hash@example.com").first()
        assert user.password_hash != "safe-pass-123"
        assert user.password_hash
