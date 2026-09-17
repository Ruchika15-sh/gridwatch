"""
qa_framework/junit_parser.py

Parses the JUnit XML that pytest produces (via --junitxml) into plain
dicts, so test run history can be recorded independently of how the
tests were actually executed.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET


def parse_junit_xml(path: str) -> list[dict]:
    tree = ET.parse(path)
    root = tree.getroot()
    results = []

    for testcase in root.iter("testcase"):
        classname = testcase.get("classname", "")
        name = testcase.get("name", "")
        full_name = f"{classname}::{name}" if classname else name
        duration = float(testcase.get("time", 0))

        if testcase.find("failure") is not None or testcase.find("error") is not None:
            outcome = "failed"
        elif testcase.find("skipped") is not None:
            outcome = "skipped"
        else:
            outcome = "passed"

        results.append(
            {"test_name": full_name, "outcome": outcome, "duration_seconds": duration}
        )

    return results
