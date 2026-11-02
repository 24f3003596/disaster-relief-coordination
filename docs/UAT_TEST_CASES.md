# User Acceptance Testing (UAT) Test Cases Specification

**Project**: Disaster Relief Resource Coordination System (Team 20)  
**Sprint**: Sprint 5 (Final Acceptance Review)  
**Test Suite**: `tests/test_sprint5_uat.py`  
**Target Environment**: Python 3.14 / Flask 3.1 / SQLite  
**Quality Benchmark**: Approved System Requirements Specification (SRS Sections 3.1–3.8)  
**Execution Status**: 10 Scenarios Executed — 10 Passed (100% Pass Rate)

---

## 1. UAT Scope & Persona Definition

User Acceptance Testing evaluates the system against realistic multi-role operational scenarios from the perspective of four distinct personas:
1. **Public Citizen / Victim (Persona: Jane Citizen)**: Affected individual registering under disaster distress, submitting life-essential resource requests with coordinates, and tracking progress without operational privileges.
2. **Operations Coordinator (Persona: Field Dispatcher Alex)**: Operational staff triaging incidents, monitoring disaster map overlays, managing warehouse inventory batches, and executing atomic resource allocations.
3. **Field Volunteer (Persona: Responder Hero)**: Authorized responder receiving dispatched supply missions, advancing delivery statuses (Assigned → In Progress → Completed), and triggering fulfillment notifications.
4. **System Administrator (Persona: Operations Admin)**: Privileged authority managing the user approval queue, granting elevated roles, monitoring system audits, and exporting administrative CSV reports.

---

## 2. Detailed UAT Test Case Specifications

### UAT-001: Public Citizen Registration, OTP Verification, and Login
- **Test ID**: UAT-001
- **User Role**: Citizen / Victim
- **SRS References**: FR 3.1.1, FR 3.1.2, FR 3.1.3
- **Objective**: Verify that an affected citizen can register via public portal with valid phone and email, receive automatic Victim role assignment, complete verification, and authenticate into the relief portal.
- **Preconditions**: Application running; test database clean.
- **Test Data**:
  - Name: `Jane Citizen`
  - Phone: `+919876543210`
  - Email: `jane.citizen@example.com`
  - Password: `SecurePassword123`
- **Execution Steps**:
  1. POST `/register` with name, phone, email, password, and confirmation.
  2. Verify HTTP 200 response and presence of user row in `users` table with `role="Victim"`, `phone_verified=True`, and `approval_status="approved"`.
  3. POST `/login` with credentials.
  4. Access authenticated route `/requests/`.
- **Expected Outcome**: Citizen account created without elevated privileges; session established; access to victim portal granted; restricted administrative views blocked.
- **Actual Outcome**: ✅ Passed (HTTP 200; Session active; user isolated to victim capabilities).

---

### UAT-002: Privileged Role Promotion & Admin Approval Queue
- **Test ID**: UAT-002
- **User Role**: Coordinator / System Administrator
- **SRS References**: FR 3.1.3, FR 3.1.4
- **Objective**: Validate that requests for privileged operational roles (Coordinator/Admin) are placed into a pending approval queue and prevented from authenticating until an Administrator explicitly reviews and approves the account.
- **Preconditions**: Administrator account (`admin.ops@example.com`) active and approved.
- **Test Data**: Candidate: `Alex Candidate` (`alex.candidate@example.com`).
- **Execution Steps**:
  1. Admin authenticates via `/auth/login`.
  2. Admin promotes candidate to `Coordinator` via PATCH `/auth/users/<id>/role`.
  3. Verify candidate `approval_status` transitions to `pending`.
  4. Candidate attempts `/auth/login` while pending.
  5. Admin queries `/auth/admin/pending-approvals`.
  6. Admin posts approval via POST `/auth/admin/users/<id>/approval` with `decision="approve"`.
  7. Candidate logs in again via `/auth/login`.
- **Expected Outcome**: Candidate login blocked with HTTP 401 while pending; candidate appears in admin approval queue; upon admin approval, candidate login succeeds with HTTP 200 and role reflects Coordinator.
- **Actual Outcome**: ✅ Passed (Pending user prevented from logging in; approved successfully by admin; full coordinator access granted post-approval).

---

### UAT-003: Victim Relief Request Intake & Coordinate Validation
- **Test ID**: UAT-003
- **User Role**: Citizen / Victim
- **SRS References**: FR 3.3.1, FR 3.3.3, FR 3.3.4
- **Objective**: Validate emergency relief request submission with geospatial coordinates, verify initial `Pending` status, and enforce strict role data isolation preventing other victims from viewing or tampering with requests.
- **Preconditions**: Two victim accounts (`victim1@example.com` and `victim2@example.com`) registered.
- **Test Data**:
  - Category: `Medical Supplies`
  - Quantity: `5`
  - Urgency: `High`
  - Location: `Sector 4 Relief Camp`
  - Latitude: `13.0827`, Longitude: `80.2707`
