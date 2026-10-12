from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models import User
from constants import ROLES

def register_user(name, phone, email, password, role="Victim"):
    if not name or not name.strip(): raise ValueError("Name is required")
    if not email or "@" not in email: raise ValueError("A valid email is required")
    if not password or len(password) < 8: raise ValueError("Password must contain at least 8 characters")
    if role not in ROLES: raise ValueError("Invalid role")
    email = email.strip().lower()
    if User.query.filter_by(email=email).first(): raise ValueError("Email is already registered")
    user = User(name=name.strip(), phone=phone, email=email, role=role, password_hash=generate_password_hash(password))
    db.session.add(user); db.session.commit(); return user

def authenticate_user(email, password):
    user = User.query.filter_by(email=(email or "").strip().lower()).first()
    return user if user and check_password_hash(user.password_hash, password or "") else None

def update_user_role(user_id, new_role, actor_id):
    actor = db.session.get(User, actor_id)
    user = db.session.get(User, user_id)
    if not actor or actor.role != "Admin": raise PermissionError("Only an Admin can change roles")
    if not user: raise ValueError("User not found")
    if new_role not in ROLES: raise ValueError("Invalid role")
    user.role = new_role; db.session.commit(); return user
