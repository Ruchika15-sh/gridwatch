from qa_framework.test_reviewer import GeneratedTestReviewer

GOOD_TEST = '''
def test_laps_include_expected_driver_code(api):
    laps = api.get_laps(2023, "spa", "RACE", "LEC").json()
    assert all(lap["driver_code"] == "LEC" for lap in laps)
'''

TRIVIAL_ASSERT_TEST = '''
def test_something(api):
    response = api.get_drivers()
    assert True
'''

NO_ASSERT_TEST = '''
def test_fetches_drivers(api):
    response = api.get_drivers()
    drivers = response.json()
'''

BROKEN_SYNTAX_TEST = '''
def test_broken(api)
    assert api.get_drivers().status_code == 200
'''

DOES_NOT_USE_FIXTURE_TEST = '''
from fastapi.testclient import TestClient
from app.main import app

def test_drivers_raw():
    client = TestClient(app)
    assert client.get("/drivers").status_code == 200
'''

NOT_A_TEST_AT_ALL = '''
def helper_function():
    return 42
'''


def test_a_well_formed_test_is_accepted_with_no_issues():
    reviewer = GeneratedTestReviewer()
    result = reviewer.review(GOOD_TEST)
    assert result.accepted
    assert result.all_issues == []


def test_trivial_always_true_assertion_is_rejected():
    reviewer = GeneratedTestReviewer()
    result = reviewer.review(TRIVIAL_ASSERT_TEST)
    assert not result.accepted
    assert any("trivial" in issue for issue in result.correctness_issues)


def test_a_test_with_no_assert_is_rejected():
    reviewer = GeneratedTestReviewer()
    result = reviewer.review(NO_ASSERT_TEST)
    assert not result.accepted
    assert any("no assert" in issue for issue in result.correctness_issues)


def test_broken_syntax_is_rejected_outright():
    reviewer = GeneratedTestReviewer()
    result = reviewer.review(BROKEN_SYNTAX_TEST)
    assert not result.accepted
    assert any("syntax" in issue.lower() for issue in result.correctness_issues)


def test_code_with_no_test_functions_is_rejected():
    reviewer = GeneratedTestReviewer()
    result = reviewer.review(NOT_A_TEST_AT_ALL)
    assert not result.accepted
    assert "No test_ functions found" in result.correctness_issues[0]


def test_test_that_bypasses_the_api_fixture_is_flagged_as_inconsistent():
    reviewer = GeneratedTestReviewer()
    result = reviewer.review(DOES_NOT_USE_FIXTURE_TEST)
    # Still accepted (it's not incorrect, just off-convention) but flagged.
    assert result.consistency_issues
    assert "api" in result.consistency_issues[0]


def test_duplicate_test_name_is_flagged_as_not_useful():
    reviewer = GeneratedTestReviewer(existing_test_names={"test_laps_include_expected_driver_code"})
    result = reviewer.review(GOOD_TEST)
    assert result.usefulness_issues
    assert "duplicate" in result.usefulness_issues[0]


def test_summary_reports_rejected_status_clearly():
    reviewer = GeneratedTestReviewer()
    result = reviewer.review(TRIVIAL_ASSERT_TEST)
    assert result.summary().startswith("REJECTED")
