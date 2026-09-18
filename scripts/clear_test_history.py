"""
scripts/clear_test_history.py

Wipes all recorded test run history so you can start fresh.
Uses the same DATABASE_URL as record_test_run.py, so it's guaranteed
to target the same database your other scripts write to - no manual
pgAdmin/Neon UI guessing required.

Usage:
    set "DATABASE_URL=your_connection_string"
    python scripts/clear_test_history.py
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from qa_framework.test_history import TestHistoryStore


def main() -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL not set - aborting.")
        return

    store = TestHistoryStore(database_url)
    with store.engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE test_results, test_runs RESTART IDENTITY CASCADE"))

    print("Cleared all test run history. Next recorded run will be #1 again.")


if __name__ == "__main__":
    main()
