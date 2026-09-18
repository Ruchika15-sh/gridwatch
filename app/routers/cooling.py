"""
app/routers/cooling.py

Component temperature endpoint: returns per-lap brake/engine/ERS
temperatures, each annotated with a NORMAL/WARNING/CRITICAL status from
CoolingStatusEvaluator.
"""

from fastapi import APIRouter, Query

from app.cooling import CoolingStatusEvaluator
from app.mock_data import RaceDataGenerator
from app.models import Component, SessionType
from app.validation import validate_driver, validate_year

router = APIRouter(prefix="/sessions", tags=["cooling"])


@router.get("/{year}/{race_name}/{session_type}/temperatures")
def get_temperatures(
    year: int,
    race_name: str,
    session_type: SessionType,
    driver_code: str = Query(..., description="3-letter driver code, e.g. LEC"),
):
    validate_year(year)
    code = validate_driver(driver_code)

    generator = RaceDataGenerator(year, race_name, session_type.value)
    raw_readings = generator.generate_temperatures(code)

    response = []
    for lap in raw_readings:
        annotated = {}
        for component_name, temp in lap["components"].items():
            component = Component(component_name)
            status = CoolingStatusEvaluator.evaluate(component, temp)
            annotated[component_name] = {"temperature_celsius": temp, "status": status.value}
        response.append(
            {"lap_number": lap["lap_number"], "driver_code": lap["driver_code"], "components": annotated}
        )

    return response
