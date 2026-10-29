import pytest
from extensions import db
from models import Assignment, InventoryItem, ReliefRequest, Notification, AuditLog, User
from assignments import allocate_request, update_assignment_status, complete_assignment
from inventory import create_inventory_item, update_inventory_stock
from constants import (
    ROLE_VOLUNTEER,
    ROLE_VICTIM,
    STATUS_REQUEST_PENDING,
    STATUS_REQUEST_ASSIGNED,
    STATUS_REQUEST_FULFILLED,
    STATUS_ASSIGNMENT_ASSIGNED,
    STATUS_ASSIGNMENT_ACCEPTED,
    STATUS_ASSIGNMENT_IN_PROGRESS,
    STATUS_ASSIGNMENT_COMPLETED,
    STATUS_ASSIGNMENT_UNABLE,
    STATUS_ASSIGNMENT_CANCELLED,
    CATEGORY_FOOD_WATER,
    CATEGORY_MEDICAL,
)

# ---------------------------------------------------------------------------
# Task 1: Verify Inventory and Resource Consistency Tests
# ---------------------------------------------------------------------------

def test_successful_allocation_updates_all_records_atomically(app, seed):
    """AC1: Successful allocations update relevant records correctly."""
    with app.app_context():
        item_before = db.session.get(InventoryItem, seed["item"]).quantity
        assignment = allocate_request(seed["request"], seed["volunteer"], seed["item"])

        assert assignment.task_id is not None
        assert assignment.quantity_assigned == 4
        assert assignment.status == STATUS_ASSIGNMENT_ASSIGNED

        # Verify stock decremented exactly
        item_after = db.session.get(InventoryItem, seed["item"])
        assert item_after.quantity == item_before - 4

        # Verify relief request transitioned to Assigned
        req = db.session.get(ReliefRequest, seed["request"])
        assert req.status == STATUS_REQUEST_ASSIGNED

        # Verify notifications sent to both volunteer and victim
        v_notifs = Notification.query.filter_by(user_id=seed["volunteer"]).all()
        assert any("assigned request" in n.message.lower() for n in v_notifs)

        req_notifs = Notification.query.filter_by(user_id=seed["victim"]).all()
        assert any("allocated to volunteer" in n.message.lower() for n in req_notifs)


def test_allocation_rejects_category_mismatch_without_data_corruption(app, seed):
    """AC2: Failed allocations do not leave inconsistent data (incompatible category)."""
    with app.app_context():
        # Create an inventory item with a different category
        med_item = create_inventory_item(
            category=CATEGORY_MEDICAL,
            quantity=50,
            storage_location="Clinic Shelf",
            threshold=10,
        )
        stock_before = med_item.quantity

        with pytest.raises(ValueError, match="category must match"):
            allocate_request(seed["request"], seed["volunteer"], med_item.item_id)

        # Inventory unchanged
        assert db.session.get(InventoryItem, med_item.item_id).quantity == stock_before
        # Request remains pending
        assert db.session.get(ReliefRequest, seed["request"]).status == STATUS_REQUEST_PENDING
        # No assignment created
        assert Assignment.query.filter_by(request_id=seed["request"]).count() == 0


def test_allocation_rejects_quantity_exceeding_requested_amount(app, seed):
    """AC2: Allocating more than requested amount is rejected without state change."""
    with app.app_context():
        stock_before = db.session.get(InventoryItem, seed["item"]).quantity

        # Request requires 4 units, attempt to allocate 10 units
        with pytest.raises(ValueError, match="cannot exceed requested quantity"):
            allocate_request(seed["request"], seed["volunteer"], seed["item"], quantity_assigned=10)

        assert db.session.get(InventoryItem, seed["item"]).quantity == stock_before
        assert db.session.get(ReliefRequest, seed["request"]).status == STATUS_REQUEST_PENDING
        assert Assignment.query.count() == 0


def test_failed_field_delivery_restores_inventory_and_resets_request(app, seed):
    """AC2: When delivery is marked 'Unable to Complete', stock is restored and request returns to Pending."""
    with app.app_context():
        initial_stock = db.session.get(InventoryItem, seed["item"]).quantity
        assignment = allocate_request(seed["request"], seed["volunteer"], seed["item"], quantity_assigned=4)

        # Stock deducted to initial - 4
        assert db.session.get(InventoryItem, seed["item"]).quantity == initial_stock - 4
        assert db.session.get(ReliefRequest, seed["request"]).status == STATUS_REQUEST_ASSIGNED

        # Volunteer encounters blocked road / flat tire -> Unable to Complete
        updated = update_assignment_status(assignment.task_id, STATUS_ASSIGNMENT_UNABLE)
        assert updated.status == STATUS_ASSIGNMENT_UNABLE

        # Stock MUST be restored to initial quantity
        restored_stock = db.session.get(InventoryItem, seed["item"]).quantity
        assert restored_stock == initial_stock

        # Request status MUST be reset to Pending so it can be reallocated
        req = db.session.get(ReliefRequest, seed["request"])
        assert req.status == STATUS_REQUEST_PENDING


