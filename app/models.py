"""
app/models.py

Pydantic models = the data contracts for GridWatch's API. FastAPI uses
these to validate every request/response automatically, and they double
as the source of truth an AI test-generator can read to understand what
"valid" data looks like.
"""

from enum import Enum
from pydantic import BaseModel, Field


class TireCompound(str, Enum):
    SOFT = "SOFT"
    MEDIUM = "MEDIUM"
    HARD = "HARD"
    INTERMEDIATE = "INTERMEDIATE"
    WET = "WET"


class SessionType(str, Enum):
    PRACTICE = "PRACTICE"
    QUALIFYING = "QUALIFYING"
    RACE = "RACE"


class Driver(BaseModel):
    code: str = Field(..., min_length=3, max_length=3, description="3-letter driver code, e.g. LEC")
    name: str
    team: str
    number: int = Field(..., ge=1, le=99)


class Lap(BaseModel):
    driver_code: str
    lap_number: int = Field(..., ge=1)
    lap_time_seconds: float = Field(..., gt=0)
    compound: TireCompound
    tyre_life: int = Field(..., ge=0, description="Laps completed on this tire set")
    pit_out: bool = False
    pit_in: bool = False


class Session(BaseModel):
    session_id: str
    year: int = Field(..., ge=2018, le=2025)
    race_name: str
    session_type: SessionType
    drivers: list[str]


class StandingsEntry(BaseModel):
    driver_code: str
    position: int = Field(..., ge=1)
    points: int = Field(..., ge=0)
