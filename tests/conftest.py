import pytest
from app import create_app
from extensions import db
from auth import register_user
from inventory import create_inventory_item
from requests_module import create_relief_request

@pytest.fixture()
def app(tmp_path):
    database_path = tmp_path / "test.db"
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret",
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database_path.as_posix()}",
        "WTF_CSRF_ENABLED": False,
        "OTP_AUTO_VERIFY_TESTING": True,
    })
    with app.app_context():
        db.drop_all()
        db.create_all()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()

@pytest.fixture()
def client(app):
    return app.test_client()

@pytest.fixture()
def seed(app):
    with app.app_context():
        victim = register_user("Victim", "111", "victim@example.com", "password123", "Victim")
        volunteer = register_user("Volunteer", "222", "volunteer@example.com", "password123", "Volunteer")
        item = create_inventory_item("Water", 10, "Warehouse A", threshold=2)
        request = create_relief_request(victim.user_id, "Water", 4, "High", 11.0, 76.0)
        return {
            "victim": victim.user_id,
            "volunteer": volunteer.user_id,
            "item": item.item_id,
            "request": request.request_id,
        }
