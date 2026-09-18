"""
tests/test_cooling_evaluator.py

Boundary value testing: for each threshold, we check three points -
just below it (should NOT trigger), exactly at it (SHOULD trigger,
since our evaluator uses >=), and just above it (still triggered).
This is the classic QA technique for anything threshold-based, and the
most common thing an interviewer will ask you to demonstrate.
"""

import pytest

from app.cooling import THRESHOLDS, CoolingStatusEvaluator
from app.models import Component, TemperatureStatus


@pytest.mark.parametrize("component", list(Component))
def test_just_below_warning_threshold_is_normal(component):
    warning, _ = THRESHOLDS[component]
    status = CoolingStatusEvaluator.evaluate(component, warning - 0.1)
    assert status == TemperatureStatus.NORMAL


@pytest.mark.parametrize("component", list(Component))
def test_exactly_at_warning_threshold_is_warning(component):
    warning, _ = THRESHOLDS[component]
    status = CoolingStatusEvaluator.evaluate(component, warning)
    assert status == TemperatureStatus.WARNING


@pytest.mark.parametrize("component", list(Component))
def test_just_above_warning_threshold_is_still_warning(component):
    warning, _ = THRESHOLDS[component]
    status = CoolingStatusEvaluator.evaluate(component, warning + 0.1)
    assert status == TemperatureStatus.WARNING


@pytest.mark.parametrize("component", list(Component))
def test_just_below_critical_threshold_is_still_warning(component):
    _, critical = THRESHOLDS[component]
    status = CoolingStatusEvaluator.evaluate(component, critical - 0.1)
    assert status == TemperatureStatus.WARNING


@pytest.mark.parametrize("component", list(Component))
def test_exactly_at_critical_threshold_is_critical(component):
    _, critical = THRESHOLDS[component]
    status = CoolingStatusEvaluator.evaluate(component, critical)
    assert status == TemperatureStatus.CRITICAL


@pytest.mark.parametrize("component", list(Component))
def test_well_above_critical_threshold_is_still_critical(component):
    _, critical = THRESHOLDS[component]
    status = CoolingStatusEvaluator.evaluate(component, critical + 500)
    assert status == TemperatureStatus.CRITICAL


def test_absolute_zero_is_normal_for_every_component():
    # Sanity/extreme-value check: nothing should misbehave at a physically
    # extreme low temperature.
    for component in Component:
        assert CoolingStatusEvaluator.evaluate(component, -273.15) == TemperatureStatus.NORMAL
