import pytest


@pytest.mark.parametrize("year", [2000, 2030, 1999])
def test_out_of_range_year_returns_400(api, year):
    response = api.get_laps(year, "spa", "RACE", "LEC")
    assert response.status_code == 400


def test_unknown_driver_code_returns_404(api):
    response = api.get_laps(2023, "spa", "RACE", "ZZZ")
    assert response.status_code == 404


def test_invalid_session_type_returns_422(api):
    # session_type isn't one of PRACTICE/QUALIFYING/RACE - FastAPI/Pydantic
    # should reject it before it ever reaches our own validation code.
    response = api.raw_get(
        "/sessions/2023/spa/BANANA/laps", params={"driver_code": "LEC"}
    )
    assert response.status_code == 422


def test_missing_required_driver_code_returns_422(api):
    response = api.raw_get("/sessions/2023/spa/RACE/laps")
    assert response.status_code == 422


def test_invalid_compound_returns_422(api):
    response = api.raw_get(
        "/sessions/2023/spa/RACE/stint",
        params={"driver_code": "LEC", "compound": "SLICK"},
    )
    assert response.status_code == 422
