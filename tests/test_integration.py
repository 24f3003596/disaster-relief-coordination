"""
Integration and End-to-End Workflow Testing for SE Project Review 2.
"""

import pytest
from extensions import db
from models import User, InventoryItem, ReliefRequest, Assignment, Notification
from auth import register_user
from inventory import create_inventory_item
from requests_module import create_relief_request
from assignments import allocate_request, complete_assignment
from dashboard import get_dashboard_summary
from constants import (
    ROLE_COORDINATOR,
    ROLE_VOLUNTEER,
    ROLE_VICTIM,
    CATEGORY_FOOD_WATER,
    URGENCY_CRITICAL,
    STATUS_REQUEST_ASSIGNED,
    STATUS_REQUEST_FULFILLED,
    STATUS_REQUEST_COMPLETED,
    STATUS_ASSIGNMENT_ASSIGNED,
    STATUS_ASSIGNMENT_COMPLETED,
    NOTIFICATION_ASSIGNMENT,
)

def test_main_pages_load(client):
    """Public pages stay reachable; sensitive request records require login."""
    for path in ['/', '/register', '/login', '/inventory', '/assignments', '/volunteers', '/notifications', '/alerts', '/incidents', '/reports']:
        response = client.get(path)
        assert response.status_code == 200, f"Failed loading {path}: status {response.status_code}"
    assert client.get('/requests').status_code == 401

def test_end_to_end_relief_workflow(app):
    with app.app_context():
        # Step 1: Register Users
        coordinator = register_user(
            name="Relief Coordinator",
            email="coordinator@relief.org",
            password="secure-password-123",
            phone="9876543210",
            role=ROLE_COORDINATOR,
        )
        volunteer = register_user(
            name="Field Volunteer",
            email="volunteer@relief.org",
            password="secure-password-123",
            phone="9876543211",
            role=ROLE_VOLUNTEER,
        )
        victim = register_user(
            name="Victim Citizen",
            email="victim@citizen.org",
            password="secure-password-123",
            phone="9876543212",
            role=ROLE_VICTIM,
        )

        assert coordinator.user_id is not None
        assert volunteer.user_id is not None
        assert victim.user_id is not None

        # Step 2: Register Inventory Resource
        initial_stock = 200
        threshold_val = 30
        item = create_inventory_item(
            category=CATEGORY_FOOD_WATER,
            quantity=initial_stock,
            storage_location="Central Disaster Warehouse Sector 1",
            threshold=threshold_val,
        )
        assert item.item_id is not None
        assert item.quantity == 200

        # Step 3: Victim Submits Relief Request
        requested_qty = 25
        req = create_relief_request(
            user_id=victim.user_id,
            category=CATEGORY_FOOD_WATER,
            quantity=requested_qty,
            urgency=URGENCY_CRITICAL,
            latitude=13.0827,
            longitude=80.2707,
            location="Emergency Camp 4, North Sector",
        )
        assert req.request_id is not None
        assert req.status == "Pending"

        # Step 4: Coordinator Allocates Inventory and Assigns Volunteer
        assignment = allocate_request(
            request_id=req.request_id,
            volunteer_id=volunteer.user_id,
            item_id=item.item_id,
        )

        # Step 5: Verify Atomic Inventory Stock Deduction
        db.session.refresh(item)
        db.session.refresh(req)
        assert item.quantity == (initial_stock - requested_qty)  # 200 - 25 = 175
        assert req.status in (STATUS_REQUEST_ASSIGNED, "Allocated")
        assert assignment.status == STATUS_ASSIGNMENT_ASSIGNED
        assert assignment.quantity_assigned == requested_qty

        # Step 6: Verify Automated Notifications Generated
        vol_notif = Notification.query.filter_by(user_id=volunteer.user_id).first()
        assert vol_notif is not None
        assert vol_notif.type == NOTIFICATION_ASSIGNMENT

        victim_notif = Notification.query.filter_by(user_id=victim.user_id).first()
        assert victim_notif is not None
        assert "allocated" in victim_notif.message.lower() or "assigned" in victim_notif.message.lower()

        # Step 7: Volunteer Completes Assignment Delivery
        completed_task = complete_assignment(assignment.task_id)
        db.session.refresh(req)
        assert completed_task.status == STATUS_ASSIGNMENT_COMPLETED
        assert completed_task.completed_at is not None
        assert req.status in (STATUS_REQUEST_FULFILLED, STATUS_REQUEST_COMPLETED)

        # Step 8: Verify Dashboard KPI Reflects Completed Workflow
        dashboard = get_dashboard_summary()
        assert dashboard["requests"]["total"] == 1
        assert dashboard["inventory"]["total_units"] == 175
        assert dashboard["volunteers"]["total_count"] == 1

