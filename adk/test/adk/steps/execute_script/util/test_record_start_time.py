import unittest
from unittest.mock import patch

import pytest
import datetime

from adk.src.adk.steps.execute_script.util.record_start_time import RecordStartTime


@pytest.mark.unit_test
class TestRecordStartTime(unittest.TestCase):

    @patch('adk.src.adk.steps.execute_script.util.record_start_time.get_current_time')
    def test_should_record_start(self, mocked_time):
        mocked_time.return_value = datetime.datetime.fromisoformat("2021-06-20T06:38:10")
        response = RecordStartTime().execute_step({})
        self.assertEqual({'Payload': '2021-06-20T06:38:10'}, response)

    def test_should_print_yaml(self):
        output_yaml = RecordStartTime().get_yaml()
        self.assertEqual(
            'description: Start the timer when SOP starts\n'
            'name: RecordStartTime\n'
            'action: aws:executeScript\n'
            'inputs:\n'
            '  Runtime: python3.6\n'
            '  Handler: script_handler\n'
            '  Script: |\n'
            '    from datetime import datetime, timezone\n'
            '\n'
            '    def script_handler(params: dict, context):\n'
            '        return get_current_time().isoformat()\n'
            '\n'
            '    def get_current_time():\n'
            '        return datetime.now(timezone.utc)\n'
            '  InputPayload: {}\n'
            'outputs:\n'
            '- Name: StartTime\n'
            '  Selector: $.Payload\n'
            '  Type: String\n', output_yaml)
