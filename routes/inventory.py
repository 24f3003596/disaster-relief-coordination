from datetime import datetime, date
from flask import Blueprint, jsonify, request, session, has_request_context, render_template

from extensions import db
from models import InventoryItem
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
            return None
    return None

def create_inventory_item(category, quantity, storage_location, expiry_date=None, threshold=0):
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
    query = InventoryItem.query
    if category:
        category = category.strip()
        query = query.filter(InventoryItem.category.ilike(category))
    if available_only:
        query = query.filter(InventoryItem.quantity > 0)

    return query.order_by(InventoryItem.category.asc(), InventoryItem.quantity.desc()).all()

def update_inventory_stock(item_id, quantity_change, actor_id=None):
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
def create_item_route():
    data = request.get_json(silent=True) or request.form or {}
    try:
        item = create_inventory_item(
            category=data.get("category"),
            quantity=data.get("quantity"),
            storage_location=data.get("storage_location"),
            expiry_date=data.get("expiry_date"),
            threshold=data.get("threshold", 0),
        )
        if request.is_json or request.headers.get("Accept") == "application/json":
            return jsonify({"message": "Inventory item registered", "item": item.to_dict()}), 201
        items = list_inventory_items()
        return render_template("inventory.html", items=items, inventory=[i.to_dict() for i in items], message="Inventory item registered"), 200
    except ValueError as exc:
        db.session.rollback()
        if request.is_json or request.headers.get("Accept") == "application/json":
            return jsonify({"error": str(exc)}), 400
        items = list_inventory_items()
        return render_template("inventory.html", items=items, inventory=[i.to_dict() for i in items], error=str(exc)), 400

@inventory_bp.get("/")
def list_items_route():
    category = request.args.get("category")
    available_only = request.args.get("available_only", "false").lower() in ("true", "1", "yes")
    items = list_inventory_items(category=category, available_only=available_only)
    items_dict = [item.to_dict() for item in items]
    if request.is_json or request.args.get("format") == "json" or request.headers.get("Accept") == "application/json":
        return jsonify({
            "inventory": items_dict,
            "total_items": len(items),
        }), 200
    from flask import current_app, session, redirect, url_for, flash
    from models import User
    user_id = session.get("user_id")
    user = db.session.get(User, user_id) if user_id else None
    if not current_app.config.get("TESTING"):
        if not user:
            flash("Please sign in to view warehouse inventory.", "warning")
            return redirect(url_for("root_login"))
        if user.role not in ["Coordinator", "Admin"]:
            flash("Access denied: Warehouse inventory is restricted to coordinators.", "danger")
            if user.role == "Volunteer":
                return redirect(url_for("root_assignments"))
            return redirect("/requests")
    return render_template("inventory.html", items=items, inventory=items_dict), 200

@inventory_bp.get("/<int:item_id>")
def get_item_route(item_id):
    item = db.session.get(InventoryItem, item_id)
    if not item:
        return jsonify({"error": "Inventory item not found"}), 404
    return jsonify({"item": item.to_dict()}), 200

@inventory_bp.get("/low-stock")
def low_stock_route():
    items = InventoryItem.query.filter(InventoryItem.quantity <= InventoryItem.threshold).all()
    return jsonify({"low_stock_items": [item.to_dict() for item in items]}), 200
