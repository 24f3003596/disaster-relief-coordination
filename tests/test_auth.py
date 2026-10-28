import pytest

from auth import register_user
from constants import ROLE_VICTIM
from extensions import db
from models import User


def test_register_success(client, app):
    response = client.post("/auth/register", json={
        "name": "Test User", "email": "test@example.com", "password": "safe-pass-123"
    })
    assert response.status_code == 201
    assert response.json["user"]["email"] == "test@example.com"
    assert response.json["user"]["role"] == ROLE_VICTIM
    with app.app_context():
        user = User.query.filter_by(email="test@example.com").one()
        assert user.role == ROLE_VICTIM


@pytest.mark.parametrize("requested_role", [
    "Admin", "Coordinator", "Volunteer", "UnexpectedRole", "Victim"
])
def test_api_registration_cannot_choose_role(client, app, requested_role):
    email = f"role-{requested_role.lower()}@example.com"
    response = client.post("/auth/register", json={
        "name": "Public User",
        "email": email,
        "password": "safe-pass-123",
        "role": requested_role,
    })

    assert response.status_code == 201
    assert response.json["user"]["role"] == ROLE_VICTIM
    with app.app_context():
        user = User.query.filter_by(email=email).one()
        assert user.role == ROLE_VICTIM


@pytest.mark.parametrize("requested_role", ["Admin", "Coordinator", "Volunteer"])
def test_html_registration_cannot_choose_role(client, app, requested_role):
    email = f"html-{requested_role.lower()}@example.com"
    response = client.post("/register", data={
        "name": "Browser User",
        "phone": "9000000000",
        "email": email,
        "password": "safe-pass-123",
        "role": requested_role,
    })

    assert response.status_code == 200
    assert b"Account created" in response.data
    with app.app_context():
        user = User.query.filter_by(email=email).one()
        assert user.role == ROLE_VICTIM


def test_registration_page_does_not_offer_role_selector(client):
    response = client.get("/register")
    assert response.status_code == 200
    assert b'name="role"' not in response.data
    assert b"registered as Victim" in response.data


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


def test_role_update_requires_authorization(client):
    response = client.patch("/auth/users/1/role", json={"role": "Admin"})
    assert response.status_code == 401

    registered = client.post("/auth/register", json={
        "name": "Ordinary User", "email": "ordinary@example.com", "password": "safe-pass-123"
    })
    assert registered.status_code == 201
    client.post("/auth/login", json={"email": "ordinary@example.com", "password": "safe-pass-123"})
    response = client.patch("/auth/users/1/role", json={"role": "Coordinator"})
    assert response.status_code == 403


def test_admin_can_assign_role_through_protected_endpoint(app, client):
    client.post("/auth/register", json={
        "name": "Ordinary User", "email": "target@example.com", "password": "safe-pass-123"
    })
    with app.app_context():
        admin = register_user(
            name="Provisioned Admin",
            email="admin-for-test@example.com",
            password="admin-pass-123",
            role="Admin",
        )
        admin_id = admin.user_id
        target = User.query.filter_by(email="target@example.com").one()
        target_id = target.user_id

    login = client.post("/auth/login", json={
        "email": "admin-for-test@example.com", "password": "admin-pass-123"
    })
    assert login.status_code == 200
    assert login.json["user"]["role"] == "Admin"

    response = client.patch(f"/auth/users/{target_id}/role", json={"role": "Coordinator"})
    assert response.status_code == 200
    assert response.json["user"]["role"] == "Coordinator"
    with app.app_context():
        assert db.session.get(User, target_id).role == "Coordinator"
        assert db.session.get(User, admin_id).role == "Admin"
