"""SQLite database setup and simple bill operations."""

import sqlite3
from contextlib import closing

from config import DATABASE_NAME, STARTING_CHALLAN_NUMBER


def get_connection():
    """Open the database and enable dictionary-like rows and foreign keys."""
    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db():
    """Create the bills and bill_rows tables if they do not exist yet."""
    with closing(get_connection()) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS bills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                challan_no INTEGER NOT NULL UNIQUE,
                date TEXT NOT NULL,
                customer_name TEXT NOT NULL,
                vehicle_no TEXT NOT NULL,
                total REAL NOT NULL,
                balance REAL NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS bill_rows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bill_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                FOREIGN KEY (bill_id) REFERENCES bills (id) ON DELETE CASCADE
            );
            """
        )
        connection.commit()


def _next_challan_number(connection):
    """Find the next challan number using an already-open connection."""
    row = connection.execute("SELECT MAX(challan_no) AS last_number FROM bills").fetchone()
    if row["last_number"] is None:
        return STARTING_CHALLAN_NUMBER
    return row["last_number"] + 1


def get_next_challan_no():
    """Return the next number, starting at the configured challan number."""
    with closing(get_connection()) as connection:
        return _next_challan_number(connection)


def _insert_bill_rows(connection, bill_id, rows):
    """Save each description and amount belonging to a bill."""
    for row in rows:
        connection.execute(
            "INSERT INTO bill_rows (bill_id, description, amount) VALUES (?, ?, ?)",
            (bill_id, row["description"], row["amount"]),
        )


def save_bill(bill_data):
    """Save a bill dictionary and its rows; return its assigned challan number.

    The dictionary has date, customer_name, vehicle_no, total, balance, and
    optionally rows (a list of dictionaries with description and amount).
    """
    with closing(get_connection()) as connection:
        try:
            # Lock the database for this short transaction while choosing a number.
            connection.execute("BEGIN IMMEDIATE")
            challan_no = _next_challan_number(connection)
            cursor = connection.execute(
                """
                INSERT INTO bills (challan_no, date, customer_name, vehicle_no, total, balance)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    challan_no,
                    bill_data["date"],
                    bill_data["customer_name"],
                    bill_data["vehicle_no"],
                    bill_data["total"],
                    bill_data["balance"],
                ),
            )
            _insert_bill_rows(connection, cursor.lastrowid, bill_data.get("rows", []))
            connection.commit()
            return challan_no
        except Exception:
            connection.rollback()
            raise


def get_bill(challan_no):
    """Return one bill and its rows, or None if the challan number is unknown."""
    with closing(get_connection()) as connection:
        bill_row = connection.execute(
            "SELECT * FROM bills WHERE challan_no = ?", (challan_no,)
        ).fetchone()
        if bill_row is None:
            return None

        bill = dict(bill_row)
        rows = connection.execute(
            "SELECT * FROM bill_rows WHERE bill_id = ? ORDER BY id", (bill["id"],)
        ).fetchall()
        bill["rows"] = [dict(row) for row in rows]
        return bill


def update_bill(challan_no, bill_data):
    """Update a bill and replace its rows; return False if it was not found."""
    with closing(get_connection()) as connection:
        try:
            cursor = connection.execute(
                """
                UPDATE bills
                SET date = ?, customer_name = ?, vehicle_no = ?, total = ?, balance = ?
                WHERE challan_no = ?
                """,
                (
                    bill_data["date"],
                    bill_data["customer_name"],
                    bill_data["vehicle_no"],
                    bill_data["total"],
                    bill_data["balance"],
                    challan_no,
                ),
            )
            if cursor.rowcount == 0:
                connection.rollback()
                return False

            bill_row = connection.execute(
                "SELECT id FROM bills WHERE challan_no = ?", (challan_no,)
            ).fetchone()
            connection.execute("DELETE FROM bill_rows WHERE bill_id = ?", (bill_row["id"],))
            _insert_bill_rows(connection, bill_row["id"], bill_data.get("rows", []))
            connection.commit()
            return True
        except Exception:
            connection.rollback()
            raise


def _bill_list_item(row):
    """Turn a database bill row into a normal dictionary."""
    return dict(row)


def list_bills():
    """Return bill summaries, newest challan number first."""
    with closing(get_connection()) as connection:
        rows = connection.execute("SELECT * FROM bills ORDER BY challan_no DESC").fetchall()
        return [_bill_list_item(row) for row in rows]


def search_bills(query):
    """Find bills by a partial challan number or customer name."""
    search_text = f"%{query}%"
    with closing(get_connection()) as connection:
        rows = connection.execute(
            """
            SELECT * FROM bills
            WHERE CAST(challan_no AS TEXT) LIKE ? OR customer_name LIKE ?
            ORDER BY challan_no DESC
            """,
            (search_text, search_text),
        ).fetchall()
        return [_bill_list_item(row) for row in rows]


if __name__ == "__main__":
    # These imports are only needed by this temporary-database demo.
    import tempfile
    from pathlib import Path

    # These sample checks use a temporary database so the real bills stay untouched.
    original_database_name = DATABASE_NAME
    try:
        with tempfile.TemporaryDirectory() as temp_folder:
            DATABASE_NAME = str(Path(temp_folder) / "test_billing.db")
            init_db()

            sample_bill = {
                "date": "2026-10-03",
                "customer_name": "Test Customer",
                "vehicle_no": "MH-12-AB-1234",
                "total": 500,
                "balance": 100,
                "rows": [
                    {"description": "Transport charge", "amount": 300},
                    {"description": "Loading charge", "amount": 200},
                ],
            }

            assert get_next_challan_no() == STARTING_CHALLAN_NUMBER
            challan_no = save_bill(sample_bill)
            assert challan_no == STARTING_CHALLAN_NUMBER
            assert get_bill(challan_no)["customer_name"] == "Test Customer"
            assert len(get_bill(challan_no)["rows"]) == 2
            assert len(list_bills()) == 1
            assert search_bills("Test Customer")[0]["challan_no"] == challan_no
            assert search_bills(str(challan_no))[0]["customer_name"] == "Test Customer"
            assert get_next_challan_no() == STARTING_CHALLAN_NUMBER + 1

            sample_bill["customer_name"] = "Updated Customer"
            sample_bill["rows"] = [{"description": "Updated charge", "amount": 500}]
            assert update_bill(challan_no, sample_bill) is True
            assert get_bill(challan_no)["customer_name"] == "Updated Customer"
            assert len(get_bill(challan_no)["rows"]) == 1

        print("All database test calls passed.")
    finally:
        DATABASE_NAME = original_database_name
