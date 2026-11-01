"""Tests for the coordinator disaster map and its filter/refresh data API."""

import pytest
from werkzeug.security import generate_password_hash

from extensions import db
from models import Incident, InventoryItem, ReliefRequest, User


def make_user(app, name, role):
    with app.app_context():
        user = User(
            name=name,
            email=f"{name.lower().replace(' ', '-')}@map.example.com",
            role=role,
            password_hash=generate_password_hash("safe-pass-123"),
        )
        db.session.add(user)
        db.session.commit()
        return user.user_id


def login(client, user_id):
    with client.session_transaction() as session:
        session["user_id"] = user_id


def add_request(app, user_id, *, category="Water", status="Pending", location="North Sector", latitude=13.08, longitude=80.27):
    with app.app_context():
        record = ReliefRequest(
            user_id=user_id,
            category=category,
            quantity=3,
            urgency="High",
            location=location,
            latitude=latitude,
            longitude=longitude,
            status=status,
        )
        db.session.add(record)
        db.session.commit()
        return record.request_id


def add_incident(app, user_id, *, title="North Flood", status="Open", latitude=13.09, longitude=80.28):
    with app.app_context():
        record = Incident(
            title=title,
            description=f"{title} affected area",
            latitude=latitude,
            longitude=longitude,
            severity="Critical",
            status=status,
            reported_by=user_id,
        )
        db.session.add(record)
        db.session.commit()
        return record.incident_id


def test_map_page_requires_authentication(client):
    response = client.get("/map/")
    assert response.status_code == 401


@pytest.mark.parametrize("role", ["Victim", "Volunteer"])
def test_map_page_rejects_non_operational_roles(app, client, role):
    user_id = make_user(app, f"map-{role}", role)
    login(client, user_id)
    assert client.get("/map/").status_code == 403
    assert client.get("/map/data").status_code == 403


def test_coordinator_can_open_map_page(app, client):
    user_id = make_user(app, "map-coordinator", "Coordinator")
    login(client, user_id)
    response = client.get("/map/")
    assert response.status_code == 200
    assert b"Disaster Operations Map" in response.data
    assert b"30 seconds" in response.data
    assert b"30000" in response.data


def test_map_data_contains_geocoded_requests_incidents_and_unmapped_counts(app, client):
    coordinator_id = make_user(app, "map-data-coordinator", "Coordinator")
    victim_id = make_user(app, "map-data-victim", "Victim")
    volunteer_id = make_user(app, "map-data-volunteer", "Volunteer")
    add_request(app, victim_id)
    add_request(app, victim_id, category="Food", location="Unknown area", latitude=None, longitude=None)
    add_incident(app, coordinator_id)
    with app.app_context():
        db.session.add(InventoryItem(
            category="Water", quantity=10, storage_location="Central Depot", threshold=2
        ))
        db.session.commit()
    login(client, coordinator_id)

    response = client.get("/map/data")
    assert response.status_code == 200
    payload = response.get_json()
    assert len(payload["requests"]) == 1
    assert payload["requests"][0]["category"] == "Water"
    assert len(payload["incidents"]) == 1
    assert payload["unmapped"]["requests_without_coordinates"] == 1
    assert payload["unmapped"]["storage_locations_without_coordinates"] == 1
    assert payload["unmapped"]["volunteers_without_coordinates"] == 1
    assert response.headers["Cache-Control"].startswith("no-store")


def test_map_data_filters_by_category_status_and_region(app, client):
    coordinator_id = make_user(app, "map-filter-coordinator", "Coordinator")
    victim_id = make_user(app, "map-filter-victim", "Victim")
    add_request(app, victim_id, category="Water", status="Pending", location="North Sector")
    add_request(app, victim_id, category="Food", status="Assigned", location="South Sector")
    add_incident(app, coordinator_id, title="North Flood", status="Open")
    add_incident(app, coordinator_id, title="South Fire", status="Resolved", latitude=12.9, longitude=80.1)
    login(client, coordinator_id)

    filtered_requests = client.get("/map/data?category=Water&status=Pending&region=North")
    assert filtered_requests.status_code == 200
    payload = filtered_requests.get_json()
    assert [item["location"] for item in payload["requests"]] == ["North Sector"]
    # Incidents have no request category, so they are omitted when category is selected.
    assert payload["incidents"] == []

    filtered_incidents = client.get("/map/data?status=Open&region=North")
    assert filtered_incidents.status_code == 200
    payload = filtered_incidents.get_json()
    assert [item["title"] for item in payload["incidents"]] == ["North Flood"]


def test_map_data_limits_results_to_current_viewport(app, client):
    coordinator_id = make_user(app, "map-bounds-coordinator", "Coordinator")
    victim_id = make_user(app, "map-bounds-victim", "Victim")
    add_request(app, victim_id, location="Inside bounds", latitude=11.5, longitude=76.5)
    add_request(app, victim_id, category="Food", location="Outside bounds", latitude=20.0, longitude=80.0)
    add_incident(app, coordinator_id, title="Inside incident", latitude=11.7, longitude=76.7)
    add_incident(app, coordinator_id, title="Outside incident", latitude=20.1, longitude=80.1)
    login(client, coordinator_id)

    response = client.get(
        "/map/data?viewport=1&south=11&west=76&north=12&east=77"
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert [item["location"] for item in payload["requests"]] == ["Inside bounds"]
    assert [item["title"] for item in payload["incidents"]] == ["Inside incident"]


def test_map_data_rejects_invalid_filters_and_bounds(app, client):
    coordinator_id = make_user(app, "map-invalid-coordinator", "Coordinator")
    login(client, coordinator_id)
    assert client.get("/map/data?category=Unknown").status_code == 400
    assert client.get("/map/data?status=Unknown").status_code == 400
    assert client.get("/map/data?viewport=1&south=20&west=76&north=10&east=77").status_code == 400
    assert client.get("/map/data?region=" + ("x" * 101)).status_code == 400


def test_map_data_defaults_to_active_requests_and_incidents(app, client):
    coordinator_id = make_user(app, "map-active-coordinator", "Coordinator")
    victim_id = make_user(app, "map-active-victim", "Victim")
    add_request(app, victim_id, category="Water", status="Pending", location="Active request")
    add_request(app, victim_id, category="Food", status="Completed", location="Completed request")
    add_incident(app, coordinator_id, title="Active incident", status="Open")
    add_incident(app, coordinator_id, title="Closed incident", status="Closed", latitude=12.9, longitude=80.1)
    login(client, coordinator_id)

    response = client.get("/map/data")
    assert response.status_code == 200
    payload = response.get_json()
    assert [item["location"] for item in payload["requests"]] == ["Active request"]
    assert [item["title"] for item in payload["incidents"]] == ["Active incident"]

    # Explicit status selection can still retrieve historical/terminal records.
    completed = client.get("/map/data?status=Completed").get_json()
    assert [item["location"] for item in completed["requests"]] == ["Completed request"]
    closed = client.get("/map/data?status=Closed").get_json()
    assert [item["title"] for item in closed["incidents"]] == ["Closed incident"]
