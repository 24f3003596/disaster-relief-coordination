"""
Automated Test Suite for Sprint 4 Tasks (Sree Naresh A)

Task 1: Complete Dashboard Analytics and CSV Export (SRS FR 3.7.1, FR 3.7.2)
- Request counts by status and category.
- Average response time and fulfillment time calculations with timestamps.
- Resource utilization rate calculations with inventory and allocation data.
- Safe handling of empty datasets and zero denominators.
- Admin-authorized CSV exports with correct headers and data.
- Access control enforcement (401 unauthenticated, 403 unauthorized).

Task 2: Automate Critical-Shortage Notifications (SRS FR 3.6.2)
- Threshold boundary checks (stock <= threshold).
- Generation of shortage notification when stock <= threshold AND pending requests exist.
- Suppression of alerts when no matching pending requests exist.
- Suppression of alerts when stock is above threshold.
- Operational role restriction (only Coordinators and Admins notified; Victims/Volunteers excluded).
- Deduplication of notifications on repeated operations while unread.
- Automatic triggers on stock updates, allocations, and new pending requests.
"""

from datetime import datetime, timedelta, timezone
import io
import csv
import pytest
from werkzeug.security import generate_password_hash

from extensions import db
from models import User, ReliefRequest, InventoryItem, Assignment, Notification, Incident
from dashboard import get_dashboard_summary
from inventory import create_inventory_item, update_inventory_stock
from assignments import allocate_request
from requests_module import create_relief_request
from notifications import check_and_notify_critical_shortage
from constants import (
    ROLE_VICTIM,
    ROLE_VOLUNTEER,
    ROLE_COORDINATOR,
    ROLE_ADMIN,
    NOTIFICATION_CRITICAL_SHORTAGE,
    STATUS_REQUEST_PENDING,
    STATUS_REQUEST_ASSIGNED,
    STATUS_REQUEST_FULFILLED,
    STATUS_ASSIGNMENT_ASSIGNED,
    STATUS_ASSIGNMENT_COMPLETED,
)


def make_user(app, role, email_prefix):
    """Helper to create a user with a given role."""
    with app.app_context():
        user = User(
            name=f"{role} User",
            email=f"{email_prefix}_{role.lower()}@example.com",
            role=role,
            password_hash=generate_password_hash("securepass123"),
        )
        db.session.add(user)
        db.session.commit()
        return user.user_id


def login_client(client, user_id):
    """Helper to authenticate test client session."""
    with client.session_transaction() as sess:
        sess["user_id"] = user_id


# ============================================================================
# TASK 1: DASHBOARD ANALYTICS & CSV EXPORT TESTS (FR 3.7.1 & FR 3.7.2)
# ============================================================================

def test_dashboard_displays_request_counts_by_category_and_status(app, client):
    """AC1: Dashboard displays total requests and counts grouped by category and status."""
    coord_id = make_user(app, ROLE_COORDINATOR, "dash_cat")
    with app.app_context():
        db.session.add_all([
            ReliefRequest(user_id=coord_id, category="Food", quantity=5, urgency="High", location="Sector A", status="Pending"),
            ReliefRequest(user_id=coord_id, category="Food", quantity=10, urgency="Critical", location="Sector B", status="Assigned"),
            ReliefRequest(user_id=coord_id, category="Water", quantity=20, urgency="Medium", location="Sector C", status="Pending"),
            ReliefRequest(user_id=coord_id, category="Medical Supplies", quantity=2, urgency="High", location="Sector D", status="Fulfilled"),
        ])
        db.session.commit()

        summary = get_dashboard_summary()
        assert summary["requests"]["total"] == 4
        assert summary["requests"]["by_category"]["Food"] == 2
        assert summary["requests"]["by_category"]["Water"] == 1
        assert summary["requests"]["by_category"]["Medical Supplies"] == 1
        assert summary["requests"]["by_status"]["Pending"] == 2
        assert summary["requests"]["by_status"]["Assigned"] == 1
        assert summary["requests"]["by_status"]["Fulfilled"] == 1

    # Verify via API endpoint as well
    login_client(client, coord_id)
    res = client.get("/dashboard/summary")
    assert res.status_code == 200
    data = res.get_json()
    assert data["requests"]["by_category"]["Food"] == 2
    assert data["requests"]["by_status"]["Pending"] == 2