def test_cancelled_assignment_restores_inventory_and_resets_request(app, seed):
    """AC2: When coordinator cancels an assignment, resources are restored and request returns to Pending."""
    with app.app_context():
        initial_stock = db.session.get(InventoryItem, seed["item"]).quantity
        assignment = allocate_request(seed["request"], seed["volunteer"], seed["item"])

        # Coordinator cancels the assignment
        update_assignment_status(assignment.task_id, STATUS_ASSIGNMENT_CANCELLED)

        # Stock restored
        assert db.session.get(InventoryItem, seed["item"]).quantity == initial_stock
        # Request reopened
        assert db.session.get(ReliefRequest, seed["request"]).status == STATUS_REQUEST_PENDING


def test_reallocation_succeeds_after_previous_assignment_failed(app, seed):
    """AC2: Re-allocation succeeds after a previous assignment failed, without orphan data."""
    with app.app_context():
        initial_stock = db.session.get(InventoryItem, seed["item"]).quantity
        # Create second volunteer
        vol2 = User(name="Volunteer Two", email="vol2@example.com", role=ROLE_VOLUNTEER, password_hash="hash")
        db.session.add(vol2)
        db.session.commit()

        # Step 1: First allocation to Volunteer 1
        a1 = allocate_request(seed["request"], seed["volunteer"], seed["item"])
        assert db.session.get(InventoryItem, seed["item"]).quantity == initial_stock - 4

        # Step 2: Volunteer 1 fails delivery
        update_assignment_status(a1.task_id, STATUS_ASSIGNMENT_UNABLE)
        assert db.session.get(InventoryItem, seed["item"]).quantity == initial_stock
        assert db.session.get(ReliefRequest, seed["request"]).status == STATUS_REQUEST_PENDING

        # Step 3: Reallocate to Volunteer 2
        a2 = allocate_request(seed["request"], vol2.user_id, seed["item"])
        assert a2.task_id == a1.task_id
        assert a2.volunteer_id == vol2.user_id
        assert a2.status == STATUS_ASSIGNMENT_ASSIGNED
        assert db.session.get(InventoryItem, seed["item"]).quantity == initial_stock - 4
        assert db.session.get(ReliefRequest, seed["request"]).status == STATUS_REQUEST_ASSIGNED

        # Step 4: Volunteer 2 completes delivery
        update_assignment_status(a2.task_id, STATUS_ASSIGNMENT_COMPLETED)
        assert db.session.get(ReliefRequest, seed["request"]).status == STATUS_REQUEST_FULFILLED
        assert db.session.get(InventoryItem, seed["item"]).quantity == initial_stock - 4


def test_insufficient_stock_exact_boundary_conditions(app, seed):
    """AC3: Insufficient resources handled safely at exact boundary values."""
    with app.app_context():
        item = db.session.get(InventoryItem, seed["item"])
        item.quantity = 4  # Exactly matches request quantity of 4
        db.session.commit()

        # Allocation of exactly available stock should succeed and bring quantity to 0
        a = allocate_request(seed["request"], seed["volunteer"], seed["item"])
        assert a.quantity_assigned == 4
        assert db.session.get(InventoryItem, seed["item"]).quantity == 0

        # Create a second request of 1 unit
        req2 = ReliefRequest(
            user_id=seed["victim"],
            category=item.category,
            quantity=1,
            urgency="Medium",
            status=STATUS_REQUEST_PENDING,
            location="Zone B Shelter",
        )
        db.session.add(req2)
        db.session.commit()

        # Allocation when stock is 0 MUST be safely rejected
        with pytest.raises(ValueError, match="Insufficient inventory stock"):
            allocate_request(req2.request_id, seed["volunteer"], seed["item"])

        # Stock remains 0, second request remains Pending, no second assignment
        assert db.session.get(InventoryItem, seed["item"]).quantity == 0
        assert req2.status == STATUS_REQUEST_PENDING
        assert Assignment.query.count() == 1


def test_repeated_allocation_call_does_not_duplicate_or_leak_stock(app, seed):
    """AC4: Repeated allocation attempts on the same request do not duplicate or leak stock."""
    with app.app_context():
        initial_stock = db.session.get(InventoryItem, seed["item"]).quantity

        # First allocation
        a1 = allocate_request(seed["request"], seed["volunteer"], seed["item"])
        stock_after_first = db.session.get(InventoryItem, seed["item"]).quantity
        assert stock_after_first == initial_stock - 4

        # Repeated allocation attempt (e.g. double click)
        with pytest.raises(ValueError):
            allocate_request(seed["request"], seed["volunteer"], seed["item"])

        # Stock must remain unchanged from stock_after_first
        assert db.session.get(InventoryItem, seed["item"]).quantity == stock_after_first
        # Only one assignment exists for this request
        assert Assignment.query.filter_by(request_id=seed["request"]).count() == 1


