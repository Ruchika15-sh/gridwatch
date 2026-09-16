"""
scripts/generate_and_review_tests.py

End-to-end AI-assisted test workflow:
  1. Scan tests/ for existing test names (so the AI doesn't duplicate them).
  2. Ask Claude to propose new tests for a given focus area.
  3. Run the proposal through GeneratedTestReviewer.
  4. If accepted, write it to tests/test_ai_proposed_<focus>.py for a
     HUMAN to review and commit — this never auto-merges.

Usage:
    export ANTHROPIC_API_KEY=your_key_here
    python scripts/generate_and_review_tests.py "the stint endpoint's edge cases"
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from qa_framework.ai_test_generator import generate_tests
from qa_framework.test_reviewer import GeneratedTestReviewer

TESTS_DIR = Path(__file__).resolve().parent.parent / "tests"


def collect_existing_test_names() -> set[str]:
    names: set[str] = set()
    for path in TESTS_DIR.glob("test_*.py"):
        tree = ast.parse(path.read_text())
        names.update(
            n.name for n in ast.walk(tree)
            if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")
        )
    return names


def main() -> None:
    focus_area = sys.argv[1] if len(sys.argv) > 1 else "general edge cases"
    existing = collect_existing_test_names()

    print(f"Generating tests for: {focus_area}")
    print(f"({len(existing)} existing test names known, will avoid duplicates)\n")

    generated_code = generate_tests(focus_area, existing)

    print("--- AI-generated code ---")
    print(generated_code)
    print("--- end generated code ---\n")

    reviewer = GeneratedTestReviewer(existing_test_names=existing, tests_dir=str(TESTS_DIR))
    result = reviewer.review(generated_code)

    print(result.summary())

    if not result.accepted:
        print("\nNot written to disk — fix the issues above or discard.")
        sys.exit(1)

    slug = re.sub(r"[^a-z0-9]+", "_", focus_area.lower()).strip("_")[:40]
    out_path = TESTS_DIR / f"test_ai_proposed_{slug}.py"
    out_path.write_text(generated_code)
    print(f"\nWritten to {out_path} — REVIEW BEFORE COMMITTING. Not auto-merged.")


if __name__ == "__main__":
    main()
