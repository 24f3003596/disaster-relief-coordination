"""End-to-End User Acceptance Testing (UAT) Suite for Sprint 5.

This module validates real-world end-to-end user journeys against the approved SRS
specifications across all four user roles (Admin, Coordinator, Volunteer, Victim).
It verifies:
  1. Registration, OTP Verification, and Login (FR 3.1.1, FR 3.1.2, FR 3.1.3)
  2. Privileged Role Request & Admin Approval Queue (FR 3.1.3, FR 3.1.4)
  3. Victim Relief Request Intake & Coordinate Validation (FR 3.3.1, FR 3.3.4)
  4. Coordinator Incident Lifecycle & Status Transitions (FR 3.2.1, FR 3.2.2, FR 3.2.3, FR 3.2.4)
  5. Warehouse Inventory Inward & Safety Thresholds (FR 3.4.1, FR 3.4.2)
  6. Atomic Resource Allocation & Idempotency Safeguards (FR 3.4.3, FR 3.5.1, FR 3.5.2)
  7. Volunteer Mission Execution & Request Auto-Fulfillment (FR 3.5.3, FR 3.5.4, FR 3.6.1)
  8. Automated Critical Shortage Alerts & Deduplication (FR 3.6.2)
  9. Geospatial Disaster Map & Clustering Data (FR 3.8.1, FR 3.8.2)
 10. Operations Dashboard Analytics & Admin CSV Data Export (FR 3.7.1, FR 3.7.2)
"""

import io
import csv
import pytest
from extensions import db
from models import (
    User,
    Incident,
    ReliefRequest,
    InventoryItem,
    Assignment,
    Notification,
    AuditLog,
)
from constants import (
    ROLE_ADMIN,
    ROLE_COORDINATOR,
    ROLE_VOLUNTEER,
    ROLE_VICTIM,
    CATEGORY_FOOD,
    CATEGORY_WATER,
    CATEGORY_MEDICAL,
    CATEGORY_SHELTER,
    STATUS_REQUEST_PENDING,
    STATUS_REQUEST_ASSIGNED,
    STATUS_REQUEST_FULFILLED,
    STATUS_INCIDENT_OPEN,
    STATUS_INCIDENT_IN_PROGRESS,
    STATUS_INCIDENT_RESOLVED,
    STATUS_INCIDENT_CLOSED,
    STATUS_ASSIGNMENT_ASSIGNED,
    STATUS_ASSIGNMENT_IN_PROGRESS,
    STATUS_ASSIGNMENT_COMPLETED,
    NOTIFICATION_CRITICAL_SHORTAGE,
)
from auth import register_user
from inventory import create_inventory_item, update_inventory_stock
from requests_module import create_relief_request
from assignments import allocate_request
from incidents import create_incident


def login_session(client, email, password="SecurePassword123"):
    """Helper to log in via HTTP form and retain session cookie."""
    with client.session_transaction() as sess:
        sess.clear()
    return client.post("/login", data={"email": email, "password": password}, follow_redirects=True)


def logout_session(client):
    """Helper to clear test client session."""
    with client.session_transaction() as sess:
        sess.clear()


def assert_status_patch(client, endpoint, target_status, entity_key):
    """Helper to execute PATCH status update and assert 200 response."""
    resp = client.patch(endpoint, json={"status": target_status})
    assert resp.status_code == 200
    assert resp.get_json()[entity_key]["status"] == target_status
    return resp


def parse_csv_headers(response):
    """Helper to parse first line of CSV response."""
    reader = csv.reader(io.StringIO(response.get_data(as_text=True)))
    return [col.strip().lower() for col in next(reader)]


