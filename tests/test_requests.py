import pytest
from extensions import db
from models import User, ReliefRequest
from requests_module import create_relief_request, list_relief_requests, update_request_status
from constants import (
    CATEGORY_FOOD_WATER,
    URGENCY_HIGH,
    URGENCY_CRITICAL,
    STATUS_REQUEST_PENDING,
    STATUS_REQUEST_ALLOCATED,
    STATUS_REQUEST_COMPLETED,
    ROLE_VICTIM,
    ROLE_COORDINATOR,
)
from werkzeug.security import generate_password_hash

def create_victim_user(app):
    with app.app_context():
        user = User(
            name="Victim John",
            email="victimjohn@example.com",
            role=ROLE_VICTIM,
            password_hash=generate_password_hash("safe-pass-123"),
        )
        db.session.add(user)
        db.session.commit()
        return user.user_id

def create_coordinator_user(app):
    with app.app_context():
        user = User(
            name="Request Coord",
            email="reqcoord@example.com",
            role=ROLE_COORDINATOR,
            password_hash=generate_password_hash("safe-pass-123"),
        )
        db.session.add(user)
        db.session.commit()
        return user.user_id

def test_create_relief_request_success(app):
    victim_id = create_victim_user(app)
    with app.app_context():
        req = create_relief_request(
            user_id=victim_id,
            category=CATEGORY_FOOD_WATER,
            quantity=15,
            urgency=URGENCY_HIGH,
            latitude=13.0827,
            longitude=80.2707,
            location="Relief Camp Sector 2",
        )
        assert req.request_id is not None
        assert req.user_id == victim_id
        assert req.category == CATEGORY_FOOD_WATER
        assert req.quantity == 15
        assert req.urgency == URGENCY_HIGH
        assert req.status == STATUS_REQUEST_PENDING
        assert req.latitude == 13.0827
        assert req.longitude == 80.2707

def test_create_request_rejects_zero_or_negative_quantity(app):
    victim_id = create_victim_user(app)
    with app.app_context():
        with pytest.raises(ValueError, match="quantity must be greater than zero"):
            create_relief_request(
                user_id=victim_id,
                category=CATEGORY_FOOD_WATER,
                quantity=0,
                urgency=URGENCY_HIGH,
            )
        with pytest.raises(ValueError, match="quantity must be greater than zero"):
            create_relief_request(
                user_id=victim_id,
                category=CATEGORY_FOOD_WATER,
                quantity=-10,
                urgency=URGENCY_HIGH,
            )

def test_create_request_rejects_invalid_coordinates(app):
    victim_id = create_victim_user(app)
    with app.app_context():
        with pytest.raises(ValueError, match="latitude must be between -90 and 90"):
            create_relief_request(
                user_id=victim_id,
                category=CATEGORY_FOOD_WATER,
                quantity=5,
                urgency=URGENCY_HIGH,
                latitude=95.0,
                longitude=80.0,
            )
        with pytest.raises(ValueError, match="longitude must be between -180 and 180"):
            create_relief_request(
                user_id=victim_id,
                category=CATEGORY_FOOD_WATER,
                quantity=5,
                urgency=URGENCY_HIGH,
                latitude=13.0,
                longitude=195.0,
            )

def test_update_request_status(app):
    victim_id = create_victim_user(app)
    with app.app_context():
        req = create_relief_request(
            user_id=victim_id,
            category=CATEGORY_FOOD_WATER,
            quantity=10,
            urgency=URGENCY_CRITICAL,
        )
        assert req.status == STATUS_REQUEST_PENDING

        updated = update_request_status(req.request_id, STATUS_REQUEST_ALLOCATED)
        assert updated.status == STATUS_REQUEST_ALLOCATED

        completed = update_request_status(req.request_id, STATUS_REQUEST_COMPLETED)
        assert completed.status == STATUS_REQUEST_COMPLETED

        with pytest.raises(ValueError, match="invalid status"):
            update_request_status(req.request_id, "NonexistentStatus")

