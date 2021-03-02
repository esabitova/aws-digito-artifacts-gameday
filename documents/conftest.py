from pytest_bdd import (
    then,
    parsers
)


@then(parsers.parse('assert "{expected_property}" at "{step_key_for_expected}" '
                    'became equal to "{actual_property}" at "{step_key_for_actual}"'))
def assert_equal(ssm_test_cache, expected_property, step_key_for_expected, actual_property, step_key_for_actual):
    assert ssm_test_cache[step_key_for_expected][expected_property] \
           == ssm_test_cache[step_key_for_actual][actual_property]
