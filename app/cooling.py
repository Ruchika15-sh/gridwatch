"""
app/cooling.py

Threshold-based status evaluation for car component temperatures
(brakes, engine, ERS). Deliberately kept as plain Python with no
FastAPI/HTTP dependency, so it can be unit-tested directly - this is
where boundary value testing actually matters: what happens at EXACTLY
the threshold, not just comfortably above or below it.

Thresholds are loosely inspired by real F1 operating ranges but
simplified - this isn't meant to be physically accurate, just a
realistic-shaped system to test against.
"""

from app.models import Component, TemperatureStatus

# (warning_threshold, critical_threshold) in Celsius, per component.
# status is WARNING at >= warning_threshold, CRITICAL at >= critical_threshold.
THRESHOLDS: dict[Component, tuple[float, float]] = {
    Component.BRAKE_FL: (400.0, 600.0),
    Component.BRAKE_FR: (400.0, 600.0),
    Component.BRAKE_RL: (400.0, 600.0),
    Component.BRAKE_RR: (400.0, 600.0),
    Component.ENGINE: (110.0, 125.0),
    Component.ERS: (50.0, 65.0),
}


class CoolingStatusEvaluator:
    """Evaluates a single temperature reading against a component's
    warning/critical thresholds. Boundary semantics: a reading exactly
    AT a threshold counts as having reached that severity (>=, not >)."""

    @staticmethod
    def evaluate(component: Component, temperature_celsius: float) -> TemperatureStatus:
        warning_threshold, critical_threshold = THRESHOLDS[component]

        if temperature_celsius >= critical_threshold:
            return TemperatureStatus.CRITICAL
        if temperature_celsius >= warning_threshold:
            return TemperatureStatus.WARNING
        return TemperatureStatus.NORMAL