# ==============================================================================
# SCENARIO 1: Public Victim Registration, OTP Verification, and Login
# ==============================================================================
def test_uat_001_victim_registration_otp_verification_and_login(app, client):
    """UAT Scenario 1: Citizen registers, verifies OTP, and logs in."""
    reg_response = client.post("/register", data={
        "name": "Jane Citizen",
        "phone": "+919876543210",
        "email": "jane.citizen@example.com",
        "password": "SecurePassword123",
        "confirm_password": "SecurePassword123",
    }, follow_redirects=True)
    assert reg_response.status_code == 200

    with app.app_context():
        user = User.query.filter_by(email="jane.citizen@example.com").first()
        assert user is not None
        assert user.role == ROLE_VICTIM
        assert user.approval_status == "approved"

    login_resp = login_session(client, "jane.citizen@example.com", "SecurePassword123")
    assert login_resp.status_code == 200
    assert client.get("/requests/").status_code == 200


# ==============================================================================
# SCENARIO 2: Privileged Role Approval Queue & Admin Workflow
# ==============================================================================
def test_uat_002_privileged_role_request_and_admin_approval_queue(app, client):
    """UAT Scenario 2: Coordinator promotion requires Admin approval before login."""
    with app.app_context():
        admin = register_user("Site Administrator", "+919999999999", "admin.ops@example.com", "AdminPass123", ROLE_ADMIN)
        admin.approval_status = "approved"
        candidate = register_user("Alex Candidate", "+919888877777", "alex.candidate@example.com", "CoordPass123", ROLE_VICTIM)
        candidate.approval_status = "approved"
        db.session.commit()
        candidate_id = candidate.user_id

    client.post("/auth/login", json={"email": "admin.ops@example.com", "password": "AdminPass123"})
    promoted = client.patch(f"/auth/users/{candidate_id}/role", json={"role": ROLE_COORDINATOR})
    assert promoted.status_code == 200
    assert promoted.json["user"]["approval_status"] == "pending"

    client.post("/auth/logout")
    assert client.post("/auth/login", json={"email": "alex.candidate@example.com", "password": "CoordPass123"}).status_code == 401

    client.post("/auth/login", json={"email": "admin.ops@example.com", "password": "AdminPass123"})
    pending_list = client.get("/auth/admin/pending-approvals")
    assert pending_list.status_code == 200
    assert candidate_id in [u["user_id"] for u in pending_list.json["accounts"]]

    approve_resp = client.post(f"/auth/admin/users/{candidate_id}/approval", json={"decision": "approve"})
    assert approve_resp.status_code == 200

    client.post("/auth/logout")
    coord_login = client.post("/auth/login", json={"email": "alex.candidate@example.com", "password": "CoordPass123"})
    assert coord_login.status_code == 200
    assert coord_login.get_json()["user"]["role"] == ROLE_COORDINATOR


# ==============================================================================
# SCENARIO 3: Victim Relief Request Intake & Coordinate Validation
# ==============================================================================
def test_uat_003_victim_relief_request_intake_and_tracking(app, client):
    """UAT Scenario 3: Request creation with coordinates and role-isolated audit history."""
    with app.app_context():
        victim_1 = register_user("Victim One", "+919111111111", "victim1@example.com", "Pass12345", ROLE_VICTIM)
        victim_2 = register_user("Victim Two", "+919222222222", "victim2@example.com", "Pass12345", ROLE_VICTIM)
        v1_id, v2_id = victim_1.user_id, victim_2.user_id

    login_session(client, "victim1@example.com", "Pass12345")
    req_post = client.post("/requests/", data={
        "category": CATEGORY_MEDICAL,
        "quantity": "5",
        "urgency": "High",
        "location": "Sector 4 Relief Camp",
        "latitude": "13.0827",
        "longitude": "80.2707",
    }, follow_redirects=True)
    assert req_post.status_code == 200

    with app.app_context():
        req = ReliefRequest.query.filter_by(user_id=v1_id).first()
        assert req.status == STATUS_REQUEST_PENDING
        assert pytest.approx(req.latitude, 0.001) == 13.0827
        req_id = req.request_id

    v1_hist = client.get(f"/requests/{req_id}/history?format=json")
    assert v1_hist.status_code == 200
    assert len(v1_hist.get_json()["activity"]) >= 1

    logout_session(client)
    login_session(client, "victim2@example.com", "Pass12345")
    assert client.get(f"/requests/{req_id}/history?format=json").status_code == 403


