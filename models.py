from datetime import datetime, timezone
from extensions import db

def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class User(db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(30), nullable=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False, default="Victim")
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)

    relief_requests = db.relationship("ReliefRequest", back_populates="user", lazy=True)
    notifications = db.relationship("Notification", back_populates="user", lazy=True)
    assignments = db.relationship("Assignment", back_populates="volunteer", lazy=True)
    audit_logs = db.relationship("AuditLog", back_populates="user", lazy=True)

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "name": self.name,
            "phone": self.phone,
            "email": self.email,
            "role": self.role,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
        }

class Incident(db.Model):
    __tablename__ = "incidents"

    incident_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    severity = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Open")
    reported_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)

    reporter = db.relationship("User", backref=db.backref("reported_incidents", lazy=True))

    def to_dict(self):
        return {
            "incident_id": self.incident_id,
            "title": self.title,
            "description": self.description,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "severity": self.severity,
            "status": self.status,
            "reported_by": self.reported_by,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
        }

class ReliefRequest(db.Model):
    __tablename__ = "relief_requests"

    request_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    urgency = db.Column(db.String(20), nullable=False, default="Medium")
    location = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    incident_id = db.Column(db.Integer, db.ForeignKey("incidents.incident_id"), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="Pending")
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)

    user = db.relationship("User", back_populates="relief_requests")
    incident = db.relationship("Incident", backref=db.backref("relief_requests", lazy=True))
    assignment = db.relationship("Assignment", back_populates="relief_request", uselist=False, lazy=True)

    def to_dict(self):
        return {
            "request_id": self.request_id,
            "user_id": self.user_id,
            "category": self.category,
            "quantity": self.quantity,
            "urgency": self.urgency,
            "location": self.location,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "incident_id": self.incident_id,
            "status": self.status,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
            "has_assignment": self.assignment is not None,
        }

class Notification(db.Model):
    __tablename__ = "notifications"

    notification_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(30), nullable=False, default="General")
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)

    user = db.relationship("User", back_populates="notifications")

    def to_dict(self):
        return {
            "notification_id": self.notification_id,
            "user_id": self.user_id,
            "message": self.message,
            "type": self.type,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
        }

class InventoryItem(db.Model):
    __tablename__ = "inventory_items"

    item_id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(80), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    storage_location = db.Column(db.String(255), nullable=False)
    expiry_date = db.Column(db.Date, nullable=True)
    threshold = db.Column(db.Integer, nullable=False, default=0)

    assignments = db.relationship("Assignment", back_populates="item", lazy=True)

    def is_low_stock(self):
        return self.quantity <= self.threshold

    def to_dict(self):
        return {
            "item_id": self.item_id,
            "category": self.category,
            "quantity": self.quantity,
            "storage_location": self.storage_location,
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "threshold": self.threshold,
            "is_low_stock": self.is_low_stock(),
        }

class Assignment(db.Model):
    __tablename__ = "assignments"

    task_id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey("relief_requests.request_id"), nullable=False, unique=True)
    volunteer_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey("inventory_items.item_id"), nullable=False)
    quantity_assigned = db.Column(db.Integer, nullable=False, default=1)
    status = db.Column(db.String(20), nullable=False, default="Assigned")
    assigned_at = db.Column(db.DateTime, nullable=False, default=utc_now)
    completed_at = db.Column(db.DateTime, nullable=True)

    relief_request = db.relationship("ReliefRequest", back_populates="assignment")
    volunteer = db.relationship("User", back_populates="assignments")
    item = db.relationship("InventoryItem", back_populates="assignments")

    @property
    def request(self):
        return self.relief_request

    @request.setter
    def request(self, value):
        self.relief_request = value

    def to_dict(self):
        return {
            "task_id": self.task_id,
            "request_id": self.request_id,
            "volunteer_id": self.volunteer_id,
            "item_id": self.item_id,
            "quantity_assigned": self.quantity_assigned,
            "status": self.status,
            "assigned_at": self.assigned_at.isoformat() + "Z" if self.assigned_at else None,
            "completed_at": self.completed_at.isoformat() + "Z" if self.completed_at else None,
        }

class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    log_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    action = db.Column(db.String(120), nullable=False)
    entity_type = db.Column(db.String(80), nullable=True)
    entity_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)

    user = db.relationship("User", back_populates="audit_logs")

    def to_dict(self):
        return {
            "log_id": self.log_id,
            "user_id": self.user_id,
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
        }
