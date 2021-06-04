import itertools
import unittest
from _ctypes_test import func
from typing import List


def assert_having_all_not_empty_arguments_in_events(exception_class,
                                                    testing_method: func, required_arguments: List[str]) -> None:
    """
    Assert that method raises an exception if:
    1) there are not enough keys in the events
    2) and if passed keys have not their values or they are "" in the events
    :param exception_class: expected exception
    :param testing_method: method to test for the exception
    :param required_arguments: list of all required arguments
    :return: None
    """
    tc = unittest.TestCase()
    for combinations_length in range(0, len(required_arguments)):
        for subset in itertools.combinations(required_arguments, combinations_length):
            # Test with not empty values of keys if keys are placed in the events
            events: dict = {}
            for key in subset:
                events[key] = "something"
            tc.assertRaises(exception_class, testing_method, events, None)

    tc.assertRaises(exception_class, testing_method, {a: "" for a in required_arguments}, None)
    tc.assertRaises(exception_class, testing_method, {a: None for a in required_arguments}, None)
