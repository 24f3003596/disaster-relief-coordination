from models import User, Assignment

def list_volunteers():
    return User.query.filter_by(role="Volunteer").order_by(User.name.asc()).all()

def get_volunteer_assignments(volunteer_id):
    volunteer = User.query.filter_by(user_id=volunteer_id, role="Volunteer").first()
    if volunteer is None: raise ValueError("Volunteer not found")
    return Assignment.query.filter_by(volunteer_id=volunteer_id).order_by(Assignment.assigned_at.desc()).all()
