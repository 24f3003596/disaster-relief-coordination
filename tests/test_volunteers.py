import pytest
from auth import register_user
from volunteers import list_volunteers, get_volunteer_assignments
from assignments import allocate_request


def test_list_volunteers_returns_only_volunteer_role(app, seed):
    with app.app_context():
        volunteers = list_volunteers()
        assert len(volunteers) == 1
        assert volunteers[0].user_id == seed["volunteer"]
        assert volunteers[0].role == "Volunteer"


def test_get_volunteer_assignments_returns_assigned_tasks(app, seed):
    with app.app_context():
        assignment = allocate_request(seed["request"], seed["volunteer"], seed["item"])
        result = get_volunteer_assignments(seed["volunteer"])
        assert len(result) == 1
        assert result[0].task_id == assignment.task_id


def test_get_volunteer_assignments_rejects_non_volunteer(app, seed):
    with app.app_context():
        with pytest.raises(ValueError, match="Volunteer not found"):
            get_volunteer_assignments(seed["victim"])


def test_get_volunteer_assignments_rejects_unknown_user(app):
    with app.app_context():
        with pytest.raises(ValueError, match="Volunteer not found"):
            get_volunteer_assignments(99999)
