def test_list_drivers_returns_the_full_grid(api):
    response = api.get_drivers()
    assert response.status_code == 200
    assert len(response.json()) == 6


def test_every_driver_has_the_required_fields(api):
    drivers = api.get_drivers().json()
    for driver in drivers:
        assert set(driver.keys()) == {"code", "name", "team", "number"}
        assert len(driver["code"]) == 3