def test_terminal_assignment_status_cannot_be_mutated(app, seed):
    """AC4: A completed assignment cannot be transitioned to other statuses (prevents stock corruption)."""
    with app.app_context():
        a = allocate_request(seed["request"], seed["volunteer"], seed["item"])
        complete_assignment(a.task_id)

        assert db.session.get(Assignment, a.task_id).status == STATUS_ASSIGNMENT_COMPLETED
        stock_completed = db.session.get(InventoryItem, seed["item"]).quantity

        # Attempting to cancel an already completed assignment MUST be rejected
        with pytest.raises(ValueError, match="Cannot change status of an assignment that is already Completed"):
            update_assignment_status(a.task_id, STATUS_ASSIGNMENT_CANCELLED)

        # Stock is NOT refunded for a completed delivery
        assert db.session.get(InventoryItem, seed["item"]).quantity == stock_completed
        assert db.session.get(ReliefRequest, seed["request"]).status == STATUS_REQUEST_FULFILLED


def test_repeated_status_update_is_idempotent(app, seed):
    """AC4: Repeated status updates to the same status are safe and idempotent."""
    with app.app_context():
        a = allocate_request(seed["request"], seed["volunteer"], seed["item"])
        update_assignment_status(a.task_id, STATUS_ASSIGNMENT_IN_PROGRESS)

        # Re-applying same status
        same = update_assignment_status(a.task_id, STATUS_ASSIGNMENT_IN_PROGRESS)
        assert same.status == STATUS_ASSIGNMENT_IN_PROGRESS


def test_repeated_failed_assignment_does_not_double_refund_stock(app, seed):
    """AC4: Repeatedly updating a failed assignment does not double-refund stock."""
    with app.app_context():
        initial_stock = db.session.get(InventoryItem, seed["item"]).quantity
        a = allocate_request(seed["request"], seed["volunteer"], seed["item"])

        # First failure marks Unable to Complete and restores stock
        update_assignment_status(a.task_id, STATUS_ASSIGNMENT_UNABLE)
        assert db.session.get(InventoryItem, seed["item"]).quantity == initial_stock

        # Second identical update call is idempotent and does not add stock again
        update_assignment_status(a.task_id, STATUS_ASSIGNMENT_UNABLE)
        assert db.session.get(InventoryItem, seed["item"]).quantity == initial_stock


def test_mathematical_stock_consistency_across_multiple_allocations(app, seed):
    """AC5: Mathematical invariant: initial_stock - sum(allocations) == current_stock."""
    with app.app_context():
        item = db.session.get(InventoryItem, seed["item"])
        item.quantity = 100
        db.session.commit()

        initial_stock = 100
        quantities = [10, 15, 25, 5, 20]  # Sum = 75
        allocated_total = 0

        for i, q in enumerate(quantities):
            req = ReliefRequest(
                user_id=seed["victim"],
                category=item.category,
                quantity=q,
                urgency="Medium",
                status=STATUS_REQUEST_PENDING,
                location=f"Zone {i} Sector",
            )
            db.session.add(req)
            db.session.commit()

            allocate_request(req.request_id, seed["volunteer"], item.item_id)
            allocated_total += q

            # Strict invariant check at each step
            current = db.session.get(InventoryItem, item.item_id).quantity
            assert current == initial_stock - allocated_total

        assert db.session.get(InventoryItem, item.item_id).quantity == 25


def test_allocate_route_missing_parameters_returns_400_without_state_change(app, client, seed):
    """AC4 & AC5: API route rejects missing payload fields with 400 without crashing with 500."""
    with app.app_context():
        stock_before = db.session.get(InventoryItem, seed["item"]).quantity

    # Empty payload
    res1 = client.post("/assignments/allocate", json={})
    assert res1.status_code == 400
    assert "required" in res1.json["error"]

    # Missing volunteer_id
    res2 = client.post("/assignments/allocate", json={"request_id": seed["request"], "item_id": seed["item"]})
    assert res2.status_code == 400

    # Non-numeric string IDs
    res3 = client.post("/assignments/allocate", json={"request_id": "bad", "volunteer_id": "vol", "item_id": "itm"})
    assert res3.status_code == 400

    with app.app_context():
        # Stock untouched across all bad API calls
        assert db.session.get(InventoryItem, seed["item"]).quantity == stock_before
        assert Assignment.query.count() == 0
