"""
Legacy ingest script retained for compatibility.

The app now uses direct file-based retrieval (no vector DB ingestion needed).
"""
import os
import sqlite3

DB_PATH = os.path.join("data", "tickets.db")


def main() -> None:
    if not os.path.exists(DB_PATH):
        print(f"Missing file: {DB_PATH}")
        return
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT COUNT(*) FROM tickets WHERE status = 'resolved'").fetchone()
    conn.close()
    count = int(rows[0]) if rows else 0
    print(f"Ticket data is ready: {count} resolved rows found in {DB_PATH}.")
    print("No ingestion step is required.")


if __name__ == "__main__":
    main()
