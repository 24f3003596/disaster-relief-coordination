
import sqlite3

import pytest

from database_backup import (
    check_database_integrity,
    create_backup,
    restore_backup,
)


def create_sample_database(path):
    """Create a sample database for backup testing."""

    connection = sqlite3.connect(path)

    try:
        connection.execute("""
            CREATE TABLE relief_records (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                location TEXT NOT NULL
            )
        """)

        connection.executemany(
            """
            INSERT INTO relief_records (name, location)
            VALUES (?, ?)
            """,
            [
                ("Flood Relief", "Coimbatore"),
                ("Food Distribution", "Chennai"),
                ("Medical Support", "Madurai"),
            ]
        )

        connection.commit()

    finally:
        connection.close()


def read_records(path):
    connection = sqlite3.connect(path)

    try:
        return connection.execute(
            """
            SELECT id, name, location
            FROM relief_records
            ORDER BY id
            """
        ).fetchall()

    finally:
        connection.close()


def test_backup_and_restore(tmp_path):
    original = tmp_path / "original.db"
    backup = tmp_path / "backup.db"
    restored = tmp_path / "restored.db"

    create_sample_database(original)

    original_records = read_records(original)

    # Create backup
    create_backup(original, backup)

    assert backup.exists()
    assert check_database_integrity(backup)

    # Restore into a separate database
    restore_backup(backup, restored)

    assert restored.exists()
    assert check_database_integrity(restored)

    # Verify restored records
    restored_records = read_records(restored)

    assert restored_records == original_records

    # Confirm original database remains unchanged
    assert read_records(original) == original_records


def test_backup_does_not_overwrite_existing_destination(
    tmp_path
):
    original = tmp_path / "original.db"
    backup = tmp_path / "backup.db"

    create_sample_database(original)

    backup.write_text(
        "Existing backup must not be overwritten"
    )

    with pytest.raises(FileExistsError):
        create_backup(original, backup)

    assert backup.read_text() == (
        "Existing backup must not be overwritten"
    )


def test_restore_does_not_overwrite_existing_destination(
    tmp_path
):
    original = tmp_path / "original.db"
    backup = tmp_path / "backup.db"
    restored = tmp_path / "restored.db"

    create_sample_database(original)
    create_backup(original, backup)

    restored.write_text(
        "Existing database must remain unchanged"
    )

    with pytest.raises(FileExistsError):
        restore_backup(backup, restored)

    assert restored.read_text() == (
        "Existing database must remain unchanged"
    )


def test_backup_fails_when_source_is_missing(tmp_path):
    missing = tmp_path / "missing.db"
    backup = tmp_path / "backup.db"

    with pytest.raises(FileNotFoundError):
        create_backup(missing, backup)


def test_integrity_check_rejects_missing_database(tmp_path):
    missing = tmp_path / "missing.db"

    with pytest.raises(FileNotFoundError):
        check_database_integrity(missing)
