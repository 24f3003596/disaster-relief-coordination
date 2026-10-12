import pytest
from extensions import db
from models import User, InventoryItem
from inventory import create_inventory_item, list_inventory_items, update_inventory_stock
from constants import CATEGORY_FOOD_WATER, CATEGORY_MEDICAL, ROLE_COORDINATOR
from werkzeug.security import generate_password_hash

def create_coordinator_user(app):
    with app.app_context():
        user = User(
            name="Inventory Coord",
            email="invcoord@example.com",
            role=ROLE_COORDINATOR,
            password_hash=generate_password_hash("safe-pass-123"),
        )
        db.session.add(user)
        db.session.commit()
        return user.user_id

def test_create_inventory_item_success(app):
    with app.app_context():
        item = create_inventory_item(
            category=CATEGORY_FOOD_WATER,
            quantity=250,
            storage_location="Warehouse A",
            expiry_date="2027-12-31",
            threshold=50,
        )
        assert item.item_id is not None
        assert item.category == CATEGORY_FOOD_WATER
        assert item.quantity == 250
        assert item.storage_location == "Warehouse A"
        assert item.threshold == 50
        assert item.is_low_stock() is False

def test_create_inventory_rejects_negative_quantity(app):
    with app.app_context():
        with pytest.raises(ValueError, match="quantity cannot be negative"):
            create_inventory_item(
                category=CATEGORY_FOOD_WATER,
                quantity=-5,
                storage_location="Warehouse A",
            )

def test_create_inventory_rejects_invalid_category(app):
    with app.app_context():
        with pytest.raises(ValueError, match="invalid category"):
            create_inventory_item(
                category="Nonexistent Category",
                quantity=100,
                storage_location="Warehouse A",
            )

def test_create_inventory_rejects_negative_threshold(app):
    with app.app_context():
        with pytest.raises(ValueError, match="threshold cannot be negative"):
            create_inventory_item(
                category=CATEGORY_FOOD_WATER,
                quantity=100,
                storage_location="Warehouse A",
                threshold=-10,
            )

def test_boundary_threshold_low_stock(app):
    with app.app_context():
        # Boundary 1: quantity equals threshold -> is_low_stock should be True
        item_at_threshold = create_inventory_item(
            category=CATEGORY_FOOD_WATER,
            quantity=50,
            storage_location="Warehouse A",
            threshold=50,
        )
        assert item_at_threshold.is_low_stock() is True

        # Boundary 2: quantity is 1 above threshold -> is_low_stock should be False
        item_above_threshold = create_inventory_item(
            category=CATEGORY_MEDICAL,
            quantity=51,
            storage_location="Warehouse B",
            threshold=50,
        )
        assert item_above_threshold.is_low_stock() is False

        # Boundary 3: quantity is 0 -> is_low_stock should be True
        zero_item = create_inventory_item(
            category="Blankets & Shelter",
            quantity=0,
            storage_location="Warehouse C",
            threshold=10,
        )
        assert zero_item.is_low_stock() is True

def test_update_inventory_stock(app):
    with app.app_context():
        item = create_inventory_item(
            category=CATEGORY_FOOD_WATER,
            quantity=100,
            storage_location="Warehouse A",
        )
        # Deduct stock
        updated = update_inventory_stock(item.item_id, -30)
        assert updated.quantity == 70

        # Restock
        restocked = update_inventory_stock(item.item_id, 50)
        assert restocked.quantity == 120

        # Attempt to deduct more than available
        with pytest.raises(ValueError, match="Insufficient stock"):
            update_inventory_stock(item.item_id, -200)

def test_inventory_routes_and_access(app, client):
    coord_id = create_coordinator_user(app)
    with client.session_transaction() as sess:
        sess["user_id"] = coord_id

    # Create via POST route
    response = client.post("/inventory/", json={
        "category": "Clothing",
        "quantity": 300,
        "storage_location": "Central Depot",
        "threshold": 30,
    })
    assert response.status_code == 201
    item_id = response.json["item"]["item_id"]

    # List items
    get_res = client.get("/inventory/", headers={"Accept": "application/json"})
    assert get_res.status_code == 200
    assert get_res.json["total_items"] >= 1

    # Filter by category
    filter_res = client.get("/inventory/?category=Clothing", headers={"Accept": "application/json"})
    assert filter_res.status_code == 200
    assert len(filter_res.json["inventory"]) == 1

    # Detail route
    detail_res = client.get(f"/inventory/{item_id}")
    assert detail_res.status_code == 200
    assert detail_res.json["item"]["category"] == "Clothing"
