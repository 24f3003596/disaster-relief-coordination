# Requirements Traceability Matrix (RTM)

**Project**: Disaster Relief Resource Coordination System (Team 20)  
**Sprint**: Sprint 5 (Final Release & Review 5 Delivery)  
**Baseline Document**: Approved System Requirements Specification (SRS Sections 3.1–3.8)  
**Total Requirements Traced**: 24 Functional Requirements across 8 Modules  
**Overall Traceability Status**: 100% Covered & Verified  

---

## 1. Executive Traceability Overview

The Requirements Traceability Matrix establishes bidirectional traceability between customer requirements documented in the SRS, application components, automated regression tests, and end-to-end User Acceptance Testing (UAT) scenarios.

```
+------------------+       +-------------------+       +-----------------------+       +-------------------+
|     SRS FR       | ----> | Source Code       | ----> | Automated Pytest      | ----> | End-to-End UAT    |
| (Requirements)   |       | (Blueprints/API)  |       | (149 Unit/Integ Tests)|       | (10 Scenarios)    |
+------------------+       +-------------------+       +-----------------------+       +-------------------+
```

---

## 2. Requirements Traceability Matrix

| FR ID | Requirement Description | Implementation Module | Automated Test Files | UAT Test Scenario | Verification Status |
|---|---|---|---|---|---|
| **FR 3.1.1** | Public User Registration (Defaults to Victim role; requires valid phone and credentials) | `auth.py`, `models.py` | `test_auth.py`, `test_sprint4_security.py` | UAT-001 | ✅ VERIFIED |
| **FR 3.1.2** | Phone OTP Two-Factor Authentication (Challenge issuance, secure hashing, expiry) | `auth.py`, `models.py` | `test_sprint4_security.py` | UAT-001 | ✅ VERIFIED |
| **FR 3.1.3** | User Authentication & Session Management (PBKDF2/Werkzeug hashing, RBAC enforcement) | `auth.py`, `app.py` | `test_auth.py`, `test_rbac.py` | UAT-001, UAT-002, UAT-010 | ✅ VERIFIED |
| **FR 3.1.4** | Privileged Role Approval Queue (Admin approval required for Coordinator/Admin promotions) | `auth.py`, `models.py` | `test_sprint4_security.py` | UAT-002 | ✅ VERIFIED |
| **FR 3.2.1** | Disaster Incident Creation (Title, description, geospatial coordinates, severity level) | `incidents.py`, `models.py` | `test_incidents.py` | UAT-004 | ✅ VERIFIED |
| **FR 3.2.2** | Incident Status Lifecycle (`Open` → `In Progress` → `Resolved` → `Closed`) | `incidents.py` | `test_incidents.py`, `test_activity_history.py` | UAT-004 | ✅ VERIFIED |
| **FR 3.2.3** | Incident Modification & Affected Areas Listing | `incidents.py` | `test_incidents.py` | UAT-004 | ✅ VERIFIED |
| **FR 3.2.4** | Incident Role Authorization (Coordinator and Admin operational restriction) | `incidents.py`, `auth.py` | `test_incidents.py`, `test_rbac.py` | UAT-004 | ✅ VERIFIED |
| **FR 3.3.1** | Relief Request Submission (Category, quantity, urgency, location, coordinates) | `requests_module.py`, `models.py` | `test_requests.py`, `test_integration.py` | UAT-003 | ✅ VERIFIED |
| **FR 3.3.2** | Request Status Lifecycle (`Pending` → `Assigned` → `In Progress` → `Fulfilled` / `Rejected`) | `requests_module.py` | `test_requests.py`, `test_assignments.py` | UAT-003, UAT-007 | ✅ VERIFIED |
| **FR 3.3.3** | Personal Request Tracking & Role Isolation (Victim sees only own requests; Ops sees all) | `requests_module.py` | `test_requests.py`, `test_rbac.py` | UAT-003 | ✅ VERIFIED |
| **FR 3.3.4** | Request Geospatial Coordinate Parsing & Bounding Validation | `requests_module.py` | `test_requests.py` | UAT-003, UAT-009 | ✅ VERIFIED |
| **FR 3.4.1** | Warehouse Inventory Item Registration & Stock Inward | `inventory.py`, `models.py` | `test_inventory.py` | UAT-005 | ✅ VERIFIED |
| **FR 3.4.2** | Low-Stock Threshold Configuration & Boundary Safety | `inventory.py`, `notifications.py` | `test_inventory.py`, `test_sprint4_dashboard_shortage.py` | UAT-005, UAT-008 | ✅ VERIFIED |
| **FR 3.4.3** | Atomic Stock Deduction & Negative Balance Prevention | `assignments.py`, `inventory.py` | `test_assignments.py`, `test_inventory_resource_consistency.py` | UAT-006 | ✅ VERIFIED |
| **FR 3.4.4** | Idempotency & Repeated Operation Safeguards (Prevent double allocation/deduction) | `assignments.py` | `test_inventory_resource_consistency.py` | UAT-006 | ✅ VERIFIED |
| **FR 3.5.1** | Atomic Inventory Allocation to Relief Request | `assignments.py`, `models.py` | `test_assignments.py`, `test_end_to_end_workflow.py` | UAT-006 | ✅ VERIFIED |
| **FR 3.5.2** | Volunteer Dispatch & Mission Assignment | `assignments.py`, `volunteers.py` | `test_assignments.py`, `test_volunteers.py` | UAT-006, UAT-007 | ✅ VERIFIED |
| **FR 3.5.3** | Volunteer Mission Execution (`Assigned` → `In Progress` → `Completed`) | `assignments.py` | `test_assignments.py` | UAT-007 | ✅ VERIFIED |
| **FR 3.5.4** | Automatic Request Fulfillment upon Assignment Completion | `assignments.py`, `requests_module.py` | `test_assignments.py`, `test_end_to_end_workflow.py` | UAT-007 | ✅ VERIFIED |
| **FR 3.6.1** | Dual In-App Operational Notifications (Dispatched volunteer & victim recipient) | `notifications.py`, `assignments.py` | `test_assignments.py`, `test_notifications.py` | UAT-007 | ✅ VERIFIED |
| **FR 3.6.2** | Automated Critical Shortage Alerting with Duplicate Suppression | `notifications.py`, `inventory.py` | `test_sprint4_dashboard_shortage.py` | UAT-008 | ✅ VERIFIED |
| **FR 3.7.1** | Operational Dashboard Analytics (Response Time, Utilization Rate, Category/Status Totals) | `dashboard.py`, `reports.py` | `test_sprint4_dashboard_shortage.py`, `test_dashboard.py` | UAT-010 | ✅ VERIFIED |
| **FR 3.7.2** | Admin-Authorized CSV Export (Requests & Inventory datasets; strict Admin protection) | `dashboard.py`, `reports.py` | `test_sprint4_dashboard_shortage.py` | UAT-010 | ✅ VERIFIED |
| **FR 3.8.1** | Geospatial Disaster Map Visualization & Viewport Bounding Filtering | `map_view.py`, `templates/map.html` | `test_map_view.py` | UAT-009 | ✅ VERIFIED |
| **FR 3.8.2** | Leaflet Marker Clustering & Fallback Handling | `map_view.py`, `templates/map.html` | `test_map_view.py` | UAT-009 | ✅ VERIFIED |
| **FR 3.8.3** | Chronological Audit Trail & Activity History per Request/Incident | `audit.py`, `templates/activity_history.html` | `test_activity_history.py`, `test_audit.py` | UAT-003, UAT-004 | ✅ VERIFIED |

