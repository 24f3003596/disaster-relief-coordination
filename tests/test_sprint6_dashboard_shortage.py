"""Sprint 6 regression tests for dashboard exports and shortage notifications."""
import csv
import io

import pytest
from werkzeug.security import generate_password_hash

from assignments import allocate_request
from constants import (
    NOTIFICATION_CRITICAL_SHORTAGE,
    ROLE_ADMIN,
    ROLE_COORDINATOR,
    ROLE_VICTIM,
    ROLE_VOLUNTEER,
)
from extensions import db
from inventory import create_inventory_item, update_inventory_stock
from models import InventoryItem, Notification, ReliefRequest, User
from notifications import check_and_notify_critical_shortage
from requests_module import create_relief_request


def make_user(app, role, suffix, **overrides):
    with app.app_context():
        values = {
            "name": f"{role} {suffix}",
            "email": f"{suffix}-{role.lower()}@example.com",
            "role": role,
            "password_hash": generate_password_hash("StrongPass123"),
        }
        values.update(overrides)
        user = User(**values)
        db.session.add(user)
        db.session.commit()
        return user.user_id


def login(client, user_id):
    with client.session_transaction() as session:
        session.clear()
        session["user_id"] = user_id


def test_dashboard_summary_requires_coordinator_or_admin(app, client):
    assert client.get("/dashboard/summary").status_code == 401
    assert client.get("/dashboard/?format=json").status_code == 401

    victim_id = make_user(app, ROLE_VICTIM, "summary-victim")
    login(client, victim_id)
    assert client.get("/dashboard/summary").status_code == 403
    assert client.get("/dashboard/?format=json").status_code == 403

    coordinator_id = make_user(app, ROLE_COORDINATOR, "summary-coordinator")
    login(client, coordinator_id)
    assert client.get("/dashboard/summary").status_code == 200
    assert client.get("/dashboard/?format=json").status_code == 200


def test_csv_exports_escape_spreadsheet_formulas_and_set_download_headers(app, client):
    admin_id = make_user(app, ROLE_ADMIN, "csv-safe-admin")
    victim_id = make_user(app, ROLE_VICTIM, "csv-safe-victim")

    with app.app_context():
        db.session.add(
            ReliefRequest(
                user_id=victim_id,
                category="=HYPERLINK(\"https://evil.example\",\"open\")",
                quantity=3,
                urgency="High",
                location="  @SUM(A1:A2)",
                status="Pending",
            )
        )
        db.session.add(
            InventoryItem(
                category="+SUM(1,1)",
                quantity=8,
                storage_location="-2+3",
                threshold=5,
            )
        )
        db.session.commit()

    login(client, admin_id)

    request_response = client.get("/reports/export/requests")
    assert request_response.status_code == 200
    assert request_response.mimetype == "text/csv"
    assert request_response.headers["X-Content-Type-Options"] == "nosniff"
    assert request_response.headers["Cache-Control"] == "no-store"
    request_rows = list(csv.reader(io.StringIO(request_response.get_data(as_text=True))))
    assert request_rows[1][2].startswith("'=")
    assert request_rows[1][5].startswith("'  @")

    inventory_response = client.get("/reports/export/inventory")
    assert inventory_response.status_code == 200
    inventory_rows = list(csv.reader(io.StringIO(inventory_response.get_data(as_text=True))))
    assert inventory_rows[1][1].startswith("'+")
    assert inventory_rows[1][3].startswith("'-")


def test_shortage_notifications_are_committed_and_survive_session_reopen(app):
    coordinator_id = make_user(app, ROLE_COORDINATOR, "persist-coordinator")
    admin_id = make_user(app, ROLE_ADMIN, "persist-admin")
    victim_id = make_user(app, ROLE_VICTIM, "persist-victim")

    with app.app_context():
        create_inventory_item("Water", 4, "Warehouse A", threshold=5)
        create_relief_request(
            victim_id, "Water", 2, "High", location="Camp A"
        )

        # The helper is called during request creation and the operation
        # commits both its request and generated notifications.
        db.session.remove()
        persisted = Notification.query.filter_by(
            type=NOTIFICATION_CRITICAL_SHORTAGE
        ).all()
        assert {item.user_id for item in persisted} == {
            coordinator_id, admin_id
        }


def test_shortage_notification_is_persisted_after_stock_reduction(app):
    coordinator_id = make_user(app, ROLE_COORDINATOR, "stock-coordinator")
    victim_id = make_user(app, ROLE_VICTIM, "stock-victim")

    with app.app_context():
        item = create_inventory_item("Medical Supplies", 20, "Depot A", threshold=10)
        create_relief_request(
            victim_id, "Medical Supplies", 3, "Critical", location="Clinic A"
        )
        update_inventory_stock(item.item_id, -12)  # 20 -> 8

        db.session.remove()
        alerts = Notification.query.filter_by(
            user_id=coordinator_id,
            type=NOTIFICATION_CRITICAL_SHORTAGE,
        ).all()
        assert len(alerts) == 1
        assert "Medical Supplies" in alerts[0].message


