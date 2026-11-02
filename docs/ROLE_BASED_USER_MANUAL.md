# Role-Based Operational User Manual

**Project**: Disaster Relief Resource Coordination System (Team 20)  
**Document Version**: 1.0.0  
**Date**: November 2026  

---

## 1. System Role Hierarchy & Permissions Matrix

The Disaster Relief Resource Coordination System implements strict Role-Based Access Control (RBAC) to enforce operational boundaries, protect victim privacy, and preserve data integrity during disaster operations.

```
+---------------------------------------------------------------------------------------+
|                                  SYSTEM ADMINISTRATOR                                 |
|  - Account Approvals & Promotions   - Security Audits        - System CSV Data Export |
+---------------------------------------------------------------------------------------+
                                           |
+---------------------------------------------------------------------------------------+
|                                OPERATIONS COORDINATOR                                 |
|  - Incident Logging & Lifecycle     - Warehouse Inventory    - Resource Allocation    |
|  - Disaster Map Operations          - Shortage Triage        - Volunteer Dispatch     |
+---------------------------------------------------------------------------------------+
                      |                                                 |
+-------------------------------------------+     +-------------------------------------+
|              FIELD VOLUNTEER              |     |          AFFECTED CITIZEN           |
|  - Mission Task Inbox                     |     |  - Emergency Relief Requests        |
|  - Delivery Updates (Assigned->Completed) |     |  - GPS Coordinate Pinning           |
|  - Fulfillment Confirmations              |     |  - Personal Status & History        |
+-------------------------------------------+     +-------------------------------------+
```

### RBAC Operational Permission Matrix

| Capability / Endpoint | Admin | Coordinator | Volunteer | Victim |
|---|:---:|:---:|:---:|:---:|
| **Public Registration & Phone OTP Verification** | ✅ | ✅ | ✅ | ✅ |
| **Submit Emergency Relief Request** | ✅ | ✅ | ❌ | ✅ |
| **View Own Relief Requests & Activity History** | ✅ | ✅ | ❌ | ✅ |
| **View All Relief Requests (Operational Intake)**| ✅ | ✅ | ❌ | ❌ |
| **Log & Transition Disaster Incidents** | ✅ | ✅ | ❌ | ❌ |
| **Register & Inward Warehouse Inventory** | ✅ | ✅ | ❌ | ❌ |
| **Allocate Supplies & Dispatch Volunteers** | ✅ | ✅ | ❌ | ❌ |
| **View Assigned Tasks & Mark In Progress/Complete** | ✅ | ✅ | ✅ | ❌ |
| **Receive In-App Delivery & Shortage Alerts** | ✅ | ✅ | ✅ | ✅ |
| **Interactive Disaster Map & Geospatial Filters** | ✅ | ✅ | ❌ | ❌ |
| **Operations Analytics Dashboard** | ✅ | ✅ | ❌ | ❌ |
| **Export Relief Request & Inventory CSV Files** | ✅ | ❌ | ❌ | ❌ |
| **Review & Approve Privileged Account Queue** | ✅ | ❌ | ❌ | ❌ |
| **Execute Database Backup & Recovery Utility** | ✅ | ❌ | ❌ | ❌ |

---

## 2. System Administrator Operations Manual

### 2.1 Role Responsibilities
Administrators govern user accounts, authorize privileged operational roles, monitor system audit trails, maintain data backups, and extract CSV analytical datasets.

### 2.2 Key Operational Procedures

#### Procedure A: Managing the Privileged Role Approval Queue
1. Log in with your Administrator credentials.
2. Navigate to **Administration → Pending Approvals** (`/auth/admin/pending-approvals`).
3. The queue displays all users who registered or were nominated for **Coordinator** or **Admin** roles.
4. For each applicant, review their name, email, verified phone number, and requested role.
5. Click **"Approve"** to activate the operational account, or **"Reject"** with an optional rejection reason.
6. The user is notified immediately; approved accounts can log in straight away.

#### Procedure B: Exporting System Datasets via CSV
1. Navigate to **Reports → Data Export** (`/dashboard/`).
2. Click **"Export Requests (CSV)"** to download the comprehensive relief request ledger (`/reports/export/requests`).
3. Click **"Export Inventory (CSV)"** to download the current warehouse stock and threshold ledger (`/reports/export/inventory`).
4. Files are formatted with standard RFC 4180 CSV headers and timestamps.

#### Procedure C: Database Backup & Integrity Check
1. On the operational host, run the backup utility:
   ```powershell
   python database_backup.py backup --source instance/disaster_relief.db --dest backups/relief_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').db
   ```
