def test_the_same_query_returns_identical_data_every_time(api):
    first = api.get_laps(2023, "monza", "QUALIFYING", "VER").json()
    second = api.get_laps(2023, "monza", "QUALIFYING", "VER").json()
    assert first == second


def test_different_years_produce_different_data(api):
    laps_2022 = api.get_laps(2022, "monza", "RACE", "HAM").json()
    laps_2023 = api.get_laps(2023, "monza", "RACE", "HAM").json()
    assert laps_2022 != laps_2023


def test_different_drivers_in_the_same_session_get_different_laps(api):
    lec_laps = api.get_laps(2023, "spa", "RACE", "LEC").json()
    ver_laps = api.get_laps(2023, "spa", "RACE", "VER").json()
    assert lec_laps != ver_laps
