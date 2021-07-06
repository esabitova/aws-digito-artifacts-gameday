import unittest
from unittest.mock import patch
from datetime import datetime

import pytest

from adk.src.adk.steps.execute_script.util.output_recovery_time import OutputRecoveryTime


@pytest.mark.unit_test
class TestOutputRecoveryTime(unittest.TestCase):

    @patch('adk.src.adk.steps.execute_script.util.output_recovery_time.get_current_time')
    def test_should_record_start(self, mocked_time):
        mocked_time.return_value = datetime.fromisoformat("2021-06-20T06:38:13")
        response = OutputRecoveryTime().execute_step({'StartTime': '2021-06-20T06:38:10'})
        self.assertEqual({'Payload': 3}, response)

    def test_should_print_yaml(self):
        output_yaml = OutputRecoveryTime().get_yaml()
        self.assertEqual(
            'description: Record the runtime in seconds\n'
            'name: OutputRecoveryTime\n'
            'action: aws:executeScript\n'
            'inputs:\n'
            '  Runtime: python3.6\n'
            '  Handler: script_handler\n'
            '  Script: |\n'
            '    from datetime import datetime, timezone\n'
            '    from dateutil import parser\n'
            '\n'
            '    def script_handler(params: dict, context):\n'
            '        return (get_current_time() - parser.parse(params[\'StartTime\'])).seconds\n'
            '\n'
            '    def get_current_time():\n'
            '        return datetime.now(timezone.utc)\n'
            '  InputPayload:\n'
            '    StartTime: \'{{ RecordStartTime.StartTime }}\'\n'
            'outputs:\n'
            '- Name: RecoveryTime\n'
            '  Selector: $.Payload\n'
            '  Type: Integer\n', output_yaml)