2. Verify backup file integrity:
   ```powershell
   python database_backup.py check --database backups/relief_backup_20261102.db
   ```

---

## 3. Operations Coordinator Operations Manual

### 3.1 Role Responsibilities
Coordinators form the tactical core of disaster operations: assessing incoming incidents, monitoring supply depots, preventing critical shortages, and dispatching volunteers.

### 3.2 Key Operational Procedures

#### Procedure A: Logging & Managing Disaster Incidents
1. Navigate to **Incidents → New Incident** (`/incidents/`).
2. Enter the title, location description, latitude, longitude, and severity (`Low`, `Medium`, `High`, `Critical`).
3. As field assessments update:
   - Transition to `In Progress` when emergency response units deploy.
   - Transition to `Resolved` once active hazards are mitigated.
   - Transition to `Closed` when recovery operations conclude.
4. Review chronological event history via **"View Activity History"**.

#### Procedure B: Managing Depots & Responding to Critical Shortages
1. Navigate to **Inventory** (`/inventory/`).
2. View current stock levels, storage depot locations, and thresholds.
3. When supplies arrive from donors or government depots, click **"Add Inventory"** with category, quantity, and safety threshold.
4. If a **"CRITICAL SHORTAGE"** alert appears:
   - Check the affected category and pending request volume.
   - Initiate emergency replenishment or reallocate surplus supplies from secondary depots.

#### Procedure C: Allocating Resources to Citizen Requests
1. Navigate to **Assignments → Allocate** (`/assignments/`).
2. Select the validated citizen request.
3. Select an available approved Volunteer.
4. Select the warehouse item batch.
5. Enter the quantity to allocate (cannot exceed warehouse stock).
6. Click **"Confirm Allocation"**.
7. The system updates stock, marks request as `Assigned`, and dispatches the task.

#### Procedure D: Geospatial Map Operations
1. Navigate to **Disaster Map** (`/map/`).
2. Pan and zoom across the disaster zone.
3. Toggle category filters to visualize specific relief needs (e.g., Medical Aid vs. Food & Water).
4. Inspect clusters to identify high-density distress areas requiring field coordination camps.

---

## 4. Field Volunteer Operations Manual

### 4.1 Role Responsibilities
Volunteers operate on the ground: picking up allocated supplies from warehouse depots, transporting them across affected zones, and delivering them safely to citizens.

### 4.2 Key Operational Procedures

#### Procedure A: Reviewing Assigned Missions
1. Log in with your Volunteer account.
2. Navigate to **My Tasks** (`/assignments/`).
3. Your active assignments display:
   - Task ID, Item category, Allocated quantity.
   - Citizen delivery address and geographic coordinates.
   - Recipient contact information and special delivery notes.

#### Procedure B: Updating Mission Progress & Completing Delivery
1. When collecting supplies from the warehouse depot and embarking on delivery, click **"Start Delivery"**.
   - Status updates to `In Progress` ("En Route").
2. When handing over supplies directly to the citizen at the relief location, click **"Confirm Delivery"**.
   - Status updates to `Completed`.
3. The system automatically marks the citizen's relief request as `Fulfilled` and issues confirmation notifications.

---

## 5. Affected Citizen / Victim Operations Manual

### 5.1 Role Responsibilities
Citizens use the portal during emergencies to request life-saving supplies, track relief progress, and receive arrival updates without operational complexity.

### 5.2 Key Operational Procedures

#### Procedure A: Registering During an Emergency
1. Visit the portal homepage and click **"Register"**.
2. Provide your name, contact phone number, email, and a password (8+ characters).
3. Public accounts are immediately activated with the **Victim** role.

#### Procedure B: Submitting an Emergency Relief Request
1. Click **"Request Relief Aid"** (`/requests/`).
2. Select what you need: *Food*, *Water*, *Medical Supplies*, *Blankets & Shelter*, etc.
3. Enter the number of people or quantity needed.
4. Select how urgently aid is needed (`Low`, `Medium`, `High`, `Critical`).
5. Enter your current shelter address or landmark description.
6. Provide GPS coordinates or click the location detection prompt on your mobile browser.
7. Click **"Submit Request"**.

#### Procedure C: Tracking Relief Status
1. Navigate to **My Requests** (`/requests/`).
2. View your active requests and their current real-time status:
   - `Pending`: Request received and queued for review.
   - `Assigned`: Supplies allocated at depot; volunteer dispatched.
   - `In Progress`: Volunteer is en route with your supplies.
   - `Fulfilled`: Supplies delivered to your location.
3. Click **"Activity History"** to see timestamped progress updates.
