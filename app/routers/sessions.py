"""
app/routers/sessions.py

Endpoints for a race session: laps, standings, and tire stints.
Every route validates its inputs (year range, known driver code, known
compound) and returns a clean 4xx with a message on bad input, rather
than letting a bad value crash into a 500.
"""

from fastapi import APIRouter, HTTPException, Query

from app.mock_data import DRIVER_CODES, RaceDataGenerator
from app.models import SessionType, TireCompound

router = APIRouter(prefix="/sessions", tags=["sessions"])

MIN_YEAR, MAX_YEAR = 2018, 2025


def _validate_year(year: int) -> None:
    if not (MIN_YEAR <= year <= MAX_YEAR):
        raise HTTPException(status_code=400, detail=f"year must be between {MIN_YEAR} and {MAX_YEAR}")


def _validate_driver(driver_code: str) -> str:
    code = driver_code.strip().upper()
    if code not in DRIVER_CODES:
        raise HTTPException(status_code=404, detail=f"unknown driver code '{driver_code}'")
    return code


@router.get("/{year}/{race_name}/{session_type}/laps")
def get_laps(
    year: int,
    race_name: str,
    session_type: SessionType,
    driver_code: str = Query(..., description="3-letter driver code, e.g. LEC"),
):
    _validate_year(year)
    code = _validate_driver(driver_code)

    generator = RaceDataGenerator(year, race_name, session_type.value)
    laps = generator.generate_laps(code)
    return laps


@router.get("/{year}/{race_name}/{session_type}/stint")
def get_tire_stint(
    year: int,
    race_name: str,
    session_type: SessionType,
    driver_code: str = Query(...),
    compound: TireCompound = Query(...),
):
    _validate_year(year)
    code = _validate_driver(driver_code)

    generator = RaceDataGenerator(year, race_name, session_type.value)
    laps = generator.generate_laps(code)
    stint = [lap for lap in laps if lap.compound == compound]

    if not stint:
        raise HTTPException(
            status_code=404,
            detail=f"{code} did not run the {compound.value} compound in this session",
        )
    return stint


@router.get("/{year}/{race_name}/{session_type}/standings")
def get_standings(year: int, race_name: str, session_type: SessionType):
    _validate_year(year)
    generator = RaceDataGenerator(year, race_name, session_type.value)
    return generator.generate_standings()
