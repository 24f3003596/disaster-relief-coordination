
import os
import sqlite3
import tempfile
from pathlib import Path
from contextlib import closing


def check_database_integrity(database_path):
    """
    Check whether a SQLite database exists and is healthy.

    Returns:
        True: Database is valid.
        False: Database is corrupted or invalid.

    Raises:
        FileNotFoundError: If the database does not exist.
    """

    database_path = Path(database_path)

    if not database_path.is_file():
        raise FileNotFoundError(
            f"Database not found: {database_path}"
        )

    try:
        database_uri = (
            database_path.resolve().as_uri() + "?mode=ro"
        )

        with closing(
            sqlite3.connect(database_uri, uri=True)
        ) as connection:

            result = connection.execute(
                "PRAGMA integrity_check"
            ).fetchone()

            return result is not None and result[0] == "ok"

    except sqlite3.DatabaseError:
        return False


def _copy_database(source_path, destination_path):
    """
    Copy a SQLite database using SQLite's backup API.

    Uses a temporary file and an atomic hard link.
    Existing destination files are never overwritten.
    """

    source_path = Path(source_path)
    destination_path = Path(destination_path)

    if not source_path.is_file():
        raise FileNotFoundError(
            f"Source database not found: {source_path}"
        )

    if source_path.resolve() == destination_path.resolve():
        raise ValueError(
            "Source and destination must be different files."
        )

    if destination_path.exists():
        raise FileExistsError(
            f"Destination already exists: {destination_path}"
        )

    destination_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = None

    try:
        # Create temporary file in the destination directory.
        with tempfile.NamedTemporaryFile(
            prefix="sqlite_backup_",
            suffix=".tmp",
            dir=destination_path.parent,
            delete=False,
        ) as temporary_file:

            temporary_path = Path(temporary_file.name)

        # IMPORTANT:
        # Explicitly close both SQLite connections.
        # This prevents Windows file-locking errors.
        with closing(
            sqlite3.connect(str(source_path))
        ) as source_connection:

            with closing(
                sqlite3.connect(str(temporary_path))
            ) as destination_connection:

                source_connection.backup(
                    destination_connection
                )

        # Connections are now closed.
        # Verify the temporary database.
        if not check_database_integrity(temporary_path):
            raise sqlite3.DatabaseError(
                "Copied database failed integrity check."
            )

        # Atomic hard link.
        # Raises FileExistsError if destination already exists.
        os.link(
            str(temporary_path),
            str(destination_path),
        )

    finally:
        # Both SQLite connections must be closed before cleanup.
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def create_backup(source_path, backup_path):
    """
    Create a backup of an existing SQLite database.

    Original database remains unchanged.
    Existing backup files are never overwritten.
    """

    source_path = Path(source_path)
    backup_path = Path(backup_path)

    if not source_path.is_file():
        raise FileNotFoundError(
            f"Source database not found: {source_path}"
        )

    if not check_database_integrity(source_path):
        raise sqlite3.DatabaseError(
            "Cannot back up an invalid database."
        )

    _copy_database(
        source_path,
        backup_path,
    )

    if not check_database_integrity(backup_path):
        raise sqlite3.DatabaseError(
            "Backup integrity verification failed."
        )

    return backup_path


def restore_backup(backup_path, destination_path):
    """
    Restore a SQLite database from an existing backup.

    Backup remains unchanged.
    Existing destination files are never overwritten.
    """

    backup_path = Path(backup_path)
    destination_path = Path(destination_path)

    if not backup_path.is_file():
        raise FileNotFoundError(
            f"Backup file not found: {backup_path}"
        )

    if not check_database_integrity(backup_path):
        raise sqlite3.DatabaseError(
            "Cannot restore an invalid backup."
        )

    _copy_database(
        backup_path,
        destination_path,
    )

    if not check_database_integrity(destination_path):
        raise sqlite3.DatabaseError(
            "Restored database integrity verification failed."
        )

    return destination_path