def test_average_response_time_calculation_with_timestamps(app):
    """AC2: Average response time is correctly computed from created_at to assigned_at."""
    t0 = datetime(2026, 11, 1, 10, 0, 0, tzinfo=timezone.utc)
    user_id = make_user(app, ROLE_VICTIM, "art_victim")
    vol_id = make_user(app, ROLE_VOLUNTEER, "art_vol")

    with app.app_context():
        item = InventoryItem(category="Water", quantity=50, storage_location="Warehouse A", threshold=10)
        db.session.add(item)
        db.session.flush()

        # Request 1: assigned 300 seconds later (5 min)
        req1 = ReliefRequest(user_id=user_id, category="Water", quantity=10, location="Loc 1", created_at=t0)
        db.session.add(req1)
        db.session.flush()

        asg1 = Assignment(
            request_id=req1.request_id,
            volunteer_id=vol_id,
            item_id=item.item_id,
            quantity_assigned=10,
            status=STATUS_ASSIGNMENT_ASSIGNED,
            assigned_at=t0 + timedelta(seconds=300),
        )
        db.session.add(asg1)

        # Request 2: assigned 900 seconds later (15 min)
        req2 = ReliefRequest(user_id=user_id, category="Water", quantity=10, location="Loc 2", created_at=t0)
        db.session.add(req2)
        db.session.flush()

        asg2 = Assignment(
            request_id=req2.request_id,
            volunteer_id=vol_id,
            item_id=item.item_id,
            quantity_assigned=10,
            status=STATUS_ASSIGNMENT_ASSIGNED,
            assigned_at=t0 + timedelta(seconds=900),
            completed_at=t0 + timedelta(seconds=1800), # 30 min fulfillment
        )
        db.session.add(asg2)
        db.session.commit()

        summary = get_dashboard_summary()
        analytics = summary["analytics"]

        # Expected average response time = (300 + 900) / 2 = 600.0 seconds = 10.0 minutes
        assert analytics["average_response_time_seconds"] == 600.0
        assert analytics["average_response_time_minutes"] == 10.0

        # Expected average fulfillment time = 1800.0 seconds = 30.0 minutes
        assert analytics["average_fulfillment_time_seconds"] == 1800.0
        assert analytics["average_fulfillment_time_minutes"] == 30.0


def test_resource_utilization_rate_calculation(app):
    """AC3: Resource-utilization rate is calculated: (allocated / total_capacity) * 100."""
    user_id = make_user(app, ROLE_VICTIM, "util_victim")
    vol_id = make_user(app, ROLE_VOLUNTEER, "util_vol")

    with app.app_context():
        # Stock remaining in warehouse: 60 units
        item = InventoryItem(category="Food", quantity=60, storage_location="Central Hub", threshold=20)
        db.session.add(item)
        db.session.flush()

        req = ReliefRequest(user_id=user_id, category="Food", quantity=40, location="Zone A")
        db.session.add(req)
        db.session.flush()

        # Units allocated to field operations: 40 units
        asg = Assignment(
            request_id=req.request_id,
            volunteer_id=vol_id,
            item_id=item.item_id,
            quantity_assigned=40,
            status=STATUS_ASSIGNMENT_ASSIGNED,
        )
        db.session.add(asg)
        db.session.commit()

        # Total available stock = 60
        # Total allocated units = 40
        # Total system capacity = 60 + 40 = 100
        # Expected utilization = (40 / 100) * 100 = 40.0%
        summary = get_dashboard_summary()
        assert summary["analytics"]["total_available_stock"] == 60
        assert summary["analytics"]["total_allocated_units"] == 40
        assert summary["analytics"]["total_system_capacity"] == 100
        assert summary["analytics"]["resource_utilization_rate"] == 40.0
        assert summary["analytics"]["resource_utilization_percent"] == 40.0