- **Execution Steps**:
  1. Victim 1 logs in and submits relief request via POST `/requests/`.
  2. Verify database record created with `status="Pending"`, coordinates parsed to float.
  3. Victim 1 queries request activity audit via GET `/requests/<id>/history?format=json`.
  4. Victim 2 logs in and attempts to access Victim 1's request activity history.
- **Expected Outcome**: Request created successfully with coordinates; Victim 1 views chronological history; Victim 2 receives HTTP 403 Forbidden.
- **Actual Outcome**: ✅ Passed (Request persisted with coordinates; activity history tracked; role isolation verified).

---

### UAT-004: Coordinator Incident Lifecycle & Status Transitions
- **Test ID**: UAT-004
- **User Role**: Operations Coordinator
- **SRS References**: FR 3.2.1, FR 3.2.2, FR 3.2.3, FR 3.2.4
- **Objective**: Verify end-to-end incident logging, geographic visibility in affected areas, and progression through complete status lifecycle (`Open` → `In Progress` → `Resolved` → `Closed`) with audit trail tracking.
- **Preconditions**: Coordinator (`field.coord@example.com`) logged in.
- **Test Data**: Title: `Coastal Sea Surge`, Severity: `Critical`, Lat: `13.0450`, Lon: `80.2820`.
- **Execution Steps**:
  1. Coordinator POST `/incidents/` with incident payload.
  2. GET `/incidents/affected-areas` to verify listing.
  3. PATCH `/incidents/<id>/status` to `In Progress`.
  4. PATCH `/incidents/<id>/status` to `Resolved`.
  5. PATCH `/incidents/<id>/status` to `Closed`.
  6. GET `/incidents/<id>/history?format=json` to verify chronological audit logs.
- **Expected Outcome**: Incident created (HTTP 201); listed in affected areas; all status transitions succeed; activity history logs each state change and acting user.
- **Actual Outcome**: ✅ Passed (All status transitions recorded and validated; audit history complete).

---

### UAT-005: Warehouse Inventory Inward & Safety Thresholds
- **Test ID**: UAT-005
- **User Role**: Operations Coordinator
- **SRS References**: FR 3.4.1, FR 3.4.2
- **Objective**: Validate warehouse stock intake, safety threshold configuration, and rejection of invalid stock entries (e.g. negative quantities or unsupported categories).
- **Preconditions**: Logistics Coordinator logged in.
- **Test Data**: Category: `Food`, Quantity: `100`, Location: `Warehouse North`, Threshold: `20`.
- **Execution Steps**:
  1. POST `/inventory/` with valid category, positive quantity, and threshold.
  2. Query database to confirm stored item and attributes.
  3. POST `/inventory/` with negative quantity (`-10`).
- **Expected Outcome**: Valid inventory registered with HTTP 201; invalid negative stock rejected with HTTP 400 Bad Request.
- **Actual Outcome**: ✅ Passed (Stock persisted correctly; negative entry cleanly rejected).

---

### UAT-006: Atomic Resource Allocation & Idempotency Safeguards
- **Test ID**: UAT-006
- **User Role**: Operations Coordinator
- **SRS References**: FR 3.4.3, FR 3.5.1, FR 3.5.2
- **Objective**: Verify that allocating warehouse resources to a pending request atomically decrements stock, updates request status to `Assigned`, creates a volunteer dispatch task, and prevents duplicate allocations from double-decrementing stock.
- **Preconditions**: Pending request for 10 units `Water`; warehouse stock of 50 units; volunteer available.
- **Execution Steps**:
  1. Coordinator POST `/assignments/allocate` with request, volunteer, item, quantity 10.
  2. Verify warehouse stock decremented to 40; request status updated to `Assigned`; assignment created with status `Assigned`.
  3. Coordinator attempts repeated allocation for the same request.
- **Expected Outcome**: Allocation succeeds (HTTP 201); stock decrements from 50 to 40; duplicate allocation rejected (HTTP 400); warehouse stock remains exactly 40.
- **Actual Outcome**: ✅ Passed (Atomic decrement verified; idempotency protection prevented stock corruption).

---

### UAT-007: Volunteer Mission Execution & Request Auto-Fulfillment
- **Test ID**: UAT-007
- **User Role**: Field Volunteer / Citizen Recipient
- **SRS References**: FR 3.5.3, FR 3.5.4, FR 3.6.1
- **Objective**: Validate volunteer task execution workflow (`Assigned` → `In Progress` → `Completed`), automatic fulfillment of the underlying relief request, and dual in-app notifications to volunteer and victim.
- **Preconditions**: Task assigned to volunteer for victim's request.
- **Execution Steps**:
  1. Volunteer logs in and views assignments via GET `/assignments/`.
  2. Volunteer updates task status to `In Progress` (en route).
  3. Volunteer updates task status to `Completed` (delivered).
  4. Query database for relief request status and generated notifications.
- **Expected Outcome**: Task advances through statuses; upon completion, relief request automatically transitions to `Fulfilled`; in-app notifications delivered to both volunteer and victim.
- **Actual Outcome**: ✅ Passed (End-to-end task flow verified; request auto-fulfilled; notifications confirmed).

---