def test_reading_notification_does_not_realert_unchanged_shortage(app):
    coordinator_id = make_user(app, ROLE_COORDINATOR, "dedup-coordinator")
    victim_id = make_user(app, ROLE_VICTIM, "dedup-victim")

    with app.app_context():
        item = create_inventory_item("Water", 20, "Depot B", threshold=10)
        create_relief_request(victim_id, "Water", 5, "High", location="Camp B")
        update_inventory_stock(item.item_id, -12)
        first = Notification.query.filter_by(
            user_id=coordinator_id,
            type=NOTIFICATION_CRITICAL_SHORTAGE,
        ).one()
        first.is_read = True
        db.session.commit()

        assert check_and_notify_critical_shortage(category="Water") == []
        assert Notification.query.filter_by(
            user_id=coordinator_id,
            type=NOTIFICATION_CRITICAL_SHORTAGE,
        ).count() == 1


def test_shortage_state_resets_after_recovery_and_alerts_on_new_episode(app):
    coordinator_id = make_user(app, ROLE_COORDINATOR, "episode-coordinator")
    victim_id = make_user(app, ROLE_VICTIM, "episode-victim")

    with app.app_context():
        item = create_inventory_item("Food", 20, "Depot C", threshold=10)
        create_relief_request(victim_id, "Food", 5, "High", location="Camp C")

        update_inventory_stock(item.item_id, -12)  # 20 -> 8: episode 1
        assert Notification.query.filter_by(
            user_id=coordinator_id,
            type=NOTIFICATION_CRITICAL_SHORTAGE,
        ).count() == 1

        update_inventory_stock(item.item_id, 10)  # 8 -> 18: recovery
        update_inventory_stock(item.item_id, -9)  # 18 -> 9: episode 2

        assert Notification.query.filter_by(
            user_id=coordinator_id,
            type=NOTIFICATION_CRITICAL_SHORTAGE,
        ).count() == 2


def test_only_active_approved_operational_users_receive_shortage_alerts(app):
    coordinator_id = make_user(app, ROLE_COORDINATOR, "active-coordinator")
    admin_id = make_user(app, ROLE_ADMIN, "active-admin")
    inactive_admin_id = make_user(
        app, ROLE_ADMIN, "inactive-admin", is_active=False
    )
    pending_coordinator_id = make_user(
        app, ROLE_COORDINATOR, "pending-coordinator", approval_status="pending"
    )
    victim_id = make_user(app, ROLE_VICTIM, "recipient-victim")
    volunteer_id = make_user(app, ROLE_VOLUNTEER, "recipient-volunteer")

    with app.app_context():
        item = create_inventory_item("Shelter", 20, "Depot D", threshold=10)
        create_relief_request(victim_id, "Shelter", 5, "High", location="Camp D")
        update_inventory_stock(item.item_id, -15)

        received = {
            row.user_id
            for row in Notification.query.filter_by(
                type=NOTIFICATION_CRITICAL_SHORTAGE
            ).all()
        }
        assert received == {coordinator_id, admin_id}
        assert inactive_admin_id not in received
        assert pending_coordinator_id not in received
        assert victim_id not in received
        assert volunteer_id not in received


def test_private_notifications_and_broadcast_routes_require_authorization(app, client):
    coordinator_id = make_user(app, ROLE_COORDINATOR, "broadcast-coordinator")
    victim_id = make_user(app, ROLE_VICTIM, "broadcast-victim")

    anonymous_list = client.get("/notifications/")
    assert anonymous_list.status_code == 200
    assert anonymous_list.get_json()["notifications"] == []
    assert client.post(
        "/notifications/broadcast", json={"message": "Test alert"}
    ).status_code == 401

    login(client, victim_id)
    assert client.post(
        "/notifications/broadcast", json={"message": "Test alert"}
    ).status_code == 403

    login(client, coordinator_id)
    response = client.post(
        "/notifications/broadcast", json={"message": "Authorized test alert"}
    )
    assert response.status_code == 201

    notifications = client.get("/notifications/")
    assert notifications.status_code == 200
    assert all(
        item["user_id"] == coordinator_id
        for item in notifications.get_json()["notifications"]
    )



def test_anonymous_notifications_page_does_not_expose_private_messages(app, client):
    victim_id = make_user(app, ROLE_VICTIM, "private-page-victim")
    with app.app_context():
        db.session.add(Notification(
            user_id=victim_id,
            message="PRIVATE SHORTAGE DETAILS",
            type=NOTIFICATION_CRITICAL_SHORTAGE,
            is_read=False,
        ))
        db.session.commit()

    response = client.get("/notifications")
    assert response.status_code == 200
    assert b"PRIVATE SHORTAGE DETAILS" not in response.data
