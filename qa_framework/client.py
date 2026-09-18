"""
qa_framework/client.py

A Service Object wrapping GridWatch's API. Tests call methods like
`api.get_laps(...)` instead of building raw URLs and query strings —
this is the "Object-Oriented automation framework" piece: one place to
update if an endpoint's path changes, and tests stay readable.
"""

from fastapi.testclient import TestClient

from app.main import app


class GridWatchClient:
    """Thin, typed wrapper around GridWatch's HTTP API for use in tests."""

    def __init__(self, client: TestClient | None = None):
        self._client = client or TestClient(app)

    def get_drivers(self):
        return self._client.get("/drivers")

    def get_laps(self, year: int, race_name: str, session_type: str, driver_code: str):
        return self._client.get(
            f"/sessions/{year}/{race_name}/{session_type}/laps",
            params={"driver_code": driver_code},
        )

    def get_stint(self, year: int, race_name: str, session_type: str, driver_code: str, compound: str):
        return self._client.get(
            f"/sessions/{year}/{race_name}/{session_type}/stint",
            params={"driver_code": driver_code, "compound": compound},
        )

    def get_standings(self, year: int, race_name: str, session_type: str):
        return self._client.get(f"/sessions/{year}/{race_name}/{session_type}/standings")

    def get_temperatures(self, year: int, race_name: str, session_type: str, driver_code: str):
        return self._client.get(
            f"/sessions/{year}/{race_name}/{session_type}/temperatures",
            params={"driver_code": driver_code},
        )

    def raw_get(self, path: str, **kwargs):
        """Escape hatch for tests that need to hit a malformed/unusual path directly."""
        return self._client.get(path, **kwargs)
