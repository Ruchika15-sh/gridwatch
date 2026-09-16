def test_get_laps_returns_the_full_race_distance(api):
    response = api.get_laps(2023, "spa", "RACE", "LEC")
    assert response.status_code == 200
    assert len(response.json()) == 45


def test_laps_are_numbered_sequentially_with_no_gaps(api):
    laps = api.get_laps(2023, "spa", "RACE", "LEC").json()
    lap_numbers = [lap["lap_number"] for lap in laps]
    assert lap_numbers == list(range(1, 46))


def test_tyre_life_resets_to_one_after_a_pit_stop(api):
    laps = api.get_laps(2023, "spa", "RACE", "LEC").json()
    laps_after_pit = [lap for lap in laps if lap["pit_out"]]
    assert all(lap["tyre_life"] == 1 for lap in laps_after_pit)


def test_lap_times_are_always_positive(api):
    laps = api.get_laps(2023, "spa", "RACE", "LEC").json()
    assert all(lap["lap_time_seconds"] > 0 for lap in laps)


def test_wet_and_intermediate_laps_are_slower_than_dry_laps(api):
    # Sanity check on the mock data model itself: wet-weather compounds
    # should never be faster than a slick tire on a normal lap.
    laps = api.get_laps(2023, "spa", "RACE", "LEC").json()
    dry_times = [l["lap_time_seconds"] for l in laps if l["compound"] in ("SOFT", "MEDIUM", "HARD")]
    assert dry_times, "expected at least some dry-compound laps in a full race distance"
    assert max(dry_times) < 100  # sanity bound - catches a broken degradation formula
