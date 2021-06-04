import unittest

import pytest

from documents.util.scripts.test.common_test_util import assert_having_all_not_empty_arguments_in_events

REQUIRED_ARGUMENTS = ['arg1', 'arg2', 'arg3']


def testing_lambda_method_positive(events: dict, context: dict):
    for argument in REQUIRED_ARGUMENTS:
        if not events.get(argument):
            raise KeyError()


def testing_lambda_method_negative_not_raises_all(events: dict, context: dict):
    pass


def testing_lambda_method_negative_not_raises_partially(events: dict, context: dict):
    if not events.get(REQUIRED_ARGUMENTS[0]):
        raise KeyError()


@pytest.mark.unit_test
class TestCommonTestUtil(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_assert_not_all_arguments_in_events_positive(self) -> None:
        assert_having_all_not_empty_arguments_in_events(KeyError, testing_lambda_method_positive, REQUIRED_ARGUMENTS)

    def test_assert_not_all_arguments_in_events_negative_not_raises(self) -> None:
        self.assertRaises(AssertionError,
                          assert_having_all_not_empty_arguments_in_events, KeyError,
                          testing_lambda_method_negative_not_raises_all, REQUIRED_ARGUMENTS)

    def test_assert_not_all_arguments_in_events_negative_not_raises_partially(self) -> None:
        self.assertRaises(AssertionError,
                          assert_having_all_not_empty_arguments_in_events, KeyError,
                          testing_lambda_method_negative_not_raises_partially,
                          [REQUIRED_ARGUMENTS[0], REQUIRED_ARGUMENTS[1]])