def test_empty_datasets_and_zero_denominators_handled_safely(app, client):
    """AC4: Empty database handled safely without DivisionByZero or 500 error."""
    admin_id = make_user(app, ROLE_ADMIN, "empty_admin")
    with app.app_context():
        # Ensure zero requests, zero items, zero assignments
        assert ReliefRequest.query.count() == 0
        assert InventoryItem.query.count() == 0
        assert Assignment.query.count() == 0

        summary = get_dashboard_summary()
        assert summary["requests"]["total"] == 0
        assert summary["inventory"]["total_units"] == 0
        assert summary["analytics"]["average_response_time_seconds"] == 0.0
        assert summary["analytics"]["average_response_time_minutes"] == 0.0
        assert summary["analytics"]["average_fulfillment_time_seconds"] == 0.0
        assert summary["analytics"]["resource_utilization_rate"] == 0.0
        assert summary["analytics"]["resource_utilization_percent"] == 0.0

    login_client(client, admin_id)
    res = client.get("/dashboard/summary")
    assert res.status_code == 200
    assert res.get_json()["analytics"]["resource_utilization_rate"] == 0.0


def test_admin_can_export_relief_requests_csv(app, client):
    """AC5 & AC7: Admin can export relief requests as CSV with correct headers and values."""
    admin_id = make_user(app, ROLE_ADMIN, "csv_admin")
    victim_id = make_user(app, ROLE_VICTIM, "csv_victim")

    with app.app_context():
        db.session.add_all([
            ReliefRequest(
                user_id=victim_id,
                category="Medical Supplies",
                quantity=15,
                urgency="Critical",
                location="Hospital Sector 4",
                latitude=12.9716,
                longitude=77.5946,
                status="Pending",
            ),
            ReliefRequest(
                user_id=victim_id,
                category="Food",
                quantity=50,
                urgency="High",
                location="Relief Camp 2",
                status="Assigned",
            ),
        ])
        db.session.commit()

    login_client(client, admin_id)
    for endpoint in ["/reports/export/relief-requests", "/reports/export/requests", "/dashboard/export/requests"]:
        res = client.get(endpoint)
        assert res.status_code == 200
        assert res.mimetype == "text/csv"
        assert "attachment; filename=relief_requests.csv" in res.headers.get("Content-Disposition", "")

        csv_reader = csv.reader(io.StringIO(res.data.decode("utf-8")))
        rows = list(csv_reader)
        assert len(rows) >= 3  # Header + 2 data rows

        headers = rows[0]
        assert headers == [
            "request_id", "user_id", "category", "quantity", "urgency",
            "location", "latitude", "longitude", "incident_id", "status", "created_at"
        ]

        # Verify values
        row1 = rows[1]
        assert row1[2] == "Medical Supplies"
        assert row1[3] == "15"
        assert row1[4] == "Critical"
        assert row1[5] == "Hospital Sector 4"
        assert "12.9716" in row1[6]
        assert "77.5946" in row1[7]
        assert row1[9] == "Pending"


def test_admin_can_export_inventory_csv(app, client):
    """AC6 & AC7: Admin can export inventory as CSV with correct headers and values."""
    admin_id = make_user(app, ROLE_ADMIN, "inv_admin")

    with app.app_context():
        db.session.add_all([
            InventoryItem(category="Water", quantity=100, storage_location="Warehouse North", threshold=20),
            InventoryItem(category="Blankets & Shelter", quantity=5, storage_location="Hub South", threshold=10),
        ])
        db.session.commit()

    login_client(client, admin_id)
    for endpoint in ["/reports/export/inventory", "/dashboard/export/inventory"]:
        res = client.get(endpoint)
        assert res.status_code == 200
        assert res.mimetype == "text/csv"
        assert "attachment; filename=inventory.csv" in res.headers.get("Content-Disposition", "")

        csv_reader = csv.reader(io.StringIO(res.data.decode("utf-8")))
        rows = list(csv_reader)
        assert len(rows) >= 3

        headers = rows[0]
        assert headers == [
            "item_id", "category", "quantity", "storage_location",
            "expiry_date", "threshold", "is_low_stock"
        ]

        # Row 1 is not low stock (100 > 20)
        row1 = rows[1]
        assert row1[1] == "Water"
        assert row1[2] == "100"
        assert row1[6] == "No"

        # Row 2 is low stock (5 <= 10)
        row2 = rows[2]
        assert row2[1] == "Blankets & Shelter"
        assert row2[2] == "5"
        assert row2[6] == "Yes"


