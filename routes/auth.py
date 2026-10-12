from functools import wraps

from flask import Blueprint, jsonify, request, session
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db
from models import User
from constants import VALID_ROLES, ROLE_ADMIN, ROLE_VICTIM

auth_bp = Blueprint("auth", __name__)

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

def register_user(name, *args, **kwargs):
    """
    Create and return a user.
    Supports both signatures:
    1) register_user(name, phone, email, password, role="Victim") [SRS & agreed spec]
    2) register_user(name, email, password, phone=None, role="Victim") [Vishal's initial PR]
    """
    name = (name or "").strip()
    if not name:
        raise ValueError("name, email and password are required")

    phone = kwargs.get("phone")
    email = kwargs.get("email")
    password = kwargs.get("password")
    role = kwargs.get("role", ROLE_VICTIM)

    # Parse positional args if provided
    if len(args) == 4:
        # (phone, email, password, role)
        phone, email, password, role = args
    elif len(args) == 3:
        # Either (phone, email, password) or (email, password, phone)
        a1, a2, a3 = args
        if isinstance(a1, str) and "@" in a1:
            # (email, password, phone)
            email, password, phone = a1, a2, a3
        else:
            # (phone, email, password)
            phone, email, password = a1, a2, a3
    elif len(args) == 2:
        # (email, password)
        a1, a2 = args
        email, password = a1, a2
    elif len(args) == 1:
        if email is None and "@" in str(args[0]):
            email = args[0]
        elif phone is None:
            phone = args[0]

    email = (email or "").strip().lower()
    password = password or ""
    phone = (phone or "").strip() or None

    if not email or not password:
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
        phone=phone,
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

def update_user_role(user_id, new_role, actor_id=None):
    """Update role of a user. If actor_id is provided, checks permissions."""
    if new_role not in VALID_ROLES:
        raise ValueError("invalid role")
    if actor_id is not None:
        actor = db.session.get(User, actor_id)
        if not actor or actor.role != ROLE_ADMIN:
            raise PermissionError("Insufficient permissions: actor must be Admin")

    user = db.session.get(User, user_id)
    if not user:
        raise ValueError("User not found")

    user.role = new_role
    db.session.commit()
    return user

@auth_bp.post("/register")
def register_route():
    data = request.get_json(silent=True) or {}
    try:
        # Public registration creates Victim accounts by default
        role = data.get("role", ROLE_VICTIM)
        user = register_user(
            name=data.get("name"),
            phone=data.get("phone"),
            email=data.get("email"),
            password=data.get("password"),
            role=role,
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
    try:
        user = update_user_role(user_id, new_role, actor_id=session.get("user_id"))
        return jsonify({"message": "Role updated", "user": user.to_dict()}), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except PermissionError as exc:
        return jsonify({"error": str(exc)}), 403
