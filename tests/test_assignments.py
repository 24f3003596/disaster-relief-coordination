
import pytest

from extensions import db
from models import Assignment, InventoryItem, ReliefRequest, Notification
from assignments import allocate_request, update_assignment_status


def test_allocate_updates_stock_request_and_notification(app, seed):
    with app.app_context():
        a = allocate_request(
            seed["request"], seed["volunteer"], seed["item"]
        )

        assert a.quantity_assigned == 4
        assert db.session.get(
            InventoryItem, seed["item"]
        ).quantity == 6
        assert db.session.get(
            ReliefRequest, seed["request"]
        ).status == "Assigned"
        assert Notification.query.filter_by(
            user_id=seed["volunteer"]
        ).count() == 1


def test_allocation_rejects_insufficient_stock_without_changes(app, seed):
    with app.app_context():
        item = db.session.get(InventoryItem, seed["item"])
        item.quantity = 2
        db.session.commit()

        with pytest.raises(ValueError, match="Insufficient"):
            allocate_request(
                seed["request"], seed["volunteer"], seed["item"]
            )

        assert db.session.get(
            InventoryItem, seed["item"]
        ).quantity == 2
        assert Assignment.query.count() == 0


def test_complete_assignment_marks_request_fulfilled(app, seed):
    with app.app_context():
        a = allocate_request(
            seed["request"], seed["volunteer"], seed["item"]
        )

        update_assignment_status(a.task_id, "Completed")

        assert db.session.get(
            Assignment, a.task_id
        ).status == "Completed"
        assert db.session.get(
            ReliefRequest, seed["request"]
        ).status == "Fulfilled"


def test_non_volunteer_cannot_be_assigned(app, seed):
    with app.app_context():
        with pytest.raises(ValueError, match="Volunteer"):
            allocate_request(
                seed["request"], seed["victim"], seed["item"]
            )


def test_allocation_rejects_nonexistent_request(app, seed):
    with app.app_context():
        stock_before = db.session.get(
            InventoryItem, seed["item"]
        ).quantity

        with pytest.raises(
            ValueError, match="Relief request not found"
        ):
            allocate_request(
                999999, seed["volunteer"], seed["item"]
            )

        assert db.session.get(
            InventoryItem, seed["item"]
        ).quantity == stock_before
        assert Assignment.query.count() == 0


def test_allocation_rejects_nonexistent_inventory(app, seed):
    with app.app_context():
        with pytest.raises(
            ValueError, match="Inventory item not found"
        ):
            allocate_request(
                seed["request"], seed["volunteer"], 999999
            )

        assert db.session.get(
            ReliefRequest, seed["request"]
        ).status == "Pending"
        assert Assignment.query.count() == 0


@pytest.mark.parametrize("quantity", [0, -1, "invalid"])
def test_invalid_allocation_quantity_changes_nothing(
    app, seed, quantity
):
    with app.app_context():
        stock_before = db.session.get(
            InventoryItem, seed["item"]
        ).quantity

        with pytest.raises(ValueError):
            allocate_request(
                seed["request"],
                seed["volunteer"],
                seed["item"],
                quantity_assigned=quantity,
            )

        assert db.session.get(
            InventoryItem, seed["item"]
        ).quantity == stock_before
        assert db.session.get(
            ReliefRequest, seed["request"]
        ).status == "Pending"
        assert Assignment.query.count() == 0


def test_allocation_rejects_duplicate_request(app, seed):
    with app.app_context():
        allocate_request(
            seed["request"], seed["volunteer"], seed["item"]
        )

        stock_after_first = db.session.get(
            InventoryItem, seed["item"]
        ).quantity

        with pytest.raises(
            ValueError,
            match="Only pending requests can be allocated",
        ):
            allocate_request(
                seed["request"], seed["volunteer"], seed["item"]
            )

        assert db.session.get(
            InventoryItem, seed["item"]
        ).quantity == stock_after_first

        assert Assignment.query.filter_by(
            request_id=seed["request"]
        ).count() == 1
