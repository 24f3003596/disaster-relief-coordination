from datetime import datetime, date
from flask import Blueprint, jsonify, request, session, has_request_context

from extensions import db
from models import InventoryItem
from auth import login_required, roles_required
from audit import log_action
from constants import VALID_CATEGORIES, ACTION_CREATE_INVENTORY, ACTION_UPDATE_INVENTORY

inventory_bp = Blueprint("inventory", __name__)

def parse_date(date_val):
    if not date_val:
        return None
    if isinstance(date_val, date):
        return date_val
    if isinstance(date_val, str):
        try:
            return datetime.strptime(date_val.strip(), "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("expiry_date must be in YYYY-MM-DD format")
    return None

def create_inventory_item(category, quantity, storage_location, expiry_date=None, threshold=0):
    """
    Register a new inventory item and log the action.
    """
    category = (category or "").strip()
    storage_location = (storage_location or "").strip()

    if not category:
        raise ValueError("category is required")
    if category not in VALID_CATEGORIES:
        raise ValueError(f"invalid category. Must be one of: {', '.join(VALID_CATEGORIES)}")
    if not storage_location:
        raise ValueError("storage_location is required")

    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        raise ValueError("quantity must be an integer")
    if quantity < 0:
        raise ValueError("quantity cannot be negative")

    try:
        threshold = int(threshold)
    except (TypeError, ValueError):
        raise ValueError("threshold must be an integer")
    if threshold < 0:
        raise ValueError("threshold cannot be negative")

    parsed_expiry = parse_date(expiry_date)

    item = InventoryItem(
        category=category,
        quantity=quantity,
        storage_location=storage_location,
        expiry_date=parsed_expiry,
        threshold=threshold,
    )
    db.session.add(item)
    db.session.commit()

    # Audit logging
    actor_id = None
    if has_request_context() and "user_id" in session:
        actor_id = session.get("user_id")
    log_action(
        user_id=actor_id,
        action=ACTION_CREATE_INVENTORY,
        entity_type="InventoryItem",
        entity_id=item.item_id,
    )

    return item

def list_inventory_items(category=None, available_only=False):
    """
    Retrieve inventory items with optional category and availability filtering.
    """
    query = InventoryItem.query
    if category:
        category = category.strip()
        query = query.filter_by(category=category)
    if available_only:
        query = query.filter(InventoryItem.quantity > 0)

    return query.order_by(InventoryItem.category.asc(), InventoryItem.quantity.desc()).all()

def update_inventory_stock(item_id, quantity_change, actor_id=None):
    """
    Adjust inventory stock by quantity_change (positive for restock, negative for deduction).
    Prevents negative stock.
    """
    item = db.session.get(InventoryItem, item_id)
    if not item:
        raise ValueError(f"Inventory item {item_id} not found")

    new_quantity = item.quantity + int(quantity_change)
    if new_quantity < 0:
        raise ValueError(f"Insufficient stock for {item.category}. Available: {item.quantity}, Requested: {abs(quantity_change)}")

    item.quantity = new_quantity
    db.session.commit()

    log_action(
        user_id=actor_id,
        action=ACTION_UPDATE_INVENTORY,
        entity_type="InventoryItem",
        entity_id=item.item_id,
    )
    return item

@inventory_bp.post("/")
@login_required
@roles_required("Coordinator", "Admin")
def create_item_route():
    data = request.get_json(silent=True) or {}
    try:
        item = create_inventory_item(
            category=data.get("category"),
            quantity=data.get("quantity"),
            storage_location=data.get("storage_location"),
            expiry_date=data.get("expiry_date"),
            threshold=data.get("threshold", 0),
        )
        return jsonify({"message": "Inventory item registered", "item": item.to_dict()}), 201
    except ValueError as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 400

@inventory_bp.get("/")
def list_items_route():
    category = request.args.get("category")
    available_only = request.args.get("available_only", "false").lower() in ("true", "1", "yes")
    items = list_inventory_items(category=category, available_only=available_only)
    items_dict = [item.to_dict() for item in items]
    if "text/html" in request.headers.get("Accept", "") and request.args.get("format") != "json":
        from flask import render_template
        return render_template("inventory.html", inventory=items_dict)
    return jsonify({
        "inventory": items_dict,
        "total_items": len(items),
    }), 200

@inventory_bp.get("/<int:item_id>")
def get_item_route(item_id):
    item = db.session.get(InventoryItem, item_id)
    if not item:
        return jsonify({"error": "Inventory item not found"}), 404
    return jsonify({"item": item.to_dict()}), 200

@inventory_bp.get("/low-stock")
@login_required
def low_stock_route():
    items = InventoryItem.query.filter(InventoryItem.quantity <= InventoryItem.threshold).all()
    return jsonify({"low_stock_items": [item.to_dict() for item in items]}), 200