---

## 3. Test Coverage by Functional Area

| SRS Functional Area | Total FRs | Automated Unit/Integ Tests | UAT Test Cases | Coverage Rate | Status |
|---|---|---|---|---|---|
| **Section 3.1: User Management & Security** | 4 | 28 tests | UAT-001, UAT-002, UAT-010 | 100% | ✅ Complete |
| **Section 3.2: Incident Management** | 4 | 16 tests | UAT-004 | 100% | ✅ Complete |
| **Section 3.3: Relief Request Management** | 4 | 24 tests | UAT-003, UAT-007 | 100% | ✅ Complete |
| **Section 3.4: Inventory & Warehouse Consistency**| 4 | 26 tests | UAT-005, UAT-006, UAT-008 | 100% | ✅ Complete |
| **Section 3.5: Resource Allocation & Volunteers** | 4 | 22 tests | UAT-006, UAT-007 | 100% | ✅ Complete |
| **Section 3.6: Notification & In-App Alerts** | 2 | 14 tests | UAT-007, UAT-008 | 100% | ✅ Complete |
| **Section 3.7: Operations Dashboard & CSV Export**| 2 | 12 tests | UAT-010 | 100% | ✅ Complete |
| **Section 3.8: Geospatial Map & Activity History** | 3 | 7 tests | UAT-003, UAT-004, UAT-009 | 100% | ✅ Complete |
| **Total Project Scope** | **27 FRs** | **149 tests** | **10 UAT Scenarios** | **100%** | **✅ PASSED** |
