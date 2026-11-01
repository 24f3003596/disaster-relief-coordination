# Sprint 4 Technical Evidence: Dashboard Analytics, CSV Export & Automated Shortage Notifications

**Assignee**: Sree Naresh A (`sreenaresh07@gmail.com`)  
**Sprint**: Sprint 4 (Review 4)  
**Total Story Points**: 8 (Task 1: 5 SP, Task 2: 3 SP)  
**Feature Branch**: [`feature/sprint4-dashboard-analytics-shortage`](https://github.com/24f3003596/disaster-relief-coordination/tree/feature/sprint4-dashboard-analytics-shortage)  
**Pull Request Link**: [Open PR #6 on GitHub](https://github.com/24f3003596/disaster-relief-coordination/pull/new/feature/sprint4-dashboard-analytics-shortage)  
**SRS Requirements Implemented**: FR 3.7.1, FR 3.7.2, and FR 3.6.2  

---

## 1. Executive Summary & Verification Metrics

| Metric | Target / Baseline (Sprint 3) | Sprint 4 Actual | Status |
|---|---|---|---|
| **Total Automated Tests** | 94 tests | **110 tests** (+16 new tests) | ✅ PASS (100%) |
| **Test Execution Pass Rate** | 100% | **100%** (0 failures, 0 errors) | ✅ PASS |
| **Execution Time** | ~41.59s | **54.44s** | ✅ STABLE |
| **Code Coverage (Focus Modules)** | ~76% - 80% | **81%** (`dashboard.py`: 91%, `reports.py`: 92%, `assignments.py`: 80%, `inventory.py`: 78%, `notifications.py`: 72%) | ✅ EXCELLENT |
| **Cyclomatic Complexity (Radon)** | Grade A (4.65 avg) | **Grade A (4.77 avg across 327 blocks)** | ✅ GRADE A |
| **Zero-Denominator Safety** | Handled | **Verified on empty DB & zero capacity** | ✅ ZERO EXCEPTION |
| **CSV Export MIME & Headers** | Validated | **`text/csv`, `Content-Disposition`, RFC 4180 compliant** | ✅ VERIFIED |
| **Role-Based Access Control** | Strictly Admin | **401 unauth, 403 Victim/Volunteer/Coordinator** | ✅ VERIFIED |
| **Notification Alert Restriction** | Coordinator & Admin only | **Victims & Volunteers excluded; deduplicated** | ✅ VERIFIED |

---

## 2. Task 1: Complete Dashboard Analytics and CSV Export (5 Story Points)
**SRS Reference**: FR 3.7.1 & FR 3.7.2

### 2.1 Mathematical Definitions & Specifications

#### 1. Average Response Time
- **Documented Definition**: The average elapsed duration between the exact timestamp when a relief request is created (`ReliefRequest.created_at`) and when an initial inventory resource and volunteer assignment is dispatched (`Assignment.assigned_at`) across all assigned requests:
  $$\text{Response Time} = \text{assigned\_at} - \text{created\_at}$$
  $$\text{Average Response Time} = \frac{1}{N} \sum_{i=1}^N \max(0, (\text{assigned\_at}_i - \text{created\_at}_i))$$
- **Fulfillment Time**: Average duration from `created_at` to `completed_at` for fulfilled assignments:
  $$\text{Fulfillment Time} = \frac{1}{M} \sum_{j=1}^M \max(0, (\text{completed\_at}_j - \text{created\_at}_j))$$
- **Safety**: If $N = 0$ (no assigned requests or empty dataset), both `average_response_time_seconds` and `average_response_time_minutes` safely return `0.0`.

#### 2. Resource Utilization Rate
- **Documented Definition**: The percentage of disaster relief inventory that has been actively utilized or assigned to field tasks relative to the total system capacity (available warehouse stock on hand plus all active/completed assigned stock):
  $$\text{Resource Utilization Rate (\%)} = \left( \frac{\text{Total Allocated Units}}{\text{Available Stock} + \text{Total Allocated Units}} \right) \times 100$$
  Where:
  - $\text{Total Allocated Units} = \sum \text{Assignment.quantity\_assigned}$ (where $\text{status} \neq \text{'Cancelled'}$)
  - $\text{Available Stock} = \sum \text{InventoryItem.quantity}$
  - $\text{Total System Capacity} = \text{Available Stock} + \text{Total Allocated Units}$
- **Safety**: If $\text{Total System Capacity} = 0$, the rate evaluates safely to `0.0%` without raising a `ZeroDivisionError`.

### 2.2 Dashboard Analytics Structure (`GET /dashboard/summary`)
```json
{
  "requests": {
    "total": 4,
    "pending": 2,
    "allocated": 1,
    "completed": 1,
    "by_status": {
      "Pending": 2,
      "Assigned": 1,
      "Fulfilled": 1
    },
    "by_category": {
      "Food": 2,
      "Water": 1,
      "Medical Supplies": 1
    }
  },
  "analytics": {
    "average_response_time_seconds": 600.0,
    "average_response_time_minutes": 10.0,
    "average_fulfillment_time_seconds": 1800.0,
    "average_fulfillment_time_minutes": 30.0,
    "resource_utilization_rate": 40.0,
    "resource_utilization_percent": 40.0,
    "total_allocated_units": 40,
    "total_available_stock": 60,
    "total_system_capacity": 100
  }
}
```

### 2.3 Admin-Authorized CSV Export (FR 3.7.2)
Two secure endpoints implemented with `@login_required` and `@roles_required("Admin")`:
1. `GET /reports/export/relief-requests` (aliases: `/reports/export/requests`, `/dashboard/export/requests`)
   - **Headers**: `request_id,user_id,category,quantity,urgency,location,latitude,longitude,incident_id,status,created_at`
   - **Filename**: `attachment; filename=relief_requests.csv`
2. `GET /reports/export/inventory` (alias: `/dashboard/export/inventory`)
   - **Headers**: `item_id,category,quantity,storage_location,expiry_date,threshold,is_low_stock`
   - **Filename**: `attachment; filename=inventory.csv`

---

## 3. Task 2: Automate Critical-Shortage Notifications (3 Story Points)
**SRS Reference**: FR 3.6.2

### 3.1 Rule Specification
A Critical Shortage Alert is generated if and only if **BOTH** conditions hold simultaneously:
1. **Stock Threshold Condition**: Current available quantity for a resource category in warehouse storage is less than or equal to its configured minimum threshold ($\text{quantity} \le \text{threshold}$).
2. **Demand Condition**: There is at least one active, unfulfilled relief request in that category with `status == "Pending"`.

### 3.2 Key Behaviors & Safeguards
- **No Unmatched Alerts**: Shortages without matching pending requests do **NOT** generate request alerts.
- **Strict Role Targeting**: Alerts are sent **only** to operational coordinators and administrators (`Coordinator` and `Admin`). Victims and Volunteers never receive internal shortage alerts.
- **Deduplication Protection**: If an unread notification of type `Critical Shortage` already exists for a Coordinator or Admin regarding that category, repeated inventory updates or allocations do **NOT** spawn duplicate notification spam.
- **Automatic Event Triggers**:
  - `update_inventory_stock()`: When stock is decremented or adjusted.
  - `create_inventory_item()`: When a new low-stock item is registered.
  - `allocate_request()`: When stock is deducted for a task.
  - `create_relief_request()`: When a new pending request arrives for a category already in shortage.

---

## 4. Test Verification Matrix (16 New Automated Tests)

All 16 test cases located in [`tests/test_sprint4_dashboard_shortage.py`](file:///d:/disaster-relief-coordination-main/tests/test_sprint4_dashboard_shortage.py):

| Test ID | Function Name | Acceptance Criteria Verified | Outcome |
|---|---|---|---|
| **TC-S4-01** | `test_dashboard_displays_request_counts_by_category_and_status` | Task 1 AC1: Request counts by category and status match DB | ✅ PASS |
| **TC-S4-02** | `test_average_response_time_calculation_with_timestamps` | Task 1 AC2: Exact response time calculation with timestamps | ✅ PASS |
| **TC-S4-03** | `test_resource_utilization_rate_calculation` | Task 1 AC3: Utilization formula `(allocated / capacity) * 100` | ✅ PASS |
| **TC-S4-04** | `test_empty_datasets_and_zero_denominators_handled_safely` | Task 1 AC4: Empty dataset returns 0.0 without exception | ✅ PASS |
| **TC-S4-05** | `test_admin_can_export_relief_requests_csv` | Task 1 AC5 & AC7: Admin CSV export with correct headers | ✅ PASS |
| **TC-S4-06** | `test_admin_can_export_inventory_csv` | Task 1 AC6 & AC7: Admin inventory export with correct headers | ✅ PASS |
| **TC-S4-07** | `test_csv_export_access_control_denies_unauthorized_users` | Task 1 AC8: 401 unauth, 403 Victim/Volunteer/Coordinator | ✅ PASS |
| **TC-S4-08** | `test_shortage_notification_generated_when_stock_at_or_below_threshold_with_pending_requests` | Task 2 AC1 & AC2: Shortage alert generated when conditions met | ✅ PASS |
| **TC-S4-09** | `test_shortage_without_matching_pending_requests_does_not_alert` | Task 2 AC3: Zero pending requests suppresses alert | ✅ PASS |
| **TC-S4-10** | `test_non_shortage_scenario_above_threshold_does_not_alert` | Task 2 AC6: Stock above threshold suppresses alert | ✅ PASS |
| **TC-S4-11** | `test_exact_threshold_boundary_conditions` | Task 2 AC6: Exact boundary: `stock == threshold` vs `+1` | ✅ PASS |
| **TC-S4-12** | `test_unauthorized_recipients_do_not_receive_shortage_alerts` | Task 2 AC4: Victims and Volunteers excluded from alert | ✅ PASS |
| **TC-S4-13** | `test_repeated_operations_do_not_duplicate_shortage_notifications` | Task 2 AC5: Deduplication prevents duplicate unread alerts | ✅ PASS |
| **TC-S4-14** | `test_replenishment_and_subsequent_shortage_allows_new_notification` | Task 2 AC5: Read/acknowledged alert allows re-alerting on drop | ✅ PASS |
| **TC-S4-15** | `test_allocation_automatically_triggers_shortage_notification` | Task 2 AC1: Allocation stock reduction triggers shortage check | ✅ PASS |
| **TC-S4-16** | `test_new_pending_request_triggers_shortage_if_stock_already_low` | Task 2 AC1: New pending request triggers shortage alert | ✅ PASS |

---

## 5. Test Run Evidence Log

```text
============================= test session starts =============================
platform win32 -- Python 3.14.5, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\disaster-relief-coordination-main
plugins: anyio-4.14.2, asyncio-1.4.0, cov-7.1.0

collected 110 items

tests\test_assignments.py ..........                                     [  9%]
tests\test_audit.py ...                                                  [ 11%]
tests\test_auth.py ................                                      [ 26%]
tests\test_dashboard.py ..                                               [ 28%]
tests\test_end_to_end_workflow.py .                                      [ 29%]
tests\test_incidents.py ........                                         [ 36%]
tests\test_integration.py ....                                           [ 40%]
tests\test_inventory.py .......                                          [ 46%]
tests\test_inventory_resource_consistency.py .............               [ 58%]
tests\test_notifications.py ..                                           [ 60%]
tests\test_rbac.py .........                                             [ 68%]
tests\test_reports.py ....                                               [ 71%]
tests\test_requests.py ...........                                       [ 81%]
tests\test_sprint4_dashboard_shortage.py ................                [ 96%]
tests\test_volunteers.py ....                                            [100%]

====================== 110 passed in 54.44s ======================
```
