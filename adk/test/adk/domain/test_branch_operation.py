import unittest

import pytest

from adk.src.adk.domain.branch_operation import Operation


@pytest.mark.unit_test
class TestBranchOperation(unittest.TestCase):

    def test_boolean_eq(self):
        self.assertTrue(Operation.BooleanEquals.value.evaluate(True, True))
        self.assertFalse(Operation.BooleanEquals.value.evaluate(True, False))

    def test_string_eq(self):
        self.assertTrue(Operation.StringEquals.value.evaluate("Foo", "Foo"))
        self.assertFalse(Operation.StringEquals.value.evaluate("Foo", "fOo"))

    def test_string_contains(self):
        self.assertTrue(Operation.Contains.value.evaluate("FooBar", "B"))
        self.assertFalse(Operation.Contains.value.evaluate("FooBar", "C"))

    def test_string_ends_with(self):
        self.assertTrue(Operation.EndsWith.value.evaluate("FooBar", "Bar"))
        self.assertFalse(Operation.EndsWith.value.evaluate("FooBar", "Foo"))

    def test_string_eq_ignore_case(self):
        self.assertTrue(Operation.EqualsIgnoreCase.value.evaluate("Foo", "fOo"))
        self.assertFalse(Operation.EqualsIgnoreCase.value.evaluate("Foo", "Bar"))

    def test_num_eq(self):
        self.assertTrue(Operation.NumericEquals.value.evaluate(5, 5))
        self.assertFalse(Operation.NumericEquals.value.evaluate(5, 6))

    def test_num_lesser(self):
        self.assertTrue(Operation.NumericLesser.value.evaluate(4, 5))
        self.assertFalse(Operation.NumericLesser.value.evaluate(5, 4))
        self.assertFalse(Operation.NumericLesser.value.evaluate(5, 5))

    def test_num_greater(self):
        self.assertTrue(Operation.NumericGreater.value.evaluate(5, 4))
        self.assertFalse(Operation.NumericGreater.value.evaluate(4, 5))
        self.assertFalse(Operation.NumericGreater.value.evaluate(5, 5))

    def test_num_lesser_eq(self):
        self.assertTrue(Operation.NumericLesserOrEquals.value.evaluate(4, 5))
        self.assertFalse(Operation.NumericLesserOrEquals.value.evaluate(5, 4))
        self.assertTrue(Operation.NumericLesserOrEquals.value.evaluate(5, 5))

    def test_num_greater_eq(self):
        self.assertTrue(Operation.NumericGreaterOrEquals.value.evaluate(5, 4))
        self.assertFalse(Operation.NumericGreaterOrEquals.value.evaluate(4, 5))
        self.assertTrue(Operation.NumericGreaterOrEquals.value.evaluate(5, 5))
