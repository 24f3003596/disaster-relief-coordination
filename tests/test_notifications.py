import pytest
from notifications import create_notification, mark_notification_read, broadcast_emergency_alert
from models import Notification, User
from extensions import db

def test_mark_read_only_for_owner(app,seed):
    with app.app_context():
        n=create_notification(seed["volunteer"],"Test message","General"); db.session.commit()
        with pytest.raises(ValueError): mark_notification_read(n.notification_id,seed["victim"])
        assert mark_notification_read(n.notification_id,seed["volunteer"]).is_read is True

def test_broadcast_targets_operational_roles(app,seed):
    with app.app_context():
        created=broadcast_emergency_alert("Flood warning","Emergency")
        assert len(created)==1
        assert User.query.filter_by(role="Volunteer").first().notifications[0].type=="Emergency"