def test_allocation_insufficient_stock_fails_atomically(app):
    with app.app_context():
        volunteer = register_user(
            name="Field Volunteer 2",
            email="vol2@relief.org",
            password="secure-password-123",
            role=ROLE_VOLUNTEER,
        )
        victim = register_user(
            name="Victim 2",
            email="victim2@citizen.org",
            password="secure-password-123",
            role=ROLE_VICTIM,
        )
        item = create_inventory_item(
            category=CATEGORY_FOOD_WATER,
            quantity=10,
            storage_location="Depot",
            threshold=5,
        )
        req = create_relief_request(
            user_id=victim.user_id,
            category=CATEGORY_FOOD_WATER,
            quantity=50,
            urgency=URGENCY_CRITICAL,
        )

        with pytest.raises(ValueError, match="Insufficient"):
            allocate_request(
                request_id=req.request_id,
                volunteer_id=volunteer.user_id,
                item_id=item.item_id,
            )

        # Confirm rollback / no changes occurred
        db.session.refresh(item)
        db.session.refresh(req)
        assert item.quantity == 10
        assert req.status == "Pending"
        assert Assignment.query.filter_by(request_id=req.request_id).first() is None

def test_automated_workflow_via_http_client(client, app):
    # 1. Register users via HTTP API
    reg_coord = client.post("/auth/register", json={
        "name": "HTTP Coordinator",
        "email": "http_coord@test.org",
        "password": "strong-password-1",
        "role": "Coordinator"
    })
    reg_vic = client.post("/auth/register", json={
        "name": "HTTP Victim",
        "email": "http_victim@test.org",
        "password": "strong-password-1",
    })
    assert reg_coord.status_code == 201
    assert reg_vic.status_code == 201
    assert reg_coord.json["user"]["role"] == ROLE_VICTIM
    assert reg_vic.json["user"]["role"] == ROLE_VICTIM
    coord_id = reg_coord.json["user"]["user_id"]
    vic_id = reg_vic.json["user"]["user_id"]

    with app.app_context():
        admin = register_user(
            name="Provisioned HTTP Admin",
            email="http_admin@test.org",
            password="strong-password-1",
            role="Admin",
        )
        vol = register_user(
            name="HTTP Volunteer",
            email="http_vol@test.org",
            password="strong-password-1",
            role=ROLE_VOLUNTEER,
        )
        admin_email = admin.email
        vol_id = vol.user_id

    # Public registration cannot assign Coordinator or Volunteer permissions.
    # Promote accounts through the Admin-protected role-management endpoint.
    admin_login = client.post("/auth/login", json={
        "email": admin_email, "password": "strong-password-1"
    })
    assert admin_login.status_code == 200
    coord_promotion = client.patch(
        f"/auth/users/{coord_id}/role", json={"role": ROLE_COORDINATOR}
    )
    volunteer_promotion = client.patch(
        f"/auth/users/{vol_id}/role", json={"role": ROLE_VOLUNTEER}
    )
    assert coord_promotion.status_code == 200
    assert volunteer_promotion.status_code == 200

    # 2. Coordinator registers inventory
    with client.session_transaction() as sess:
        sess["user_id"] = coord_id

    inv_res = client.post("/inventory/", json={
        "category": "Medical Supplies",
        "quantity": 100,
        "storage_location": "Field Hospital Alpha",
        "threshold": 20,
    })
    assert inv_res.status_code == 201
    item_id = inv_res.json["item"]["item_id"]

    # 3. Victim places request
    with client.session_transaction() as sess:
        sess["user_id"] = vic_id

    req_res = client.post("/requests/", json={
        "category": "Medical Supplies",
        "quantity": 15,
        "urgency": "Critical",
        "latitude": 13.04,
        "longitude": 80.25,
        "location": "Relief Tent 2",
    })
    assert req_res.status_code == 201
    request_id = req_res.json["request"]["request_id"]

    # 4. Coordinator allocates
    with client.session_transaction() as sess:
        sess["user_id"] = coord_id

    alloc_res = client.post("/assignments/allocate", json={
        "request_id": request_id,
        "volunteer_id": vol_id,
        "item_id": item_id,
    })
    assert alloc_res.status_code == 201
    task_id = alloc_res.json["assignment"]["task_id"]

    # 5. Volunteer views notifications
    with client.session_transaction() as sess:
        sess["user_id"] = vol_id

    notif_res = client.get("/notifications/")
    assert notif_res.status_code == 200
    assert len(notif_res.json["notifications"]) >= 1

    # 6. Volunteer completes task
    comp_res = client.post(f"/assignments/{task_id}/complete")
    assert comp_res.status_code == 200
    assert comp_res.json["assignment"]["status"] == "Completed"
