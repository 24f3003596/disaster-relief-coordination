from datetime import date
from extensions import db
from models import InventoryItem

def create_inventory_item(category, quantity, storage_location, expiry_date=None, threshold=0):
    if not category or not category.strip(): raise ValueError("Category is required")
    if int(quantity)<0 or int(threshold)<0: raise ValueError("Quantity and threshold cannot be negative")
    expiry = date.fromisoformat(expiry_date) if isinstance(expiry_date, str) and expiry_date else expiry_date
    item=InventoryItem(category=category.strip(),quantity=int(quantity),storage_location=storage_location.strip(),expiry_date=expiry,threshold=int(threshold))
    db.session.add(item); db.session.commit(); return item

def list_inventory_items(category=None, available_only=False):
    q=InventoryItem.query
    if category: q=q.filter(InventoryItem.category.ilike(category))
    if available_only: q=q.filter(InventoryItem.quantity>0)
    return q.order_by(InventoryItem.category.asc()).all()