def test_csv_export_access_control_denies_unauthorized_users(app, client):
    """AC8: Unauthenticated users get 401; Victims, Volunteers, and Coordinators get 403."""
    victim_id = make_user(app, ROLE_VICTIM, "no_export_vic")
    vol_id = make_user(app, ROLE_VOLUNTEER, "no_export_vol")
    coord_id = make_user(app, ROLE_COORDINATOR, "no_export_coord")

    endpoints = [
        "/reports/export/requests",
        "/reports/export/inventory",
        "/dashboard/export/requests",
        "/dashboard/export/inventory",
    ]

    for ep in endpoints:
        # Unauthenticated -> 401
        with client.session_transaction() as sess:
            sess.clear()
        res = client.get(ep)
        assert res.status_code == 401

        # Victim -> 403
        login_client(client, victim_id)
        assert client.get(ep).status_code == 403

        # Volunteer -> 403
        login_client(client, vol_id)
        assert client.get(ep).status_code == 403

        # Coordinator -> 403 (Export is Admin-only per FR 3.7.2)
        login_client(client, coord_id)
        assert client.get(ep).status_code == 403


# ============================================================================
# TASK 2: AUTOMATE CRITICAL-SHORTAGE NOTIFICATIONS (SRS FR 3.6.2)
# ============================================================================

def test_shortage_notification_generated_when_stock_at_or_below_threshold_with_pending_requests(app):
    """AC1 & AC2: Shortage alert generated when stock <= threshold AND pending requests exist."""
    coord_id = make_user(app, ROLE_COORDINATOR, "sn_coord")
    admin_id = make_user(app, ROLE_ADMIN, "sn_admin")
    victim_id = make_user(app, ROLE_VICTIM, "sn_victim")

    with app.app_context():
        # Inventory threshold is 10, initial quantity 20
        item = create_inventory_item("Water", 20, "Hub 1", threshold=10)
        # Pending request for Water
        req = create_relief_request(victim_id, "Water", 5, "High", location="Camp 1")

        # Notification count should currently be 0
        assert Notification.query.filter_by(type=NOTIFICATION_CRITICAL_SHORTAGE).count() == 0

        # Reduce stock by 12 -> new quantity is 8 (8 <= 10 -> shortage condition met!)
        update_inventory_stock(item.item_id, -12)

        # Check notifications generated for Coordinator and Admin
        alerts = Notification.query.filter_by(type=NOTIFICATION_CRITICAL_SHORTAGE).all()
        assert len(alerts) == 2

        recipient_ids = {a.user_id for a in alerts}
        assert coord_id in recipient_ids
        assert admin_id in recipient_ids

        for a in alerts:
            assert "Water" in a.message
            assert "CRITICAL SHORTAGE" in a.message
            assert a.is_read is False


def test_shortage_without_matching_pending_requests_does_not_alert(app):
    """AC3: Shortages without matching pending requests do NOT generate request alerts."""
    make_user(app, ROLE_COORDINATOR, "sn_coord_nomatch")
    make_user(app, ROLE_ADMIN, "sn_admin_nomatch")

    with app.app_context():
        # Inventory is below threshold (5 <= 10)
        item = create_inventory_item("Food", 5, "Hub 2", threshold=10)

        # But NO pending requests exist for Food
        alerts = check_and_notify_critical_shortage(category="Food")
        assert len(alerts) == 0
        assert Notification.query.filter_by(type=NOTIFICATION_CRITICAL_SHORTAGE).count() == 0


