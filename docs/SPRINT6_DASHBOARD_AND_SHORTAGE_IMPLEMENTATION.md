# Sprint 6 Implementation — Dashboard Analytics, CSV Export and Critical-Shortage Notifications

## Scope

This implementation completes Vishal KV's two Sprint 6 tasks:

1. Dashboard Analytics and CSV Export (5 story points).
2. Automated Critical-Shortage Notifications (3 story points).

The supplied project already contained initial analytics, CSV exports and shortage detection from earlier sprint work. This update strengthens access control, CSV safety, transaction persistence, and shortage lifecycle handling instead of duplicating those features.

## 1. Dashboard Analytics and CSV Export

### Existing analytics retained

`dashboard.py` continues to provide:
- Request totals and grouped counts by status and category.
- Average response time from request creation to assignment.
- Average fulfillment time from request creation to assignment completion.
- Resource utilization using allocated units divided by available stock plus allocated units.
- Inventory, incident, volunteer and recent activity summaries.
- Safe zero values for empty datasets and zero capacity.

### Access control

The dashboard HTML page and JSON summary endpoints now both require an authenticated Coordinator or Admin. The dashboard's JSON response cannot bypass the same role restriction as the HTML view.

CSV download endpoints remain Admin-only:
- `/reports/export/relief-requests`
- `/reports/export/requests`
- `/reports/export/inventory`
- Dashboard aliases under `/dashboard/export/...`

### Export safety

A shared `csv_safety.py` helper prefixes untrusted spreadsheet text fields beginning with formula characters (`=`, `+`, `-`, `@`, tab or carriage return) with an apostrophe. Numeric values remain numeric. Export responses include `Cache-Control: no-store` and `X-Content-Type-Options: nosniff`.

## 2. Automated Critical-Shortage Notifications

### Trigger condition

A shortage alert is eligible when:
- Inventory for a category is at/below the configured category threshold, or at least one storage record is at/below its own threshold; and
- At least one matching relief request remains in `Pending` status.

Only active, phone-verified, approved Coordinators and Admins receive the operational shortage alert. Victims and Volunteers are excluded.

### Trigger points

The existing service-level integration is retained:
- Inventory item creation.
- Inventory stock changes.
- Resource allocation.
- Creation of a new pending relief request.
- Manual Coordinator/Admin shortage check.

### Persistence and transaction handling

The helper flushes generated notifications and state changes but does not commit independently. The calling inventory or request operation commits the notifications/state with its own operation. Allocation already commits after the shortage helper as part of its transaction.

This avoids notifications being lost when the request-scoped SQLAlchemy session is removed.

### Shortage lifecycle and deduplication

A new `InventoryShortageState` table tracks whether a category's shortage episode is active. Repeated checks do not create duplicate alerts during an unchanged shortage, even after a previous notification is read. When stock recovers above threshold or matching pending demand no longer exists, the episode is closed. A subsequent shortage can create a new alert.

The table is created by the application's existing `db.create_all()` startup path; no destructive schema change is introduced.

### Notification privacy

- The JSON notification list requires authentication and returns only the current user's notifications.
- Mark-as-read requires authentication and retains ownership validation.
- Broadcast requires an authenticated Coordinator or Admin.
- The HTML notifications page no longer exposes all users' notifications to anonymous visitors.

## 3. Regression coverage added or updated

`tests/test_sprint6_dashboard_shortage.py` adds checks for:
- Coordinator/Admin-only dashboard analytics.
- CSV formula-injection protection and download headers.
- Notification persistence after the session is reopened.
- Persistence after stock reduction.
- No duplicate alert after a notification is read while the shortage remains active.
- New alert after a genuine recovery and subsequent shortage.
- Exclusion of inactive, unverified/unapproved and non-operational recipients.
- Authentication and role restrictions for notification listing and broadcast.
- No private notification leakage on the anonymous HTML page.

`tests/test_dashboard.py` now authenticates the dashboard route test. The earlier shortage lifecycle test was updated to include actual stock recovery before testing a subsequent alert.

## 4. Verification

The following checks are run in the build workspace:
- Python source compilation.
- Jinja template parsing.
- JavaScript syntax validation where applicable.
- ZIP integrity validation.

The full pytest suite must be executed in the project's Python 3.14 environment. If the build environment does not have Flask and Flask-SQLAlchemy available and cannot download dependencies, runtime test status must be reported as blocked rather than passed.

Run locally:

```bash
python -m pip install -r requirements.txt
python -m pytest -v
```
