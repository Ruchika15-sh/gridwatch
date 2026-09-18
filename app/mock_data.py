"""
app/mock_data.py

A deterministic race data generator. Same (year, race_name, session_type)
always produces the same laps/standings — no real F1 API call, no
randomness leaking into test runs. This is what makes the whole test
suite reproducible in CI: every run sees identical data.

Design note: this is intentionally a small class hierarchy (not a pile of
free functions) so it's easy to extend later — e.g. add a
`WetRaceDataGenerator` subclass that overrides `_lap_time_for` to model
degraded wet-weather pace, without touching the base class.
"""

import hashlib
import random

from app.models import Driver, Lap, TireCompound

DRIVERS = [
    Driver(code="LEC", name="Charles Leclerc", team="Ferrari", number=16),
    Driver(code="VER", name="Max Verstappen", team="Red Bull", number=1),
    Driver(code="HAM", name="Lewis Hamilton", team="Mercedes", number=44),
    Driver(code="NOR", name="Lando Norris", team="McLaren", number=4),
    Driver(code="PIA", name="Oscar Piastri", team="McLaren", number=81),
    Driver(code="RUS", name="George Russell", team="Mercedes", number=63),
]

DRIVER_CODES = [d.code for d in DRIVERS]


class RaceDataGenerator:
    """Generates a deterministic set of laps for a given session key."""

    LAPS_PER_STINT = 15
    BASE_LAP_TIME = 90.0  # seconds

    def __init__(self, year: int, race_name: str, session_type: str):
        self.year = year
        self.race_name = race_name.lower()
        self.session_type = session_type
        self._seed = self._make_seed()

    def _make_seed(self) -> int:
        """Same inputs -> same seed -> same 'random' data, every time."""
        key = f"{self.year}-{self.race_name}-{self.session_type}"
        return int(hashlib.sha256(key.encode()).hexdigest(), 16) % (2**32)

    def generate_laps(self, driver_code: str, total_laps: int = 45) -> list[Lap]:
        rng = random.Random(self._seed + hash(driver_code) % 1000)
        laps: list[Lap] = []
        compounds = [TireCompound.SOFT, TireCompound.MEDIUM, TireCompound.HARD]
        stint_index = 0
        tyre_life = 0

        for lap_num in range(1, total_laps + 1):
            if tyre_life >= self.LAPS_PER_STINT and stint_index < len(compounds) - 1:
                stint_index += 1
                tyre_life = 0

            compound = compounds[stint_index]
            tyre_life += 1
            degradation = tyre_life * 0.05  # tires get slower as they age
            noise = rng.uniform(-0.3, 0.3)
            lap_time = self._lap_time_for(compound, degradation, noise)

            laps.append(
                Lap(
                    driver_code=driver_code,
                    lap_number=lap_num,
                    lap_time_seconds=round(lap_time, 3),
                    compound=compound,
                    tyre_life=tyre_life,
                    pit_out=(tyre_life == 1 and lap_num > 1),
                    pit_in=(tyre_life == self.LAPS_PER_STINT),
                )
            )
        return laps

    def _lap_time_for(self, compound: TireCompound, degradation: float, noise: float) -> float:
        compound_offset = {
            TireCompound.SOFT: -0.8,
            TireCompound.MEDIUM: 0.0,
            TireCompound.HARD: 0.6,
            TireCompound.INTERMEDIATE: 8.0,
            TireCompound.WET: 15.0,
        }[compound]
        return self.BASE_LAP_TIME + compound_offset + degradation + noise

    def generate_standings(self) -> list[dict]:
        rng = random.Random(self._seed)
        order = DRIVER_CODES.copy()
        rng.shuffle(order)
        points_table = [25, 18, 15, 12, 10, 8]
        return [
            {"driver_code": code, "position": i + 1, "points": points_table[i]}
            for i, code in enumerate(order)
        ]

    def generate_temperatures(self, driver_code: str, total_laps: int = 45) -> list[dict]:
        """Per-lap component temperature readings. Brakes swing widely lap
        to lap (heavy braking zones vs straights); engine and ERS are more
        stable but still vary enough to occasionally cross into WARNING."""
        rng = random.Random(self._seed + hash(driver_code) % 1000 + 777)
        brake_components = ["BRAKE_FL", "BRAKE_FR", "BRAKE_RL", "BRAKE_RR"]
        readings = []

        for lap_num in range(1, total_laps + 1):
            components = {}
            for name in brake_components:
                components[name] = round(380 + rng.uniform(-40, 240), 1)
            components["ENGINE"] = round(95 + rng.uniform(-8, 38), 1)
            components["ERS"] = round(40 + rng.uniform(-8, 32), 1)

            readings.append(
                {"lap_number": lap_num, "driver_code": driver_code, "components": components}
            )
        return readings
