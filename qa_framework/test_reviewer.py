"""
qa_framework/test_reviewer.py

Reviews AI-generated pytest code BEFORE it's trusted enough to merge.
Checks are grouped into the three categories QA teams actually use when
evaluating AI-generated output:

  - correctness:  is this even valid, runnable test code? Does every
                   test assert something real (not `assert True`)?
  - consistency:  does it follow this repo's conventions (uses the
                   shared `api` fixture / qa_framework client, rather
                   than reinventing raw HTTP calls)?
  - usefulness:   does it duplicate a test that already exists?

This never auto-merges anything — it produces a ReviewResult that a
human (or CI) decides what to do with. AI-generated tests are a
suggestion, not an authority.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
import tempfile
import uuid
from dataclasses import dataclass, field


@dataclass
class ReviewResult:
    accepted: bool
    correctness_issues: list[str] = field(default_factory=list)
    consistency_issues: list[str] = field(default_factory=list)
    usefulness_issues: list[str] = field(default_factory=list)

    @property
    def all_issues(self) -> list[str]:
        return self.correctness_issues + self.consistency_issues + self.usefulness_issues

    def summary(self) -> str:
        if self.accepted and not self.all_issues:
            return "ACCEPTED — no issues found"
        status = "ACCEPTED with warnings" if self.accepted else "REJECTED"
        lines = [status]
        for label, issues in (
            ("correctness", self.correctness_issues),
            ("consistency", self.consistency_issues),
            ("usefulness", self.usefulness_issues),
        ):
            for issue in issues:
                lines.append(f"  [{label}] {issue}")
        return "\n".join(lines)


class GeneratedTestReviewer:
    def __init__(self, existing_test_names: set[str] | None = None, tests_dir: str = "tests"):
        self.existing_test_names = existing_test_names or set()
        self.tests_dir = tests_dir

    def review(self, code: str) -> ReviewResult:
        result = ReviewResult(accepted=True)

        tree = self._parse(code, result)
        if tree is None:
            result.accepted = False
            return result

        test_funcs = [
            n for n in ast.walk(tree)
            if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")
        ]
        if not test_funcs:
            result.correctness_issues.append("No test_ functions found in generated code")
            result.accepted = False
            return result

        for func in test_funcs:
            self._check_correctness(func, result)
            self._check_consistency(func, result)
            self._check_usefulness(func, result)

        if result.correctness_issues:
            result.accepted = False

        if not self._collectable(code):
            result.correctness_issues.append("pytest could not collect the generated file")
            result.accepted = False

        return result

    def _parse(self, code: str, result: ReviewResult):
        try:
            return ast.parse(code)
        except SyntaxError as e:
            result.correctness_issues.append(f"Invalid Python syntax: {e}")
            return None

    def _check_correctness(self, func: ast.FunctionDef, result: ReviewResult) -> None:
        asserts = [n for n in ast.walk(func) if isinstance(n, ast.Assert)]
        if not asserts:
            result.correctness_issues.append(f"{func.name}: contains no assert statement")
        for a in asserts:
            if isinstance(a.test, ast.Constant):
                result.correctness_issues.append(f"{func.name}: trivial/always-true assertion")

    def _check_consistency(self, func: ast.FunctionDef, result: ReviewResult) -> None:
        arg_names = {a.arg for a in func.args.args}
        if "api" not in arg_names:
            result.consistency_issues.append(
                f"{func.name}: doesn't use the shared 'api' fixture "
                f"— may bypass qa_framework client conventions"
            )

    def _check_usefulness(self, func: ast.FunctionDef, result: ReviewResult) -> None:
        if func.name in self.existing_test_names:
            result.usefulness_issues.append(f"{func.name}: duplicate of an existing test name")

    def _collectable(self, code: str) -> bool:
        """Write the generated code into tests/ (so it can see conftest.py's
        fixtures) under a throwaway name, ask pytest to collect it, then
        delete it. Never left behind either way."""
        temp_name = f"test_ai_review_{uuid.uuid4().hex[:8]}.py"
        temp_path = os.path.join(self.tests_dir, temp_name)
        with open(temp_path, "w") as f:
            f.write(code)
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "--collect-only", "-q", temp_path],
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        finally:
            os.unlink(temp_path)