### UAT-008: Automated Critical Shortage Alerting & Deduplication
- **Test ID**: UAT-008
- **User Role**: Coordinator / System Administrator
- **SRS References**: FR 3.6.2
- **Objective**: Verify that depleting inventory below safety threshold when pending requests exist automatically generates critical shortage alerts to Coordinators/Admins, and subsequent operations do not flood the system with duplicate alerts.
- **Preconditions**: Inventory item with stock 20, threshold 10; pending request for same category; 0 prior alerts.
- **Execution Steps**:
  1. Deplete inventory stock by 12 (new stock = 8 <= threshold 10).
  2. Check notifications generated for Coordinators and Admins.
  3. Deplete stock further by 1 (stock = 7) without recovering above threshold.
  4. Verify notification count has not increased (duplicate suppression).
- **Expected Outcome**: Critical shortage alerts generated on threshold breach; deduplication logic prevents spam alerts while the shortage condition persists.
- **Actual Outcome**: ✅ Passed (Shortage alerts triggered; deduplication logic verified).

---

### UAT-009: Geospatial Disaster Map Visualization & Filtering
- **Test ID**: UAT-009
- **User Role**: Operations Coordinator
- **SRS References**: FR 3.8.1, FR 3.8.2
- **Objective**: Validate rendering of Leaflet operations map, loading of marker clustering assets, and querying of filtered geospatial marker datasets.
- **Preconditions**: Coordinator authenticated; active incidents and relief requests with coordinates present.
- **Execution Steps**:
  1. GET `/map/` and verify HTML contains Leaflet and MarkerCluster asset links.
  2. GET `/map/data` without parameters; verify default active requests and open incidents returned.
  3. GET `/map/data?category=Medical+Supplies`; verify filtered request markers.
- **Expected Outcome**: Map page renders (HTTP 200) with clustering support; map data API returns valid GeoJSON-compatible marker records with accurate coordinates.
- **Actual Outcome**: ✅ Passed (Map UI rendered; clustering script loaded; geospatial filter queries verified).

---

### UAT-010: Operational Analytics, Access Control & Admin CSV Export
- **Test ID**: UAT-010
- **User Role**: Operations Coordinator / System Administrator
- **SRS References**: FR 3.7.1, FR 3.7.2, FR 3.1.3
- **Objective**: Validate real-time operations dashboard metrics and verify that administrative CSV data exports (`/reports/export/requests` and `/reports/export/inventory`) are strictly restricted to Administrators.
- **Preconditions**: Coordinator and Administrator accounts available; relief requests and inventory data seeded.
- **Execution Steps**:
  1. Coordinator logs in and accesses `/dashboard/`.
  2. Coordinator attempts to export requests CSV and inventory CSV.
  3. Coordinator logs out; Administrator logs in.
  4. Administrator downloads requests CSV via GET `/reports/export/requests`.
  5. Administrator downloads inventory CSV via GET `/reports/export/inventory`.
- **Expected Outcome**: Dashboard displays analytics; Coordinator export attempts rejected with HTTP 403 Forbidden; Administrator exports succeed with HTTP 200, valid `text/csv` MIME type, attachment headers, and accurate column headers.
- **Actual Outcome**: ✅ Passed (Dashboard metrics rendered; non-admin exports blocked; admin CSV downloads validated).

---

## 3. Summary of UAT Execution Results

| Test ID | Scenario Name | Primary User Persona | SRS Requirements | Result |
|---|---|---|---|---|
| **UAT-001** | Public Citizen Registration, OTP & Login | Victim (Citizen) | FR 3.1.1, FR 3.1.2, FR 3.1.3 | ✅ PASS |
| **UAT-002** | Privileged Role Request & Admin Approval | Coordinator / Admin | FR 3.1.3, FR 3.1.4 | ✅ PASS |
| **UAT-003** | Relief Request Intake & Role Isolation | Victim (Citizen) | FR 3.3.1, FR 3.3.3, FR 3.3.4 | ✅ PASS |
| **UAT-004** | Incident Lifecycle & Affected Areas | Coordinator | FR 3.2.1, FR 3.2.2, FR 3.2.3, FR 3.2.4 | ✅ PASS |
| **UAT-005** | Warehouse Inventory Inward & Thresholds | Coordinator | FR 3.4.1, FR 3.4.2 | ✅ PASS |
| **UAT-006** | Atomic Allocation & Idempotency Safeguards | Coordinator | FR 3.4.3, FR 3.5.1, FR 3.5.2 | ✅ PASS |
| **UAT-007** | Volunteer Mission Execution & Auto-Fulfillment | Volunteer / Victim | FR 3.5.3, FR 3.5.4, FR 3.6.1 | ✅ PASS |
| **UAT-008** | Automated Critical Shortage Alerting | Coordinator / Admin | FR 3.6.2 | ✅ PASS |
| **UAT-009** | Geospatial Disaster Map & Clustering | Coordinator | FR 3.8.1, FR 3.8.2 | ✅ PASS |
| **UAT-010** | Dashboard Analytics & Admin CSV Export | Coordinator / Admin | FR 3.7.1, FR 3.7.2, FR 3.1.3 | ✅ PASS |