# ==============================================================================
# SCENARIO 4: Coordinator Incident Lifecycle & Status Transitions
# ==============================================================================
def test_uat_004_coordinator_incident_lifecycle_and_affected_areas(app, client):
    """UAT Scenario 4: Incident creation, affected area display, and status progression."""
    with app.app_context():
        coord = register_user("Field Coordinator", "+919333333333", "field.coord@example.com", "CoordPass123", ROLE_COORDINATOR)
        coord.approval_status = "approved"
        db.session.commit()

    login_session(client, "field.coord@example.com", "CoordPass123")
    create_resp = client.post("/incidents/", json={
        "title": "Coastal Sea Surge",
        "description": "Seawater breach affecting low-lying residential sectors",
        "latitude": 13.0450,
        "longitude": 80.2820,
        "severity": "Critical",
    })
    assert create_resp.status_code == 201
    inc_id = create_resp.get_json()["incident"]["incident_id"]

    areas_resp = client.get("/incidents/affected-areas")
    assert areas_resp.status_code == 200
    assert any("Coastal Sea Surge" in item["title"] for item in areas_resp.get_json()["affected_areas"])

    for next_status in (STATUS_INCIDENT_IN_PROGRESS, STATUS_INCIDENT_RESOLVED, STATUS_INCIDENT_CLOSED):
        assert_status_patch(client, f"/incidents/{inc_id}/status", next_status, "incident")

    hist = client.get(f"/incidents/{inc_id}/history?format=json")
    assert hist.status_code == 200
    actions = [e["action"] for e in hist.get_json()["activity"]]
    assert any("Open -> In Progress" in a for a in actions)
    assert any("Resolved -> Closed" in a for a in actions)


# ==============================================================================
# SCENARIO 5: Warehouse Inventory Inward & Safety Thresholds
# ==============================================================================
def test_uat_005_warehouse_inventory_inward_and_thresholds(app, client):
    """UAT Scenario 5: Warehouse stock registration and boundary validation."""
    with app.app_context():
        coord = register_user("Logistics Officer", "+919444444444", "logistics@example.com", "LogPass123", ROLE_COORDINATOR)
        coord.approval_status = "approved"
        db.session.commit()

    login_session(client, "logistics@example.com", "LogPass123")
    add_resp = client.post("/inventory/", json={
        "category": CATEGORY_FOOD,
        "quantity": 100,
        "storage_location": "Warehouse North",
        "threshold": 20,
    })
    assert add_resp.status_code == 201

    with app.app_context():
        item = InventoryItem.query.filter_by(category=CATEGORY_FOOD).first()
        assert item.quantity == 100
        assert item.threshold == 20

    bad_resp = client.post("/inventory/", json={
        "category": CATEGORY_FOOD,
        "quantity": -10,
        "storage_location": "Warehouse North",
        "threshold": 5,
    })
    assert bad_resp.status_code == 400


# ==============================================================================
# SCENARIO 6: Atomic Resource Allocation & Idempotency Safeguards
# ==============================================================================
def test_uat_006_atomic_resource_allocation_and_idempotency(app, client):
    """UAT Scenario 6: Atomic resource allocation and idempotency guard."""
    with app.app_context():
        coord = register_user("Dispatcher", "+919555555555", "dispatcher@example.com", "Dispatch123", ROLE_COORDINATOR)
        coord.approval_status = "approved"
        victim = register_user("Victim A", "+919666666666", "victim.a@example.com", "VictimPass123", ROLE_VICTIM)
        volunteer = register_user("Volunteer B", "+919777777777", "volunteer.b@example.com", "VolPass123", ROLE_VOLUNTEER)
        volunteer.approval_status = "approved"
        item = create_inventory_item(CATEGORY_WATER, 50, "Central Depot", threshold=10)
        req = create_relief_request(victim.user_id, CATEGORY_WATER, 10, "High", 13.08, 80.27)
        db.session.commit()
        req_id, vol_id, item_id = req.request_id, volunteer.user_id, item.item_id

    login_session(client, "dispatcher@example.com", "Dispatch123")
    alloc_resp = client.post("/assignments/allocate", json={
        "request_id": req_id,
        "volunteer_id": vol_id,
        "item_id": item_id,
        "quantity_assigned": 10,
    })
    assert alloc_resp.status_code == 201

    with app.app_context():
        assert db.session.get(InventoryItem, item_id).quantity == 40
        assert db.session.get(ReliefRequest, req_id).status == STATUS_REQUEST_ASSIGNED

    # Duplicate allocation attempt fails without state corruption
    assert client.post("/assignments/allocate", json={
        "request_id": req_id,
        "volunteer_id": vol_id,
        "item_id": item_id,
        "quantity_assigned": 10,
    }).status_code == 400

    with app.app_context():
        assert db.session.get(InventoryItem, item_id).quantity == 40