def test_non_shortage_scenario_above_threshold_does_not_alert(app):
    """AC6: Inventory strictly above threshold does NOT generate shortage alerts."""
    make_user(app, ROLE_COORDINATOR, "sn_coord_healthy")
    victim_id = make_user(app, ROLE_VICTIM, "sn_vic_healthy")

    with app.app_context():
        # Stock is 50, threshold is 10 (50 > 10)
        create_inventory_item("Water", 50, "Hub 3", threshold=10)
        # Pending request exists
        create_relief_request(victim_id, "Water", 5, "High", location="Camp 2")

        # Stock is well above threshold; no shortage
        alerts = check_and_notify_critical_shortage(category="Water")
        assert len(alerts) == 0
        assert Notification.query.filter_by(type=NOTIFICATION_CRITICAL_SHORTAGE).count() == 0


def test_exact_threshold_boundary_conditions(app):
    """AC6: Verify boundary behavior: quantity == threshold vs quantity == threshold + 1."""
    make_user(app, ROLE_COORDINATOR, "sn_coord_bound")
    victim_id = make_user(app, ROLE_VICTIM, "sn_vic_bound")

    with app.app_context():
        # Case 1: Threshold = 10, Quantity = 11 (11 > 10 -> No shortage)
        item1 = create_inventory_item("Medical Supplies", 11, "Hub Med", threshold=10)
        create_relief_request(victim_id, "Medical Supplies", 2, "High", location="Med Clinic")

        alerts1 = check_and_notify_critical_shortage(category="Medical Supplies")
        assert len(alerts1) == 0

        # Case 2: Reduce quantity to exactly 10 (10 <= 10 -> Boundary reached!)
        update_inventory_stock(item1.item_id, -1)
        alerts2 = Notification.query.filter_by(type=NOTIFICATION_CRITICAL_SHORTAGE).all()
        assert len(alerts2) >= 1
        assert any("Medical Supplies" in a.message for a in alerts2)


def test_unauthorized_recipients_do_not_receive_shortage_alerts(app):
    """AC4: Victims and Volunteers do NOT receive restricted operational shortage alerts."""
    coord_id = make_user(app, ROLE_COORDINATOR, "sn_op_coord")
    admin_id = make_user(app, ROLE_ADMIN, "sn_op_admin")
    volunteer_id = make_user(app, ROLE_VOLUNTEER, "sn_op_vol")
    victim_id = make_user(app, ROLE_VICTIM, "sn_op_vic")

    with app.app_context():
        item = create_inventory_item("Clothing", 20, "Hub Cloth", threshold=10)
        create_relief_request(victim_id, "Clothing", 5, "Low", location="Shelter A")

        # Drop stock to 5 (<= 10)
        update_inventory_stock(item.item_id, -15)

        # Check all notifications
        vic_shortage_notifs = Notification.query.filter_by(user_id=victim_id, type=NOTIFICATION_CRITICAL_SHORTAGE).all()
        vol_shortage_notifs = Notification.query.filter_by(user_id=volunteer_id, type=NOTIFICATION_CRITICAL_SHORTAGE).all()
        coord_shortage_notifs = Notification.query.filter_by(user_id=coord_id, type=NOTIFICATION_CRITICAL_SHORTAGE).all()
        admin_shortage_notifs = Notification.query.filter_by(user_id=admin_id, type=NOTIFICATION_CRITICAL_SHORTAGE).all()

        assert len(vic_shortage_notifs) == 0
        assert len(vol_shortage_notifs) == 0
        assert len(coord_shortage_notifs) == 1
        assert len(admin_shortage_notifs) == 1


def test_repeated_operations_do_not_duplicate_shortage_notifications(app):
    """AC5: Repeated operations do not generate duplicate alerts for unchanged shortage."""
    make_user(app, ROLE_COORDINATOR, "sn_dedup_coord")
    victim_id = make_user(app, ROLE_VICTIM, "sn_dedup_vic")

    with app.app_context():
        item = create_inventory_item("Sanitation & Hygiene", 20, "Hub San", threshold=10)
        create_relief_request(victim_id, "Sanitation & Hygiene", 5, "Medium", location="San Camp")

        # Initial trigger: stock falls to 8
        update_inventory_stock(item.item_id, -12)
        initial_count = Notification.query.filter_by(type=NOTIFICATION_CRITICAL_SHORTAGE).count()
        assert initial_count >= 1

        # Second operation while unread: another small stock deduction to 7
        update_inventory_stock(item.item_id, -1)
        subsequent_count = Notification.query.filter_by(type=NOTIFICATION_CRITICAL_SHORTAGE).count()
        # Count must remain unchanged because previous alert is still unread
        assert subsequent_count == initial_count

        # Manual trigger check also does not duplicate
        check_and_notify_critical_shortage(category="Sanitation & Hygiene")
        assert Notification.query.filter_by(type=NOTIFICATION_CRITICAL_SHORTAGE).count() == initial_count


