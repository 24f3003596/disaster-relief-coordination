# Disaster Relief Resource Coordination System — User Guide

**System Name**: Disaster Relief Resource Coordination System  
**Product Version**: 1.0.0  
**Target Audience**: Citizens, Emergency Responders, Logistics Coordinators, and System Administrators  
**Date**: November 2026  

---

## 1. System Overview

The **Disaster Relief Resource Coordination System** is a unified, real-time web platform designed to streamline disaster response, relief supply management, and volunteer coordination during humanitarian emergencies. The system connects affected citizens who urgently need life-essential aid with warehouse supply depots, field volunteers, and emergency coordination teams.

### Key Capabilities
- **Citizen Distress Portal**: Submit emergency requests for food, water, medical aid, blankets, and shelter with GPS coordinates.
- **Incident Command Management**: Report and track natural disasters, floodings, storms, and sea surges with severity indicators and affected area boundaries.
- **Warehouse Supply Oversight**: Monitor inventory levels across multiple depots, configure safety thresholds, and receive automatic critical shortage alerts.
- **Resource Allocation Engine**: Atomically match available warehouse supplies with validated victim requests and dispatch delivery tasks to field volunteers.
- **Volunteer Response Workflow**: Mobile-friendly task inbox for volunteers to accept missions, update transit status, and confirm delivery.
- **Geospatial Operations Map**: Interactive map visualization featuring marker clustering, viewport filtering, and category isolation.
- **Real-Time Analytics & CSV Export**: Operations dashboard calculating response times and inventory utilization rates with administrative data export capabilities.

---

## 2. Getting Started

### 2.1 System Access & Browser Requirements
The system is accessible via modern desktop and mobile browsers, including:
- Google Chrome (v100+)
- Mozilla Firefox (v100+)
- Apple Safari (v15+)
- Microsoft Edge (v100+)

### 2.2 Account Registration
1. Navigate to the system home page (`http://localhost:5000/` or public domain).
2. Click **"Register"** in the top navigation bar.
3. Fill in the required fields:
   - **Full Name**: Your legal name or community organization name.
   - **Mobile Phone**: 10-digit number formatted with country code (e.g. `+919876543210`).
   - **Email Address**: Valid email address for notifications and sign-in.
   - **Password**: Minimum 8 characters including mixed characters.
4. Click **"Register"**. Public registrations automatically receive the **Victim** role, granting immediate access to relief request submission.

### 2.3 Signing In
1. Click **"Login"** from the navigation bar.
2. Enter your registered email address and password.
3. Click **"Sign In"**. You will be directed to your role's primary operations dashboard.

---

## 3. Core Functional Workflows

### 3.1 Submitting a Relief Request (Citizen / Victim)
1. Log in to your account and click **"My Requests"** or **"Request Aid"**.
2. Select the resource category needed:
   - *Food*, *Water*, *Medical Supplies*, *Blankets & Shelter*, *Clothing*, *Sanitation & Hygiene*, or *Search & Rescue Equipment*.
3. Enter the requested **Quantity** (must be a positive integer).
4. Select the **Urgency Level**:
   - `Low`, `Medium`, `High`, or `Critical`.
5. Enter your delivery location description (e.g., `"Community Hall, 2nd Floor, Flood Relief Camp A"`).
6. Enter or capture your GPS **Latitude** and **Longitude** (e.g., `13.0827`, `80.2707`).
7. Click **"Submit Relief Request"**.
8. Your request enters the system with status `Pending`. You can view the request's real-time status and chronological activity history at any time.

### 3.2 Reporting & Tracking Disaster Incidents (Coordinator / Admin)
1. Coordinators click **"Incidents"** in the top navigation bar.
2. Click **"Report Incident"**.
3. Fill in the incident title, narrative description, severity level, and geographic coordinates.
4. Click **"Create Incident"**.
5. As response operations proceed, update the incident status:
   - `Open` → Initial reported incident awaiting assessment.
   - `In Progress` → Rescue and relief operations actively deployed.
   - `Resolved` → Active emergency mitigated; cleanup or secondary relief ongoing.
   - `Closed` → Incident fully concluded and archived.

### 3.3 Managing Warehouse Inventory (Coordinator / Admin)
1. Click **"Inventory"** to access the warehouse management dashboard.
2. To inward new supplies, enter:
   - Category name, quantity, storage depot location, and safety threshold.
3. The system continuously monitors stock against thresholds. If stock falls to or below the configured threshold while pending requests exist for that category, an automated **Critical Shortage** banner and notification will alert operational staff.

### 3.4 Allocating Resources & Dispatching Volunteers (Coordinator)
1. Click **"Assignments"** or navigate to a pending relief request.
2. Click **"Allocate Resources"**.
3. Choose the target request, available volunteer, and warehouse inventory item.
4. Confirm allocation quantity.
5. The system atomically decrements warehouse stock, updates request status to `Assigned`, and dispatches a delivery mission to the volunteer.

### 3.5 Executing Delivery Missions (Volunteer)
1. Log in to your Volunteer account and click **"My Assignments"**.
2. Review assigned missions with delivery locations and requested items.
3. When embarking on delivery, click **"Start Delivery"** (transitions task to `In Progress`).
4. Upon successful handover of aid to the citizen, click **"Mark Completed"**.
5. The task is finalized, the relief request transitions automatically to `Fulfilled`, and confirmation notifications are delivered.

### 3.6 Exploring the Geospatial Disaster Map (Coordinator / Admin)
1. Click **"Disaster Map"** in the navigation bar.
2. The map displays color-coded pins for active incidents and relief requests.
3. Use the filter controls to isolate:
   - Supply categories (e.g., only "Medical Supplies")
   - Operational statuses (e.g., only "Pending" or "In Progress")
   - Regional search terms.
4. Clusters group dense clusters of aid requests for visual clarity. Click on any cluster to zoom in to individual emergency pins.

### 3.7 Analytics & Administrative CSV Export (Admin)
1. Click **"Dashboard"** to view real-time operations metrics:
   - Total requests, category distributions, average fulfillment response times, and inventory utilization rates.
2. Administrators can click **"Export Relief Requests CSV"** or **"Export Inventory CSV"** to download full operational data for reporting and external compliance.

---

## 4. Troubleshooting & Error Scenarios

| Issue | Cause | Solution |
|---|---|---|
| **Login fails with "Account pending approval"** | User registered or was promoted to Coordinator/Admin. | Privileged accounts require Administrator approval. Contact your administrator to approve your account via the pending queue. |
| **"Insufficient stock for allocation"** | Requested allocation quantity exceeds available warehouse units. | Adjust allocation quantity to match available stock, or inward new supplies before allocating. |
| **"Invalid coordinates" error** | Coordinates outside valid ranges or only one coordinate provided. | Ensure latitude is between -90 and 90, longitude is between -180 and 180, and both values are entered. |
| **"403 Forbidden" on CSV export** | Non-administrator user attempting to download operational data. | CSV exports contain sensitive operational data and are strictly restricted to Administrators per system security policy. |
| **Map markers not clustering** | External CDN resource temporarily blocked by network firewall. | The map automatically falls back to standard individual markers; all data remains visible. |
