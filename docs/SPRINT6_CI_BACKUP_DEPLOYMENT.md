# Sprint 6 – CI, Database Backup/Recovery and Deployment Readiness

## 1. Runtime and application configuration

- Application: Flask + Flask-SQLAlchemy
- Database: SQLite for the current repository configuration
- Supported CI/runtime baseline: Python 3.13
- Dependencies: `requirements.txt`
- Test framework: pytest

Create a virtual environment and install dependencies:

```bash
python -m venv .venv
# Windows PowerShell
.venv\\Scripts\\Activate.ps1
# macOS/Linux
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set a unique random `SECRET_KEY`.
The application loads `.env` through python-dotenv. Never commit `.env`,
production secrets, database files, or backup files.

| Variable | Purpose | Example |
|---|---|---|
| `APP_ENV` | Runtime environment; production requires a configured secret | `development` |
| `SECRET_KEY` | Flask session signing key | generate a long random value |
| `DATABASE_URL` | SQLAlchemy database URI | `sqlite:///disaster_relief.db` |
| `OTP_TTL_MINUTES` | OTP validity in minutes | `5` |
| `OTP_DEMO_MODE` | Enables demo OTP display; keep off in production | `0` |

With Flask-SQLAlchemy, `sqlite:///disaster_relief.db` is relative to Flask's
instance directory, so the default file is `instance/disaster_relief.db`.
Do not prefix the URI with `instance/` a second time.

## 2. Continuous Integration

The existing workflow at `.github/workflows/ci.yml` is the repository's
single CI workflow. It runs on pull requests targeting `main`, pushes to
`main`, `feature/**`, and `sprint/**`, and manual dispatch.

It uses Python 3.13, installs `requirements.txt`, validates Python syntax,
runs the complete pytest suite, and uploads a JUnit XML report even when
tests fail. A failed test or validation step makes the GitHub Actions check
fail; successful jobs appear as passing checks on the pull request.

Run the same checks locally:

```bash
python -m compileall -q .
python -m pytest -v --tb=short
```

### Verify with a feature-branch pull request

1. Create a feature branch: `git switch -c feature/sprint6-ci-backup`.
2. Commit the CI and documentation changes and push the branch.
3. Open a pull request from that branch into `main`.
4. Wait for **Python CI - Automated Tests** to finish.
5. Open the check details and confirm syntax validation and pytest pass.
6. Confirm the `pytest-results-<run number>` artifact is available.
7. Merge only after review and required checks pass.

Do not add secrets to workflow YAML. CI uses non-production test-only
environment values and the test fixture uses a temporary SQLite database.

## 3. Database backup

The live development database is expected at `instance/disaster_relief.db`
when using the example SQLite URI. Confirm the actual `DATABASE_URL` and
database path before running these commands. Stop application writes or
schedule a quiet maintenance window for a consistent operational backup.

PowerShell:

```powershell
New-Item -ItemType Directory -Force backups
python database_backup.py backup --source instance/disaster_relief.db --output backups/disaster_relief_YYYYMMDD.db
```

Use a real date in place of `YYYYMMDD`. The utility uses SQLite's online
backup API, verifies `PRAGMA integrity_check`, and refuses to overwrite an
existing destination. Keep backup files outside version control and store
production backups in an access-controlled, encrypted backup location.

## 4. Restore into a separate test database

Never restore over the live development database. Use a new destination:

```powershell
New-Item -ItemType Directory -Force restore_test
python database_backup.py restore --backup backups/disaster_relief_YYYYMMDD.db --output restore_test/restored_disaster_relief.db
```

Verify integrity and compare record counts/content with the backup/source.
For a quick SQLite integrity check:

```bash
python -c "import sqlite3; c=sqlite3.connect('restore_test/restored_disaster_relief.db'); print(c.execute('PRAGMA integrity_check').fetchone()[0]); c.close()"
```

The restore command creates a new file and refuses to overwrite an existing
destination. The original development database is not modified. For an
application-level comparison, open the original and restored copies read-only
and compare table names and row counts before declaring recovery verified.

## 5. Backup utility tests

```bash
python -m pytest -v tests/test_database_backup.py
```

The tests cover backup creation, restore, restored-record equality,
source preservation, missing source handling, integrity checking, and
protection against overwriting existing files.

## 6. Deployment readiness checklist

- [ ] Python 3.13 runtime selected.
- [ ] Dependencies installed from `requirements.txt`.
- [ ] `APP_ENV=production` configured.
- [ ] Strong unique `SECRET_KEY` configured in hosting environment.
- [ ] `DATABASE_URL` points to the intended persistent database.
- [ ] `OTP_DEMO_MODE=0` in production.
- [ ] No `.env`, credentials, database, or backup files committed.
- [ ] Persistent storage and backup retention configured for SQLite.
- [ ] Backup created and integrity checked.
- [ ] Restore tested to a separate destination and records compared.
- [ ] CI passing on a feature-branch pull request.
- [ ] Production deployment uses a production WSGI server (for example,
      Gunicorn on Linux) rather than Flask's development server.
- [ ] Deployment and recovery steps reviewed by the team.

The current repository is SQLite-based. If the hosting platform does not
provide persistent disk storage, configure a managed database and update
`DATABASE_URL` accordingly before deployment. The SQLite backup utility
does not back up PostgreSQL/MySQL databases.

## 7. Evidence to attach to Sprint 6

Capture the GitHub Actions passing run and pull-request check, downloaded
JUnit artifact, backup command output, restore command output, integrity
check output (`ok`), record comparison, and the completed deployment
readiness checklist. Do not claim successful remote CI or a production
restore until those actions have actually been run.
