def test_stint_only_contains_the_requested_compound(api):
    response = api.get_stint(2023, "spa", "RACE", "LEC", "SOFT")
    assert response.status_code == 200
    stint = response.json()
    assert stint  # not empty
    assert all(lap["compound"] == "SOFT" for lap in stint)


def test_lap_times_get_slower_across_a_stint_due_to_degradation(api):
    stint = api.get_stint(2023, "spa", "RACE", "LEC", "SOFT").json()
    midpoint = len(stint) // 2
    first_half_avg = sum(l["lap_time_seconds"] for l in stint[:midpoint]) / midpoint
    second_half_avg = sum(l["lap_time_seconds"] for l in stint[midpoint:]) / (len(stint) - midpoint)
    assert second_half_avg > first_half_avg


def test_requesting_an_unused_compound_returns_404_not_empty_200(api):
    # LEC never runs WET tires in a dry mock race - should be a clear 404,
    # not a silently empty 200 that a UI might mistake for "no data yet".
    response = api.get_stint(2023, "spa", "RACE", "LEC", "WET")
    assert response.status_code == 404
