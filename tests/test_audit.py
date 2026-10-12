import pytest
from extensions import db
from models import User, AuditLog
from audit import log_action, list_audit_logs
from constants import ACTION_CREATE_INVENTORY, ACTION_UPDATE_ROLE, ROLE_COORDINATOR, ROLE_VICTIM
from werkzeug.security import generate_password_hash

def test_log_action_and_listing(app):
    with app.app_context():
        user = User(
            name="Audit User",
            email="audit@example.com",
            role=ROLE_VICTIM,
            password_hash=generate_password_hash("safe-pass-123"),
        )
        db.session.add(user)
        db.session.commit()

        # Log action
        entry = log_action(
            user_id=user.user_id,
            action=ACTION_CREATE_INVENTORY,
            entity_type="InventoryItem",
            entity_id=1,
        )
        assert entry.log_id is not None
        assert entry.action == ACTION_CREATE_INVENTORY
        assert entry.entity_id == 1

        # List audit logs
        logs = list_audit_logs()
        assert len(logs) >= 1
        assert logs[0].action == ACTION_CREATE_INVENTORY

def test_log_action_requires_action(app):
    with app.app_context():
        with pytest.raises(ValueError, match="action is required"):
            log_action(user_id=1, action="")

def test_audit_routes_require_authorization(app, client):
    with app.app_context():
        coord = User(
            name="Audit Coord",
            email="auditcoord@example.com",
            role=ROLE_COORDINATOR,
            password_hash=generate_password_hash("safe-pass-123"),
        )
        victim = User(
            name="Regular Victim",
            email="victimreg@example.com",
            role=ROLE_VICTIM,
            password_hash=generate_password_hash("safe-pass-123"),
        )
        db.session.add_all([coord, victim])
        db.session.commit()
        coord_id = coord.user_id
        victim_id = victim.user_id

    # Unauthenticated request -> 401
    res = client.get("/audit/")
    assert res.status_code == 401

    # Victim request -> 403 Forbidden
    with client.session_transaction() as sess:
        sess["user_id"] = victim_id
    res_victim = client.get("/audit/")
    assert res_victim.status_code == 403

    # Coordinator request -> 200 OK
    with client.session_transaction() as sess:
        sess["user_id"] = coord_id
    res_coord = client.get("/audit/")
    assert res_coord.status_code == 200
    assert "audit_logs" in res_coord.json
