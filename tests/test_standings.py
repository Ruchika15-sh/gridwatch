def test_standings_include_every_driver_with_unique_positions(api):
    standings = api.get_standings(2023, "spa", "RACE").json()
    positions = [entry["position"] for entry in standings]
    assert len(standings) == 6
    assert positions == sorted(positions)
    assert len(set(positions)) == len(positions)  # no duplicate positions


def test_points_never_increase_as_position_gets_worse(api):
    standings = api.get_standings(2023, "spa", "RACE").json()
    points = [entry["points"] for entry in standings]
    assert points == sorted(points, reverse=True)