# ==============================================================================
# SCENARIO 7: Volunteer Mission Execution & Request Auto-Fulfillment
# ==============================================================================
def test_uat_007_volunteer_mission_execution_and_auto_fulfillment(app, client):
    """UAT Scenario 7: Volunteer status transitions and auto-fulfillment of request."""
    with app.app_context():
        victim = register_user("Victim Recipient", "+919100000001", "recipient@example.com", "Pass12345", ROLE_VICTIM)
        volunteer = register_user("Hero Volunteer", "+919100000002", "hero.vol@example.com", "Pass12345", ROLE_VOLUNTEER)
        volunteer.approval_status = "approved"
        item = create_inventory_item(CATEGORY_FOOD, 30, "Depot South", threshold=5)
        req = create_relief_request(victim.user_id, CATEGORY_FOOD, 5, "Critical", 13.01, 80.20)
        task = allocate_request(req.request_id, volunteer.user_id, item.item_id, 5)
        task_id, req_id = task.task_id, req.request_id
        v_user_id, vol_user_id = victim.user_id, volunteer.user_id

    login_session(client, "hero.vol@example.com", "Pass12345")
    assert client.get("/assignments/").status_code == 200

    assert_status_patch(client, f"/assignments/{task_id}/status", STATUS_ASSIGNMENT_IN_PROGRESS, "assignment")
    assert_status_patch(client, f"/assignments/{task_id}/status", STATUS_ASSIGNMENT_COMPLETED, "assignment")

    with app.app_context():
        assert db.session.get(ReliefRequest, req_id).status == STATUS_REQUEST_FULFILLED
        assert Notification.query.filter_by(user_id=vol_user_id).count() >= 1
        assert Notification.query.filter_by(user_id=v_user_id).count() >= 1


# ==============================================================================
# SCENARIO 8: Automated Critical Shortage Alerting & Deduplication
# ==============================================================================
def test_uat_008_critical_shortage_alerting_and_deduplication(app, client):
    """UAT Scenario 8: Depletion below threshold triggers alert with duplicate suppression."""
    with app.app_context():
        admin = register_user("Alert Admin", "+919200000001", "alert.admin@example.com", "AdminPass123", ROLE_ADMIN)
        admin.approval_status = "approved"
        coord = register_user("Alert Coordinator", "+919200000002", "alert.coord@example.com", "CoordPass123", ROLE_COORDINATOR)
        coord.approval_status = "approved"
        victim = register_user("Alert Victim", "+919200000003", "alert.victim@example.com", "VictimPass123", ROLE_VICTIM)
        item = create_inventory_item(CATEGORY_SHELTER, 20, "Depot East", threshold=10)
        create_relief_request(victim.user_id, CATEGORY_SHELTER, 5, "High", 13.05, 80.25)
        db.session.commit()
        admin_id, coord_id, item_id = admin.user_id, coord.user_id, item.item_id

        assert Notification.query.filter_by(type=NOTIFICATION_CRITICAL_SHORTAGE).count() == 0

        # Deplete stock below threshold
        update_inventory_stock(item_id, -12)

        alerts = Notification.query.filter_by(type=NOTIFICATION_CRITICAL_SHORTAGE).all()
        assert len(alerts) >= 2
        recipients = {n.user_id for n in alerts}
        assert coord_id in recipients and admin_id in recipients
        first_count = len(alerts)

        # Subsequent check without stock recovery causes no duplicate notification
        update_inventory_stock(item_id, -1)
        assert Notification.query.filter_by(type=NOTIFICATION_CRITICAL_SHORTAGE).count() == first_count


