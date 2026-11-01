from functools import wraps
from datetime import datetime, timedelta
import secrets

from flask import Blueprint, jsonify, request, session, current_app
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db
from models import User, PhoneOTP
from constants import VALID_ROLES, ROLE_ADMIN, ROLE_VICTIM

auth_bp = Blueprint("auth", __name__)

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Authentication required"}), 401
        user = db.session.get(User, session["user_id"])
        if user is None or not user.is_active or not user.phone_verified:
            session.clear()
            return jsonify({"error": "Account is inactive or unverified"}), 401
        if user.role in (ROLE_ADMIN, "Coordinator") and user.approval_status != "approved":
            session.clear()
            return jsonify({"error": "Administrator approval is required"}), 403
        return view(*args, **kwargs)
    return wrapped

def roles_required(*allowed_roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                return jsonify({"error": "Authentication required"}), 401
            user = db.session.get(User, session["user_id"])
            if user is None or not user.is_active or not user.phone_verified or user.approval_status != "approved" or user.role not in allowed_roles:
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
        phone_verified=True,  # trusted internal provisioning; public registration uses the OTP flow below
        is_active=True,
        approval_status="approved",  # trusted bootstrap/provisioning only
    )
    db.session.add(user)
    db.session.commit()
    return user

def authenticate_user(email, password):
    email = (email or "").strip().lower()
    user = User.query.filter_by(email=email).first()
    if user and password and check_password_hash(user.password_hash, password):
        if not user.is_active or not user.phone_verified:
            return None
        if user.role in (ROLE_ADMIN, "Coordinator") and user.approval_status != "approved":
            return None
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
    if new_role in (ROLE_ADMIN, "Coordinator"):
        user.approval_status = "pending"
        user.approval_reviewed_by = None
        user.approval_reviewed_at = None
        user.approval_rejection_reason = None
    else:
        user.approval_status = "approved"
        user.approval_reviewed_by = None
        user.approval_reviewed_at = None
        user.approval_rejection_reason = None
    db.session.commit()
    return user

def _issue_phone_otp(user):
    """Issue a six-digit OTP; only its hash is persisted."""
    code = f"{secrets.randbelow(1_000_000):06d}"
    challenge = PhoneOTP(
        user_id=user.user_id,
        phone=user.phone,
        otp_hash=generate_password_hash(code),
        expires_at=datetime.utcnow() + timedelta(minutes=current_app.config.get("OTP_TTL_MINUTES", 5)),
    )
    db.session.add(challenge)
    db.session.commit()
    # Development delivery: print to the server console, never log in production.
    if current_app.config.get("OTP_DEMO_MODE", False):
        current_app.logger.warning("DEMO OTP for %s (%s): %s", user.email, user.phone, code)
    return code


def _public_registration(data):
    name = (data.get("name") or "").strip()
    phone = (data.get("phone") or "").strip()
    email = (data.get("email") or "").strip().lower()
    test_auto_verify = bool(current_app.config.get("OTP_AUTO_VERIFY_TESTING", False))
    # Backward-compatible fixture behavior only; never enabled by create_app defaults.
    if not phone and test_auto_verify:
        phone = f"TEST-{email}"
    password = data.get("password") or ""
    if not name or not phone or not email or not password:
        raise ValueError("name, phone, email and password are required")
    if len(password) < 8:
        raise ValueError("password must contain at least 8 characters")
    if User.query.filter_by(email=email).first():
        raise ValueError("email already registered")
    # Never accept a public role value. Public accounts are Victims only.
    user = User(name=name, phone=phone, email=email, role=ROLE_VICTIM,
                password_hash=generate_password_hash(password),
                phone_verified=test_auto_verify, is_active=test_auto_verify,
                approval_status="approved")
    db.session.add(user)
    db.session.commit()
    if test_auto_verify:
        return user, None
    demo_code = _issue_phone_otp(user)
    return user, demo_code


@auth_bp.post("/register")
def register_route():
    data = request.get_json(silent=True) or {}
    try:
        user, demo_code = _public_registration(data)
        response = {"message": "Registration received. Verify your phone using the OTP.",
                    "user": user.to_dict(), "verification_required": True}
        if current_app.config.get("OTP_DEMO_MODE", False):
            response["demo_otp"] = demo_code
        return jsonify(response), 201
    except ValueError as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 400


@auth_bp.post("/verify-phone")
def verify_phone_route():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    phone = (data.get("phone") or "").strip()
    code = str(data.get("otp") or "").strip()
    user = User.query.filter_by(email=email, phone=phone).first()
    if not user or not code or user.phone_verified:
        return jsonify({"error": "Invalid or unavailable verification request"}), 400
    challenge = PhoneOTP.query.filter_by(user_id=user.user_id, phone=phone, consumed_at=None).order_by(PhoneOTP.created_at.desc()).first()
    if not challenge or challenge.expires_at < datetime.utcnow() or challenge.attempts >= 5:
        return jsonify({"error": "OTP expired or verification limit exceeded"}), 400
    challenge.attempts += 1
    if not check_password_hash(challenge.otp_hash, code):
        db.session.commit()
        return jsonify({"error": "Incorrect OTP"}), 400
    challenge.consumed_at = datetime.utcnow()
    user.phone_verified = True
    user.is_active = True
    db.session.commit()
    return jsonify({"message": "Phone verified. Your account is active.", "user": user.to_dict()}), 200


@auth_bp.get("/admin/pending-approvals")
@roles_required(ROLE_ADMIN)
def pending_approvals_route():
    users = User.query.filter(User.role.in_([ROLE_ADMIN, "Coordinator"]),
                              User.approval_status == "pending").order_by(User.created_at.asc()).all()
    return jsonify({"accounts": [u.to_dict() for u in users]}), 200


@auth_bp.post("/admin/users/<int:user_id>/approval")
@roles_required(ROLE_ADMIN)
def review_approval_route(user_id):
    data = request.get_json(silent=True) or {}
    decision = (data.get("decision") or "").strip().lower()
    reason = (data.get("reason") or "").strip()
    if decision not in ("approve", "reject"):
        return jsonify({"error": "decision must be approve or reject"}), 400
    user = db.session.get(User, user_id)
    if not user or user.role not in (ROLE_ADMIN, "Coordinator") or user.approval_status != "pending":
        return jsonify({"error": "Account is not eligible for approval"}), 400
    if user.user_id == session.get("user_id"):
        return jsonify({"error": "Administrators cannot approve their own account"}), 403
    user.approval_status = "approved" if decision == "approve" else "rejected"
    user.approval_reviewed_by = session.get("user_id")
    user.approval_reviewed_at = datetime.utcnow()
    user.approval_rejection_reason = reason if decision == "reject" else None
    if decision == "reject":
        user.is_active = False
    db.session.commit()
    return jsonify({"message": f"Account {decision}d", "user": user.to_dict()}), 200


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
