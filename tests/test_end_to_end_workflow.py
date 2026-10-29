
"""End-to-end Flask client test for the relief allocation workflow."""

from auth import register_user
from extensions import db
from models import User, InventoryItem, ReliefRequest, Assignment, Notification


def test_register_request_allocate_complete_and_notify(client, app):
    # 1. Register a Victim.
    response = client.post("/register", data={
        "name": "Test Victim",
        "phone": "9000000001",
        "email": "victim-flow@example.com",
        "password": "testpass123",
        "role": "Victim",
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Account created" in response.data

    # 2. Register a second public user.
    response = client.post("/register", data={
        "name": "Test Volunteer",
        "phone": "9000000002",
        "email": "volunteer-flow@example.com",
        "password": "testpass123",
        "role": "Volunteer",
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Account created" in response.data

    # Public registration must not grant privileged roles.
    with app.app_context():
        victim = User.query.filter_by(
            email="victim-flow@example.com"
        ).one()
        volunteer = User.query.filter_by(
            email="volunteer-flow@example.com"
        ).one()

        assert victim.role == "Victim"
        assert volunteer.role == "Victim"

        victim_id = victim.user_id
        volunteer_id = volunteer.user_id

        admin = register_user(
            name="Test Provisioned Admin",
            email="admin-flow@example.com",
            password="adminpass123",
            role="Admin",
        )
        admin_id = admin.user_id

    # 3. Admin logs in and grants the Volunteer role.
    response = client.post("/auth/login", json={
        "email": "admin-flow@example.com",
        "password": "adminpass123",
    })
    assert response.status_code == 200

    response = client.patch(
        f"/auth/users/{volunteer_id}/role",
        json={"role": "Volunteer"},
    )
    assert response.status_code == 200
    assert response.json["user"]["role"] == "Volunteer"

    # 4. Log out and log in again as Admin before protected operations.
    client.post("/auth/logout")

    response = client.post("/auth/login", json={
        "email": "admin-flow@example.com",
        "password": "adminpass123",
    })
    assert response.status_code == 200

    # Registered users must be available in the Requester dropdown.
    response = client.get("/requests")
    assert response.status_code == 200
    assert b"Test Victim" in response.data

    # 5. Admin registers inventory.
    response = client.post("/inventory", data={
        "category": "Water",
        "quantity": "10",
        "storage_location": "Warehouse A",
        "expiry_date": "",
        "threshold": "2",
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Inventory item registered" in response.data

    # 6. Victim logs in before submitting their own relief request.
    client.post("/auth/logout")

    response = client.post("/auth/login", json={
        "email": "victim-flow@example.com",
        "password": "testpass123",
    })
    assert response.status_code == 200

    response = client.post("/requests", data={
        "user_id": str(victim_id),
        "category": "Water",
        "quantity": "4",
        "urgency": "Critical",
        "latitude": "11.0168",
        "longitude": "76.9558",
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Relief request submitted" in response.data

    with app.app_context():
        item = InventoryItem.query.filter_by(
            category="Water"
        ).one()
        relief_request = ReliefRequest.query.filter_by(
            user_id=victim_id
        ).one()

        item_id = item.item_id
        request_id = relief_request.request_id

        assert item.quantity == 10
        assert relief_request.status == "Pending"

    # 7. Admin logs in and allocates the request.
    client.post("/auth/logout")

    response = client.post("/auth/login", json={
        "email": "admin-flow@example.com",
        "password": "adminpass123",
    })
    assert response.status_code == 200

    response = client.post("/assignments", data={
        "request_id": str(request_id),
        "volunteer_id": str(volunteer_id),
        "item_id": str(item_id),
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Resource allocated and volunteer notified" in response.data

    with app.app_context():
        item = db.session.get(InventoryItem, item_id)
        relief_request = db.session.get(ReliefRequest, request_id)
        assignment = Assignment.query.filter_by(
            request_id=request_id
        ).one()
        notification = Notification.query.filter_by(
            user_id=volunteer_id
        ).one()

        task_id = assignment.task_id

        assert item.quantity == 6
        assert relief_request.status == "Assigned"
        assert assignment.quantity_assigned == 4
        assert assignment.status == "Assigned"
        assert "assigned request" in notification.message.lower()

# 8. The assigned Volunteer logs in and views their notification.
    client.post("/auth/logout")

    response = client.post("/auth/login", json={
        "email": "volunteer-flow@example.com",
        "password": "testpass123",
    })
    assert response.status_code == 200

    response = client.get("/notifications")
    assert response.status_code == 200
    assert b"assigned request" in response.data.lower()

    # 9. Volunteer completes the assignment.
    response = client.post(
        f"/assignments/{task_id}/status",
        data={"status": "Completed"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Assignment status updated" in response.data

    with app.app_context():
        assignment = db.session.get(Assignment, task_id)
        relief_request = db.session.get(ReliefRequest, request_id)

        assert assignment.status == "Completed"
        assert relief_request.status == "Fulfilled"