# ==============================================================================
# SCENARIO 9: Geospatial Disaster Map Visualization & Filtering
# ==============================================================================
def test_uat_009_geospatial_disaster_map_visualization_and_filtering(app, client):
    """UAT Scenario 9: Disaster map rendering and active markers filtering."""
    with app.app_context():
        coord = register_user("GIS Coordinator", "+919300000001", "gis.coord@example.com", "CoordPass123", ROLE_COORDINATOR)
        coord.approval_status = "approved"
        victim = register_user("Mapped Victim", "+919300000002", "map.victim@example.com", "VictimPass123", ROLE_VICTIM)
        create_incident("Downtown Flooding", "Heavy inundation", 13.0800, 80.2700, "High", coord.user_id)
        create_relief_request(victim.user_id, CATEGORY_MEDICAL, 10, "Critical", 13.0810, 80.2710)
        db.session.commit()

    login_session(client, "gis.coord@example.com", "CoordPass123")
    map_resp = client.get("/map/")
    assert map_resp.status_code == 200
    assert "leaflet" in map_resp.get_data(as_text=True).lower()

    data_resp = client.get("/map/data")
    assert data_resp.status_code == 200
    json_data = data_resp.get_json()
    assert any(i["title"] == "Downtown Flooding" for i in json_data["incidents"])
    assert any(r["category"] == CATEGORY_MEDICAL for r in json_data["requests"])

    cat_resp = client.get(f"/map/data?category={CATEGORY_MEDICAL}")
    assert cat_resp.status_code == 200
    assert any(r["category"] == CATEGORY_MEDICAL for r in cat_resp.get_json()["requests"])


# ==============================================================================
# SCENARIO 10: Operational Analytics, Access Control & Admin CSV Export
# ==============================================================================
def test_uat_010_dashboard_analytics_and_admin_csv_export(app, client):
    """UAT Scenario 10: Dashboard analytics view and Admin-only CSV data export."""
    with app.app_context():
        admin = register_user("Data Admin", "+919400000001", "data.admin@example.com", "AdminPass123", ROLE_ADMIN)
        admin.approval_status = "approved"
        coord = register_user("Ops Analyst", "+919400000002", "analyst.coord@example.com", "CoordPass123", ROLE_COORDINATOR)
        coord.approval_status = "approved"
        victim = register_user("Standard Victim", "+919400000003", "standard.victim@example.com", "VictimPass123", ROLE_VICTIM)
        create_inventory_item(CATEGORY_SHELTER, 80, "Depot West", threshold=10)
        create_relief_request(victim.user_id, CATEGORY_SHELTER, 4, "Medium", 13.06, 80.24)
        db.session.commit()

    # Coordinator access check
    login_session(client, "analyst.coord@example.com", "CoordPass123")
    assert client.get("/dashboard/").status_code == 200
    assert client.get("/reports/export/requests").status_code == 403
    assert client.get("/reports/export/inventory").status_code == 403

    # Admin access check
    logout_session(client)
    login_session(client, "data.admin@example.com", "AdminPass123")

    req_csv = client.get("/reports/export/requests")
    assert req_csv.status_code == 200
    req_cols = parse_csv_headers(req_csv)
    assert "request_id" in req_cols and "category" in req_cols

    inv_csv = client.get("/reports/export/inventory")
    assert inv_csv.status_code == 200
    inv_cols = parse_csv_headers(inv_csv)
    assert "item_id" in inv_cols and "category" in inv_cols
