"""
app/validation.py

Shared request validation for session-scoped endpoints (laps, stints,
standings, temperatures). Pulled out of sessions.py so new endpoints
(like cooling/temperatures) don't duplicate this logic.
"""

from fastapi import HTTPException

from app.mock_data import DRIVER_CODES

MIN_YEAR, MAX_YEAR = 2018, 2025


def validate_year(year: int) -> None:
    if not (MIN_YEAR <= year <= MAX_YEAR):
        raise HTTPException(status_code=400, detail=f"year must be between {MIN_YEAR} and {MAX_YEAR}")


def validate_driver(driver_code: str) -> str:
    code = driver_code.strip().upper()
    if code not in DRIVER_CODES:
        raise HTTPException(status_code=404, detail=f"unknown driver code '{driver_code}'")
    return code
