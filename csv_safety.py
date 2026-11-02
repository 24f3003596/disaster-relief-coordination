"""Helpers for producing spreadsheet-safe CSV downloads."""


def safe_csv_text(value):
    """Prefix potentially executable spreadsheet text with an apostrophe.

    Numeric values are deliberately left untouched. This protects untrusted
    text fields such as categories and locations from formula execution when
    CSV files are opened in spreadsheet applications.
    """
    if not isinstance(value, str) or not value:
        return value

    probe = value.lstrip(" \t\r\n")
    if probe.startswith(("=", "+", "-", "@", "\t", "\r")):
        return "'" + value
    return value
