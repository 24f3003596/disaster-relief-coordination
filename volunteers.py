from flask import Blueprint, jsonify, request

from extensions import db
from models import User, Assignment
from constants import ROLE_VOLUNTEER

volunteers_bp = Blueprint("volunteers", __name__)

def list_volunteers():
    """Retrieve all users registered with the Volunteer role."""
    return User.query.filter_by(role=ROLE_VOLUNTEER).order_by(User.name.asc()).all()

def get_volunteer_assignments(volunteer_id):
    """Retrieve all tasks assigned to a specific volunteer."""
    volunteer = User.query.filter_by(user_id=volunteer_id, role=ROLE_VOLUNTEER).first()
    if volunteer is None:
        raise ValueError("Volunteer not found")

    return (
        Assignment.query.filter_by(volunteer_id=volunteer_id)
        .order_by(Assignment.assigned_at.desc())
        .all()
    )

@volunteers_bp.get("/")
def list_volunteers_route():
    volunteers = list_volunteers()
    return jsonify({"volunteers": [v.to_dict() for v in volunteers]}), 200

@volunteers_bp.get("/<int:volunteer_id>/assignments")
def get_assignments_route(volunteer_id):
    try:
        tasks = get_volunteer_assignments(volunteer_id)
        return jsonify({"assignments": [t.to_dict() for t in tasks]}), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404
