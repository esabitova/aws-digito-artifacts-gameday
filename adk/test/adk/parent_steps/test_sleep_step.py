import unittest
from unittest.mock import patch

import pytest

from adk.src.adk.parent_steps.sleep_step import SleepStep


@pytest.mark.unit_test
class TestSleepStep(unittest.TestCase):

    @patch('time.sleep', return_value=None)
    def test_should_pause_if_true(self, mocked_sleep):
        SleepStep(4).execute_step({})
        mocked_sleep.assert_called_once()

    def test_should_print_yaml(self):
        pause_yaml = SleepStep(4).get_yaml()
        self.assertEqual('name: SleepStep\n'
                         'action: aws:sleep\n'
                         'inputs:\n'
                         '  Duration: PT4S\n', pause_yaml)
