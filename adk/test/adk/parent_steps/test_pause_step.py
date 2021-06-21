import unittest
from unittest import mock

import pytest

from adk.src.adk.parent_steps.pause_step import PauseStep


@pytest.mark.unit_test
class TestPauseStep(unittest.TestCase):

    @mock.patch('adk.src.adk.parent_steps.pause_step.PauseStep.get_input')
    def test_should_pause_if_true(self, mocked_input):
        PauseStep(pause_runtime=True).execute_step({})
        mocked_input.assert_called_once()

    @mock.patch('adk.src.adk.parent_steps.pause_step.PauseStep.get_input')
    def test_should_not_pause_if_false(self, mocked_input):
        PauseStep(pause_runtime=False).execute_step({})
        mocked_input.assert_not_called()

    def test_should_print_yaml(self):
        pause_yaml = PauseStep(pause_runtime=False).get_yaml()
        self.assertEqual('name: PauseStep\naction: aws:pause\ninputs: {}\n', pause_yaml)
