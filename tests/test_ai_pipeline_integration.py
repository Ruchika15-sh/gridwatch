from unittest.mock import patch

from qa_framework.test_reviewer import GeneratedTestReviewer

GENERATED_GOOD = '''
def test_stint_for_a_two_letter_code_is_rejected(api):
    response = api.get_stint(2023, "spa", "RACE", "LE", "SOFT")
    assert response.status_code == 404
'''

GENERATED_BAD = '''
def test_pointless(api):
    x = api.get_drivers()
    assert True
'''


@patch("qa_framework.ai_test_generator.generate_tests")
def test_pipeline_accepts_and_would_write_good_generated_code(mock_generate):
    mock_generate.return_value = GENERATED_GOOD

    from qa_framework.ai_test_generator import generate_tests

    code = generate_tests("stint endpoint edge cases", existing_test_names=set())
    reviewer = GeneratedTestReviewer()
    result = reviewer.review(code)

    assert result.accepted
    mock_generate.assert_called_once()


@patch("qa_framework.ai_test_generator.generate_tests")
def test_pipeline_rejects_bad_generated_code_before_it_reaches_disk(mock_generate):
    mock_generate.return_value = GENERATED_BAD

    from qa_framework.ai_test_generator import generate_tests

    code = generate_tests("anything", existing_test_names=set())
    reviewer = GeneratedTestReviewer()
    result = reviewer.review(code)

    assert not result.accepted
    assert any("trivial" in issue for issue in result.correctness_issues)
