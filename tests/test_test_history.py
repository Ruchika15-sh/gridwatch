import tempfile
from pathlib import Path

import pytest

from qa_framework.junit_parser import parse_junit_xml
from qa_framework.test_history import TestHistoryStore

SAMPLE_JUNIT_XML = """<?xml version="1.0" encoding="utf-8"?>
<testsuites>
  <testsuite name="pytest">
    <testcase classname="tests.test_drivers" name="test_a" time="0.01"></testcase>
    <testcase classname="tests.test_drivers" name="test_b" time="0.02">
      <failure message="assert failed">traceback...</failure>
    </testcase>
    <testcase classname="tests.test_drivers" name="test_c" time="0.00">
      <skipped message="not ready"></skipped>
    </testcase>
  </testsuite>
</testsuites>
"""


@pytest.fixture
def junit_file(tmp_path):
    path = tmp_path / "results.xml"
    path.write_text(SAMPLE_JUNIT_XML)
    return str(path)


@pytest.fixture
def store():
    """Fresh in-memory SQLite DB per test - same code as production Postgres."""
    return TestHistoryStore("sqlite:///:memory:")


def test_parse_junit_xml_extracts_all_three_outcomes(junit_file):
    results = parse_junit_xml(junit_file)
    outcomes = {r["test_name"]: r["outcome"] for r in results}

    assert outcomes["tests.test_drivers::test_a"] == "passed"
    assert outcomes["tests.test_drivers::test_b"] == "failed"
    assert outcomes["tests.test_drivers::test_c"] == "skipped"


def test_parse_junit_xml_extracts_durations(junit_file):
    results = parse_junit_xml(junit_file)
    durations = {r["test_name"]: r["duration_seconds"] for r in results}
    assert durations["tests.test_drivers::test_a"] == 0.01


def test_record_run_stores_correct_pass_fail_counts(store):
    results = [
        {"test_name": "test_a", "outcome": "passed", "duration_seconds": 0.1},
        {"test_name": "test_b", "outcome": "failed", "duration_seconds": 0.2},
        {"test_name": "test_c", "outcome": "passed", "duration_seconds": 0.05},
    ]
    run_id = store.record_run("abc1234", "3.11", results)

    runs = store.recent_runs()
    assert len(runs) == 1
    assert runs[0].id == run_id
    assert runs[0].total == 3
    assert runs[0].passed == 2
    assert runs[0].failed == 1


def test_recent_runs_orders_newest_first(store):
    store.record_run("commit1", "3.11", [{"test_name": "t", "outcome": "passed", "duration_seconds": 0.1}])
    store.record_run("commit2", "3.11", [{"test_name": "t", "outcome": "passed", "duration_seconds": 0.1}])

    runs = store.recent_runs()
    assert runs[0].git_commit == "commit2"
    assert runs[1].git_commit == "commit1"


def test_flaky_tests_detects_a_test_that_changed_outcome_across_runs(store):
    # test_stable passes every time; test_flaky flips between pass/fail
    store.record_run("c1", "3.11", [
        {"test_name": "test_stable", "outcome": "passed", "duration_seconds": 0.1},
        {"test_name": "test_flaky", "outcome": "passed", "duration_seconds": 0.1},
    ])
    store.record_run("c2", "3.11", [
        {"test_name": "test_stable", "outcome": "passed", "duration_seconds": 0.1},
        {"test_name": "test_flaky", "outcome": "failed", "duration_seconds": 0.1},
    ])

    flaky = store.flaky_tests(lookback_runs=10)
    flaky_names = {f["test_name"] for f in flaky}

    assert "test_flaky" in flaky_names
    assert "test_stable" not in flaky_names


def test_flaky_tests_respects_lookback_window(store):
    # An old flip should NOT count if it falls outside the lookback window
    store.record_run("old1", "3.11", [{"test_name": "t", "outcome": "passed", "duration_seconds": 0.1}])
    store.record_run("old2", "3.11", [{"test_name": "t", "outcome": "failed", "duration_seconds": 0.1}])
    store.record_run("recent1", "3.11", [{"test_name": "t", "outcome": "passed", "duration_seconds": 0.1}])
    store.record_run("recent2", "3.11", [{"test_name": "t", "outcome": "passed", "duration_seconds": 0.1}])

    flaky = store.flaky_tests(lookback_runs=2)  # only the two most recent runs
    assert flaky == []  # both recent runs passed - not flaky within this window


def test_flaky_tests_returns_empty_list_when_no_runs_exist(store):
    assert store.flaky_tests() == []
