import pytest
from datetime import datetime, timedelta
from auth import register_user
from extensions import db
from models import User, PhoneOTP


def make_admin(app):
    with app.app_context():
        admin = register_user("Sprint Admin", email="sprint-admin@example.com",
                              password="strong-pass-123", role="Admin")
        return admin.user_id

def login_as(client, email, password="strong-pass-123"):
    return client.post("/auth/login", json={"email": email, "password": password})

def test_privileged_role_assignment_requires_admin_approval(app, client):
    admin_id = make_admin(app)
    with app.app_context():
        victim = register_user("Candidate", email="candidate@example.com",
                              password="strong-pass-123", role="Victim")
        candidate_id = victim.user_id
    assert login_as(client, "sprint-admin@example.com").status_code == 200
    promoted = client.patch(f"/auth/users/{candidate_id}/role", json={"role": "Coordinator"})
    assert promoted.status_code == 200
    assert promoted.json["user"]["approval_status"] == "pending"
    client.post("/auth/logout")
    assert login_as(client, "candidate@example.com").status_code == 401
    assert login_as(client, "sprint-admin@example.com").status_code == 200
    pending = client.get("/auth/admin/pending-approvals")
    assert pending.status_code == 200
    assert candidate_id in [u["user_id"] for u in pending.json["accounts"]]
    approved = client.post(f"/auth/admin/users/{candidate_id}/approval", json={"decision": "approve"})
    assert approved.status_code == 200
    client.post("/auth/logout")
    assert login_as(client, "candidate@example.com").status_code == 200

def test_unauthorized_user_cannot_approve(app, client):
    with app.app_context():
        admin = register_user("Admin", email="approval-admin@example.com", password="strong-pass-123", role="Admin")
        candidate = register_user("Candidate", email="approval-candidate@example.com", password="strong-pass-123", role="Victim")
        candidate.role = "Coordinator"
        candidate.approval_status = "pending"
        db.session.commit()
        candidate_id = candidate.user_id
    assert login_as(client, "approval-candidate@example.com").status_code == 401
    response = client.post(f"/auth/admin/users/{candidate_id}/approval", json={"decision": "approve"})
    assert response.status_code == 401

def test_rejection_blocks_privileged_login(app, client):
    make_admin(app)
    with app.app_context():
        candidate = register_user("Reject Me", email="reject-me@example.com", password="strong-pass-123", role="Victim")
        candidate.role = "Coordinator"
        candidate.approval_status = "pending"
        db.session.commit()
        candidate_id = candidate.user_id
    assert login_as(client, "sprint-admin@example.com").status_code == 200
    response = client.post(f"/auth/admin/users/{candidate_id}/approval", json={"decision": "reject", "reason": "Not authorized"})
    assert response.status_code == 200
    client.post("/auth/logout")
    assert login_as(client, "reject-me@example.com").status_code == 401

def test_public_registration_requires_phone_and_otp(app, client):
    app.config["OTP_AUTO_VERIFY_TESTING"] = False
    app.config["OTP_DEMO_MODE"] = True
    response = client.post("/auth/register", json={"name": "OTP User", "phone": "9876543210",
        "email": "otp-user@example.com", "password": "strong-pass-123", "role": "Admin"})
    assert response.status_code == 201
    code = response.json["demo_otp"]
    assert response.json["user"]["role"] == "Victim"
    assert response.json["user"]["is_active"] is False
    assert login_as(client, "otp-user@example.com").status_code == 401
    with app.app_context():
        otp = PhoneOTP.query.one()
        assert otp.otp_hash != code
        assert otp.phone == "9876543210"
    wrong = client.post("/auth/verify-phone", json={"email": "otp-user@example.com", "phone": "9876543210", "otp": "000000"})
    assert wrong.status_code == 400
    verified = client.post("/auth/verify-phone", json={"email": "otp-user@example.com", "phone": "9876543210", "otp": code})
    assert verified.status_code == 200
    assert login_as(client, "otp-user@example.com").status_code == 200
    reused = client.post("/auth/verify-phone", json={"email": "otp-user@example.com", "phone": "9876543210", "otp": code})
    assert reused.status_code == 400

def test_production_registration_does_not_return_otp(app, client):
    app.config["OTP_AUTO_VERIFY_TESTING"] = False
    app.config["OTP_DEMO_MODE"] = False
    response = client.post("/auth/register", json={"name": "No Leak", "phone": "9000000000",
        "email": "no-leak@example.com", "password": "strong-pass-123"})
    assert response.status_code == 201
    assert "demo_otp" not in response.json


def test_expired_otp_is_rejected(app, client):
    app.config["OTP_AUTO_VERIFY_TESTING"] = False
    app.config["OTP_DEMO_MODE"] = True
    response = client.post("/auth/register", json={"name": "Expired OTP", "phone": "9000000001",
        "email": "expired-otp@example.com", "password": "strong-pass-123"})
    code = response.json["demo_otp"]
    with app.app_context():
        challenge = PhoneOTP.query.one()
        challenge.expires_at = datetime.utcnow() - timedelta(seconds=1)
        db.session.commit()
    result = client.post("/auth/verify-phone", json={"email": "expired-otp@example.com",
        "phone": "9000000001", "otp": code})
    assert result.status_code == 400


def test_invalid_privileged_approval_state_fails_closed(app, client):
    with app.app_context():
        user = register_user("Invalid State", email="invalid-state@example.com",
                             password="strong-pass-123", role="Coordinator")
        user.approval_status = "unknown"
        db.session.commit()
    assert login_as(client, "invalid-state@example.com").status_code == 401
