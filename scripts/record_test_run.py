"""
scripts/record_test_run.py

Reads pytest's JUnit XML output and records it into the test history DB.
Meant to run right after `pytest --junitxml=test-results.xml` in CI.

Requires the DATABASE_URL environment variable (a Postgres connection
string, e.g. from Neon). If it's not set, this script skips recording
rather than failing the build - history tracking is a bonus, not a
requirement for tests to pass.

Usage:
    export DATABASE_URL=postgresql://user:pass@host/dbname
    python scripts/record_test_run.py test-results.xml
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from qa_framework.junit_parser import parse_junit_xml
from qa_framework.test_history import TestHistoryStore


def get_git_commit() -> str:
    try:
        full_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip()
        return full_sha[:8]
    except Exception:
        return "unknown"


def main() -> None:
    junit_path = sys.argv[1] if len(sys.argv) > 1 else "test-results.xml"
    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        print("DATABASE_URL not set - skipping test history recording.")
        return

    if not Path(junit_path).exists():
        print(f"No JUnit report found at {junit_path} - nothing to record.")
        return

    results = parse_junit_xml(junit_path)
    store = TestHistoryStore(database_url)
    run_id = store.record_run(
        git_commit=get_git_commit(),
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}",
        results=results,
    )
    passed = sum(1 for r in results if r["outcome"] == "passed")
    print(f"Recorded run #{run_id}: {passed}/{len(results)} passed")


if __name__ == "__main__":
    main()