def test_relief_request_routes(app, client):
    victim_id = create_victim_user(app)
    coord_id = create_coordinator_user(app)

    # Login as victim
    with client.session_transaction() as sess:
        sess["user_id"] = victim_id

    # Post request
    post_res = client.post("/requests/", json={
        "category": "Medical Supplies",
        "quantity": 8,
        "urgency": "High",
        "latitude": 13.05,
        "longitude": 80.20,
        "location": "Shelter Delta",
    })
    assert post_res.status_code == 201
    req_id = post_res.json["request"]["request_id"]

    # List requests via JSON
    list_res = client.get("/requests/", headers={"Accept": "application/json"})
    assert list_res.status_code == 200
    assert list_res.json["total_requests"] >= 1

    # Login as coordinator to update status
    with client.session_transaction() as sess:
        sess["user_id"] = coord_id

    patch_res = client.patch(f"/requests/{req_id}/status", json={"status": "Allocated"})
    assert patch_res.status_code == 200
    assert patch_res.json["request"]["status"] == "Allocated"


def test_request_status_transition_rejects_skipping_workflow(app):
    victim_id = create_victim_user(app)
    with app.app_context():
        req = create_relief_request(
            user_id=victim_id,
            category=CATEGORY_FOOD_WATER,
            quantity=2,
            urgency=URGENCY_HIGH,
        )
        with pytest.raises(ValueError, match="Invalid request status transition"):
            update_request_status(req.request_id, STATUS_REQUEST_COMPLETED)
        db.session.refresh(req)
        assert req.status == STATUS_REQUEST_PENDING


def test_request_creation_requires_login(client):
    response = client.post("/requests/", json={
        "category": CATEGORY_FOOD_WATER,
        "quantity": 2,
        "urgency": URGENCY_HIGH,
    })
    assert response.status_code == 401


def test_request_creation_ignores_forged_user_id(app, client):
    victim_id = create_victim_user(app)
    with app.app_context():
        other = User(
            name="Other Victim",
            email="other-victim@example.com",
            role=ROLE_VICTIM,
            password_hash=generate_password_hash("safe-pass-123"),
        )
        db.session.add(other)
        db.session.commit()
        other_id = other.user_id

    with client.session_transaction() as sess:
        sess["user_id"] = victim_id
    response = client.post("/requests/", json={
        "user_id": other_id,
        "category": CATEGORY_FOOD_WATER,
        "quantity": 2,
        "urgency": URGENCY_HIGH,
    })
    assert response.status_code == 201
    assert response.json["request"]["user_id"] == victim_id
    assert response.json["request"]["user_id"] != other_id


def test_victim_only_sees_own_requests_and_cannot_change_status(app, client):
    first_victim_id = create_victim_user(app)
    with app.app_context():
        second_victim = User(
            name="Second Victim",
            email="second-victim@example.com",
            role=ROLE_VICTIM,
            password_hash=generate_password_hash("safe-pass-123"),
        )
        db.session.add(second_victim)
        db.session.commit()
        second_victim_id = second_victim.user_id
        other_request = create_relief_request(
            user_id=second_victim_id,
            category=CATEGORY_FOOD_WATER,
            quantity=3,
            urgency=URGENCY_HIGH,
        )
        other_request_id = other_request.request_id

    with client.session_transaction() as sess:
        sess["user_id"] = first_victim_id
    response = client.get("/requests/", headers={"Accept": "application/json"})
    assert response.status_code == 200
    assert all(item["user_id"] == first_victim_id for item in response.json["requests"])
    hidden_request = client.get(f"/requests/{other_request_id}")
    assert hidden_request.status_code == 403
    status_response = client.patch(
        f"/requests/{other_request_id}/status", json={"status": STATUS_REQUEST_ALLOCATED}
    )
    assert status_response.status_code == 403


def test_incomplete_coordinate_pair_is_rejected(app):
    victim_id = create_victim_user(app)
    with app.app_context():
        with pytest.raises(ValueError, match="latitude and longitude must be provided together"):
            create_relief_request(
                user_id=victim_id,
                category=CATEGORY_FOOD_WATER,
                quantity=2,
                urgency=URGENCY_HIGH,
                latitude=13.0,
            )


def test_invalid_http_request_payload_returns_client_error(app, client):
    victim_id = create_victim_user(app)
    with client.session_transaction() as sess:
        sess["user_id"] = victim_id

    missing_fields = client.post("/requests/", json={"category": CATEGORY_FOOD_WATER})
    assert missing_fields.status_code == 400
    assert "error" in missing_fields.json

    non_object_payload = client.post("/requests/", json=["not", "an", "object"])
    assert non_object_payload.status_code == 400
    assert "error" in non_object_payload.json
