from app.cooling import CoolingStatusEvaluator
from app.models import Component


def test_temperatures_endpoint_returns_full_race_distance(api):
    response = api.get_temperatures(2023, "spa", "RACE", "LEC")
    assert response.status_code == 200
    assert len(response.json()) == 45


def test_every_lap_reports_all_six_components(api):
    readings = api.get_temperatures(2023, "spa", "RACE", "LEC").json()
    expected_components = {c.value for c in Component}
    for lap in readings:
        assert set(lap["components"].keys()) == expected_components


def test_reported_status_matches_the_evaluator_for_every_reading(api):
    # Cross-check: the API's status field should always agree with running
    # the same temperature through CoolingStatusEvaluator directly.
    readings = api.get_temperatures(2023, "spa", "RACE", "LEC").json()
    for lap in readings:
        for component_name, reading in lap["components"].items():
            expected_status = CoolingStatusEvaluator.evaluate(
                Component(component_name), reading["temperature_celsius"]
            ).value
            assert reading["status"] == expected_status


def test_temperatures_endpoint_validates_driver_code(api):
    response = api.get_temperatures(2023, "spa", "RACE", "ZZZ")
    assert response.status_code == 404


def test_temperatures_endpoint_validates_year(api):
    response = api.get_temperatures(2099, "spa", "RACE", "LEC")
    assert response.status_code == 400
