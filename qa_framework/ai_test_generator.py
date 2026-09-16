"""
qa_framework/ai_test_generator.py

Asks an LLM to propose new pytest edge-case tests for GridWatch, using
qa_framework.client's real methods so the output matches this repo's
conventions. Requires ANTHROPIC_API_KEY to run.

This is only the "propose" half — nothing here is trusted until it has
also passed qa_framework.test_reviewer.GeneratedTestReviewer.
"""

from __future__ import annotations

import os

import anthropic

CLIENT_REFERENCE = '''
class GridWatchClient:
    def get_drivers(self): ...
    def get_laps(self, year: int, race_name: str, session_type: str, driver_code: str): ...
    def get_stint(self, year: int, race_name: str, session_type: str, driver_code: str, compound: str): ...
    def get_standings(self, year: int, race_name: str, session_type: str): ...
'''

EXAMPLE_TEST = '''
def test_laps_are_numbered_sequentially_with_no_gaps(api):
    laps = api.get_laps(2023, "spa", "RACE", "LEC").json()
    lap_numbers = [lap["lap_number"] for lap in laps]
    assert lap_numbers == list(range(1, 46))
'''


def generate_tests(focus_area: str, existing_test_names: set[str]) -> str:
    """Ask Claude for 3-5 new edge-case pytest tests for GridWatch.

    focus_area: plain-English description of what to target, e.g.
        "the /sessions/.../stint endpoint" or "boundary years".
    """
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    prompt = f"""You are writing pytest tests for a FastAPI service called GridWatch.

Tests use a shared `api` fixture (type: GridWatchClient) — every test
function's first parameter must be named `api`. Never construct a raw
TestClient yourself.

Available client methods:
{CLIENT_REFERENCE}

Example of an existing, correctly-styled test:
{EXAMPLE_TEST}

These test names already exist — do not repeat them:
{sorted(existing_test_names)}

Write 3-5 NEW pytest test functions focused on: {focus_area}.
Cover edge cases a happy-path test would miss (boundary values, unusual
but valid inputs, combinations not yet tested). Every test must contain
a real assertion — never `assert True` or an assertion with no
consequence. Return ONLY valid Python code, no explanation, no markdown
fences."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in response.content if block.type == "text")
