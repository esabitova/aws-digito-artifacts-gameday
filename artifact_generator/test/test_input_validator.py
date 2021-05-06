import pytest
from artifact_generator.src.input_validator import InputValidator


@pytest.mark.unit_test
class TestInputValidator:
    allowed_values = ["REGION", "AZ", "HARDWARE", "SOFTWARE"]

    @pytest.mark.parametrize(
        "text",
        ["api-gw", "sqs", pytest.param("api_gw", marks=pytest.mark.xfail), pytest.param("Api", marks=pytest.mark.xfail)]
    )
    def test_validate_small_case_with_hyphens(self, text):
        assert InputValidator.validate_small_case_with_hyphens(text) == text

    @pytest.mark.parametrize(
        "text",
        ["my_test", "test", pytest.param("my-test", marks=pytest.mark.xfail),
         pytest.param("MyTest", marks=pytest.mark.xfail)]
    )
    def test_validate_small_case_with_underscore(self, text):
        assert InputValidator.validate_small_case_with_underscore(text) == text

    @pytest.mark.parametrize(
        "text",
        ["MyText", "mytext", pytest.param("mytext1", marks=pytest.mark.xfail),
         pytest.param("my_text", marks=pytest.mark.xfail)]
    )
    def test_validate_alpha(self, text):
        assert InputValidator.validate_alpha(text) == text

    @pytest.mark.parametrize(
        "text",
        ["yes", "no", pytest.param("Yes", marks=pytest.mark.xfail), pytest.param("none", marks=pytest.mark.xfail)]
    )
    def test_validate_boolean_inputs(self, text):
        assert InputValidator.validate_boolean_inputs(text) == text

    @pytest.mark.parametrize(
        "text",
        ["2021-05-05", pytest.param("05-05-2021", marks=pytest.mark.xfail),
         pytest.param("2021-13-31", marks=pytest.mark.xfail), pytest.param("2021-01-41", marks=pytest.mark.xfail)]
    )
    def test_validate_date_input(self, text):
        assert InputValidator.validate_date_input(text) == text

    @pytest.mark.parametrize(
        "text,allowed_values",
        [("REGION", allowed_values),
         pytest.param("INVALID", allowed_values, marks=pytest.mark.xfail)]
    )
    def test_validate_one_of(self, text, allowed_values):
        assert InputValidator.validate_one_of(text, allowed_values) == text

    @pytest.mark.parametrize(
        "text,allowed_values",
        [("SOFTWARE", allowed_values),
         ("AZ,SOFTWARE", allowed_values),
         pytest.param("SOFTWARE,INVALID", allowed_values, marks=pytest.mark.xfail),
         pytest.param("INVALID", allowed_values, marks=pytest.mark.xfail)]
    )
    def test_validate_one_or_more_of(self, text, allowed_values):
        InputValidator.validate_one_or_more_of(text, allowed_values)
