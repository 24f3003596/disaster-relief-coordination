
# Sprint 5 - CI, Deployment and Database Backup/Recovery

## 1. Project Overview

Project: Disaster Relief Coordination System

Framework: Flask

Database: SQLite

ORM: Flask-SQLAlchemy

Testing Framework: Pytest

CI Platform: GitHub Actions

Python Version: 3.13

## 2. Dependencies

Install the required dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the application:

```bash
python app.py
```

The Flask application runs on port 5000.

## 3. Environment Configuration

The application uses environment variables for sensitive and configurable settings.

| Variable | Description |
|---|---|
| SECRET_KEY | Flask session security key |
| DATABASE_URL | Database connection URI |
| OTP_TTL_MINUTES | OTP validity duration |
| OTP_DEMO_MODE | Controls OTP demo mode |

Create a local `.env` file using `.env.example` as a template.

Never commit `.env` or production secrets.

## 4. Database Configuration

Database engine: SQLite

Database file:

`instance/disaster_relief.db`

The application uses Flask-SQLAlchemy.

The database is configured through DATABASE_URL.

## 5. Automated CI Testing

GitHub Actions workflow:

`.github/workflows/ci.yml`

The workflow is triggered by:

- Pull requests targeting main.
- Pushes to main.
- Manual workflow dispatch.

CI execution steps:

1. Checkout repository.
2. Configure Python 3.13.
3. Install requirements.
4. Execute pytest.
5. Upload the JUnit test report.

Execute tests locally:

```bash
python -m pytest -v
```

## 6. Database Backup Procedure

Create the backup directory if necessary.

```powershell
New-Item -ItemType Directory -Force backups
```

Create a database backup:

```bash
python database_backup.py backup --source instance/disaster_relief.db --output backups/disaster_relief_backup.db
```

The backup utility:

- Checks the source database.
- Uses SQLite's online backup API.
- Creates a separate backup file.
- Validates backup integrity.
- Refuses to overwrite existing files.

## 7. Database Recovery Procedure

Create a separate restoration directory:

```powershell
New-Item -ItemType Directory -Force restore_test
```

Restore the backup into a separate database:

```bash
python database_backup.py restore --backup backups/disaster_relief_backup.db --output restore_test/restored_disaster_relief.db
```

The restoration procedure:

- Validates the backup.
- Creates a separate restored database.
- Checks restored database integrity.
- Does not overwrite an existing destination.
- Does not modify the original development database.

## 8. Backup and Recovery Verification

Run the automated backup tests:

```bash
python -m pytest -v tests/test_database_backup.py
```

The tests verify:

1. Successful backup creation.
2. Successful restoration.
3. Restored record consistency.
4. Original database preservation.
5. Prevention of accidental overwrite.
6. Handling of missing database files.

## 9. Security

- Environment secrets are not committed.
- `.env` is excluded through `.gitignore`.
- Database files are excluded from Git.
- Backup files are excluded from Git.
- Production secrets must be configured through the deployment platform.

## 10. Deployment Instructions

1. Clone the repository.
2. Install Python 3.13.
3. Install dependencies.
4. Configure environment variables.
5. Configure the database URI.
6. Ensure the SQLite instance directory exists.
7. Start the Flask application.

```bash
python -m pip install -r requirements.txt
python app.py
```

For production, use a production WSGI server and configure a strong SECRET_KEY.

## 11. Evidence

Attach the following evidence after verification:

- GitHub Actions successful workflow.
- Pull request CI check.
- Database backup creation output.
- Database restoration output.
- Restored database integrity check.
- Pytest backup and recovery test results.