def test_replenishment_and_subsequent_shortage_allows_new_notification(app):
    """AC5: Once an alert is acknowledged/read and stock drops again, a new alert is permitted."""
    coord_id = make_user(app, ROLE_COORDINATOR, "sn_ack_coord")
    victim_id = make_user(app, ROLE_VICTIM, "sn_ack_vic")

    with app.app_context():
        item = create_inventory_item("Food & Water", 10, "Hub FW", threshold=5)
        create_relief_request(victim_id, "Food & Water", 2, "High", location="Camp FW")

        # Trigger shortage: stock drops to 3
        update_inventory_stock(item.item_id, -7)
        notif = Notification.query.filter_by(user_id=coord_id, type=NOTIFICATION_CRITICAL_SHORTAGE).first()
        assert notif is not None

        # Coordinator marks notification as read
        notif.is_read = True
        db.session.commit()

        # Stock drops further or new event occurs: now that it is read, a new alert can be dispatched
        created = check_and_notify_critical_shortage(category="Food & Water")
        assert len(created) >= 1


def test_allocation_automatically_triggers_shortage_notification(app):
    """AC1: allocate_request stock deduction automatically checks threshold and alerts."""
    coord_id = make_user(app, ROLE_COORDINATOR, "sn_alloc_coord")
    victim_id = make_user(app, ROLE_VICTIM, "sn_alloc_vic")
    vol_id = make_user(app, ROLE_VOLUNTEER, "sn_alloc_vol")

    with app.app_context():
        item = create_inventory_item("Rescue", 20, "Hub Rescue", threshold=10)
        req1 = create_relief_request(victim_id, "Rescue", 12, "Critical", location="Zone Res 1")
        req2 = create_relief_request(victim_id, "Rescue", 5, "High", location="Zone Res 2")

        # Initial stock: 20 > 10 (no alert yet)
        assert Notification.query.filter_by(type=NOTIFICATION_CRITICAL_SHORTAGE).count() == 0

        # Allocate request 1: deducts 12 units -> remaining stock = 8 (<= 10)
        # Note: req2 is still Pending for category "Rescue"!
        allocate_request(request_id=req1.request_id, volunteer_id=vol_id, item_id=item.item_id)

        # Critical shortage should have automatically triggered
        alerts = Notification.query.filter_by(type=NOTIFICATION_CRITICAL_SHORTAGE).all()
        assert len(alerts) >= 1
        assert any("Rescue" in a.message for a in alerts)


def test_new_pending_request_triggers_shortage_if_stock_already_low(app):
    """AC1: Submitting a new pending request when stock is already low triggers shortage alert."""
    coord_id = make_user(app, ROLE_COORDINATOR, "sn_newreq_coord")
    victim_id = make_user(app, ROLE_VICTIM, "sn_newreq_vic")

    with app.app_context():
        # Stock is low (4 <= 10), but initially 0 pending requests (so NO alert generated yet)
        create_inventory_item("Shelter", 4, "Hub Shelter", threshold=10)
        assert Notification.query.filter_by(type=NOTIFICATION_CRITICAL_SHORTAGE).count() == 0

        # Victim submits a new pending relief request for Shelter
        create_relief_request(victim_id, "Shelter", 3, "High", location="Flood Camp 9")

        # Now condition (stock <= threshold AND pending > 0) is met!
        alerts = Notification.query.filter_by(type=NOTIFICATION_CRITICAL_SHORTAGE).all()
        assert len(alerts) >= 1
        assert any("Shelter" in a.message for a in alerts)
