import pytest
from auth import register_user, authenticate_user
from extensions import db

def test_password_is_hashed_and_login_works(app):
    with app.app_context():
        u=register_user("Test User",None,"test@example.com","password123")
        assert u.password_hash != "password123"
        assert authenticate_user("test@example.com","password123").user_id==u.user_id
        assert authenticate_user("test@example.com","wrong") is None

def test_duplicate_email_rejected(app):
    with app.app_context():
        register_user("A",None,"same@example.com","password123")
        with pytest.raises(ValueError): register_user("B",None,"same@example.com","password123")
