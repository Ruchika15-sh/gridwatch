"""
app/routers/sessions.py

Endpoints for a race session: laps, standings, and tire stints.
Every route validates its inputs (year range, known driver code, known
compound) and returns a clean 4xx with a message on bad input, rather
than letting a bad value crash into a 500.
"""

from fastapi import APIRouter, HTTPException, Query

from app.mock_data import RaceDataGenerator
from app.models import SessionType, TireCompound
from app.validation import validate_driver, validate_year

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("/{year}/{race_name}/{session_type}/laps")
def get_laps(
    year: int,
    race_name: str,
    session_type: SessionType,
    driver_code: str = Query(..., description="3-letter driver code, e.g. LEC"),
):
    validate_year(year)
    code = validate_driver(driver_code)

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
    validate_year(year)
    code = validate_driver(driver_code)

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
    validate_year(year)
    generator = RaceDataGenerator(year, race_name, session_type.value)
    return generator.generate_standings()
