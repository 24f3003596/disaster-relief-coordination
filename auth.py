from functools import wraps

from flask import Blueprint, jsonify, request, session
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db
from models import User

auth_bp = Blueprint("auth", __name__)
VALID_ROLES = {"Victim", "Volunteer", "Coordinator", "Admin"}

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Authentication required"}), 401
        return view(*args, **kwargs)
    return wrapped

def roles_required(*allowed_roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                return jsonify({"error": "Authentication required"}), 401
            user = db.session.get(User, session["user_id"])
            if user is None or user.role not in allowed_roles:
                return jsonify({"error": "Insufficient permissions"}), 403
            return view(*args, **kwargs)
        return wrapped
    return decorator

def register_user(name, email, password, phone=None, role="Victim"):
    """Create and return a user; raise ValueError for invalid input."""
    name = (name or "").strip()
    email = (email or "").strip().lower()
    if not name or not email or not password:
        raise ValueError("name, email and password are required")
    if len(password) < 8:
        raise ValueError("password must contain at least 8 characters")
    if role not in VALID_ROLES:
        raise ValueError("invalid role")
    if User.query.filter_by(email=email).first():
        raise ValueError("email already registered")
    user = User(
        name=name,
        email=email,
        phone=(phone or "").strip() or None,
        role=role,
        password_hash=generate_password_hash(password),
    )
    db.session.add(user)
    db.session.commit()
    return user

def authenticate_user(email, password):
    email = (email or "").strip().lower()
    user = User.query.filter_by(email=email).first()
    if user and password and check_password_hash(user.password_hash, password):
        return user
    return None

@auth_bp.post("/register")
def register_route():
    data = request.get_json(silent=True) or {}
    try:
        # Public registration deliberately creates Victim accounts only.
        user = register_user(
            data.get("name"), data.get("email"), data.get("password"),
            data.get("phone"), role="Victim",
        )
        return jsonify({"message": "User registered", "user": user.to_dict()}), 201
    except ValueError as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 400

@auth_bp.post("/login")
def login_route():
    data = request.get_json(silent=True) or {}
    user = authenticate_user(data.get("email"), data.get("password"))
    if not user:
        return jsonify({"error": "Invalid email or password"}), 401
    session.clear()
    session["user_id"] = user.user_id
    return jsonify({"message": "Login successful", "user": user.to_dict()}), 200

@auth_bp.post("/logout")
def logout_route():
    session.clear()
    return jsonify({"message": "Logged out"}), 200

@auth_bp.get("/me")
@login_required
def current_user_route():
    user = db.session.get(User, session["user_id"])
    if not user:
        session.clear()
        return jsonify({"error": "User no longer exists"}), 401
    return jsonify({"user": user.to_dict()}), 200

@auth_bp.patch("/users/<int:user_id>/role")
@roles_required("Admin")
def update_role_route(user_id):
    data = request.get_json(silent=True) or {}
    new_role = data.get("role")
    if new_role not in VALID_ROLES:
        return jsonify({"error": "invalid role"}), 400
    user = db.session.get(User, user_id)
    if user is None:
        return jsonify({"error": "User not found"}), 404
    user.role = new_role
    db.session.commit()
    return jsonify({"message": "Role updated", "user": user.to_dict()}), 200
