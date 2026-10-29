"""Regression tests for role-based access control on protected API routes."""

import pytest

from auth import register_user
from extensions import db
from models import ReliefRequest, User
from requests_module import create_relief_request


def make_user(app, name, role):
    with app.app_context():
        user = register_user(
            name=name,
            email=f"{name.lower().replace(' ', '-')}@rbac.example.com",
            password="safe-pass-123",
            role=role,
        )
        return user.user_id


def login(client, user_id):
    with client.session_transaction() as session:
        session["user_id"] = user_id


def test_inventory_write_requires_authentication(client):
    response = client.post("/inventory/", json={
        "category": "Water", "quantity": 5, "storage_location": "Depot A"
    })
    assert response.status_code == 401


@pytest.mark.parametrize("role", ["Victim", "Volunteer"])
def test_non_coordinator_cannot_create_inventory(app, client, role):
    user_id = make_user(app, f"inventory-{role}", role)
    login(client, user_id)

    response = client.post("/inventory/", json={
        "category": "Water", "quantity": 5, "storage_location": "Depot A"
    })
    assert response.status_code == 403


def test_victim_cannot_allocate_resources(app, client):
    user_id = make_user(app, "allocation-victim", "Victim")
    login(client, user_id)

    response = client.post("/assignments/allocate", json={
        "request_id": 1, "volunteer_id": 2, "item_id": 1
    })
    assert response.status_code == 403


def test_victim_cannot_update_request_status(app, client):
    victim_id = make_user(app, "status-victim", "Victim")
    with app.app_context():
        req = create_relief_request(victim_id, "Water", 2, "High")
        request_id = req.request_id
    login(client, victim_id)

    response = client.patch(
        f"/requests/{request_id}/status", json={"status": "Allocated"}
    )
    assert response.status_code == 403
    with app.app_context():
        assert db.session.get(ReliefRequest, request_id).status == "Pending"


def test_victim_cannot_read_another_victims_request(app, client):
    victim_a = make_user(app, "owner-victim", "Victim")
    victim_b = make_user(app, "other-victim", "Victim")
    with app.app_context():
        req = create_relief_request(victim_b, "Water", 2, "High")
        request_id = req.request_id
    login(client, victim_a)

    response = client.get(f"/requests/{request_id}")
    assert response.status_code == 403


def test_victim_cannot_spoof_request_owner(app, client):
    victim_a = make_user(app, "session-victim", "Victim")
    victim_b = make_user(app, "spoof-target", "Victim")
    login(client, victim_a)

    response = client.post("/requests/", json={
        "user_id": victim_b,
        "category": "Water",
        "quantity": 2,
        "urgency": "High",
    })
    assert response.status_code == 201
    assert response.json["request"]["user_id"] == victim_a


def test_victim_cannot_see_other_users_requests_by_filter(app, client):
    victim_a = make_user(app, "filter-victim", "Victim")
    victim_b = make_user(app, "filtered-victim", "Victim")
    with app.app_context():
        create_relief_request(victim_b, "Water", 2, "High")
    login(client, victim_a)

    response = client.get(
        f"/requests/?user_id={victim_b}",
        headers={"Accept": "application/json"},
    )
    assert response.status_code == 200
    assert response.json["total_requests"] == 0


def test_volunteer_cannot_update_another_volunteers_assignment(app, client, seed):
    other_volunteer_id = make_user(app, "other-assigned-volunteer", "Volunteer")
    # Allocate through the service function to create a real assignment.
    from assignments import allocate_request
    with app.app_context():
        assignment = allocate_request(seed["request"], seed["volunteer"], seed["item"])
        task_id = assignment.task_id
    login(client, other_volunteer_id)

    response = client.patch(
        f"/assignments/{task_id}/status", json={"status": "Completed"}
    )
    assert response.status_code == 403
