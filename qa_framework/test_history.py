"""
qa_framework/test_history.py

Stores test run history in a relational database. Built on SQLAlchemy
specifically so the SAME code can run against:
  - an in-memory SQLite DB (used by the test suite below - fast, free,
    no external service needed to prove this logic works)
  - a real Postgres database (Neon, or any Postgres URL) in production,
    via the DATABASE_URL environment variable.

This is what powers the dashboard's trend/flaky-test views.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()


class TestRun(Base):
    __test__ = False  # not a pytest test class, just named similarly
    __tablename__ = "test_runs"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=lambda: dt.datetime.now(dt.timezone.utc))
    git_commit = Column(String(40))
    python_version = Column(String(10))
    total = Column(Integer)
    passed = Column(Integer)
    failed = Column(Integer)

    results = relationship("TestResult", back_populates="run", cascade="all, delete-orphan")


class TestResult(Base):
    __test__ = False  # not a pytest test class, just named similarly
    __tablename__ = "test_results"

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("test_runs.id"))
    test_name = Column(String(255))
    outcome = Column(String(10))  # passed / failed / skipped
    duration_seconds = Column(Float)

    run = relationship("TestRun", back_populates="results")


class TestHistoryStore:
    __test__ = False  # tells pytest this isn't a test class despite the name

    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def record_run(self, git_commit: str, python_version: str, results: list[dict]) -> int:
        session = self.Session()
        try:
            passed = sum(1 for r in results if r["outcome"] == "passed")
            failed = sum(1 for r in results if r["outcome"] == "failed")

            run = TestRun(
                git_commit=git_commit,
                python_version=python_version,
                total=len(results),
                passed=passed,
                failed=failed,
            )
            session.add(run)
            session.flush()  # populate run.id before we attach results

            for r in results:
                session.add(
                    TestResult(
                        run_id=run.id,
                        test_name=r["test_name"],
                        outcome=r["outcome"],
                        duration_seconds=r["duration_seconds"],
                    )
                )
            session.commit()
            return run.id
        finally:
            session.close()

    def recent_runs(self, limit: int = 20) -> list[TestRun]:
        session = self.Session()
        try:
            return (
                session.query(TestRun)
                .order_by(TestRun.timestamp.desc())
                .limit(limit)
                .all()
            )
        finally:
            session.close()

    def flaky_tests(self, lookback_runs: int = 10) -> list[dict]:
        """Tests whose outcome differed across the last N runs (i.e. they
        passed sometimes and failed other times with no code change in
        between) - the classic definition of a flaky test."""
        session = self.Session()
        try:
            recent_run_ids = [
                r.id
                for r in session.query(TestRun.id)
                .order_by(TestRun.timestamp.desc())
                .limit(lookback_runs)
            ]
            if not recent_run_ids:
                return []

            results = (
                session.query(TestResult)
                .filter(TestResult.run_id.in_(recent_run_ids))
                .all()
            )

            outcomes_by_test: dict[str, set[str]] = {}
            for r in results:
                outcomes_by_test.setdefault(r.test_name, set()).add(r.outcome)

            return [
                {"test_name": name, "outcomes_seen": sorted(outcomes)}
                for name, outcomes in outcomes_by_test.items()
                if len(outcomes) > 1
            ]
        finally:
            session.close()
