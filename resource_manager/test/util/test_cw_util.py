import unittest
import pytest
from unittest.mock import MagicMock, call
import resource_manager.src.util.cw_util as cw_utils


CW_ALARM_NAME = 'alarm_name'
CW_OK_STATE = 'OK'
CW_ALARM_STATE = 'ALARM'


def describe_alarms_side_effect(state):
    return {
        'MetricAlarms': [{'StateValue': state}]
    }


@pytest.mark.unit_test
class TestCWUtil(unittest.TestCase):

    def setUp(self):
        self.session_mock = MagicMock()
        self.mock_cw_service = MagicMock()
        self.client_side_effect_map = {
            'cloudwatch': self.mock_cw_service,

        }
        self.session_mock.client.side_effect = lambda service_name, config=None:\
            self.client_side_effect_map.get(service_name)

    def tearDown(self):
        pass

    def test_get_metric_alarm_state(self):
        self.mock_cw_service.describe_alarms.return_value = describe_alarms_side_effect(CW_OK_STATE)
        response = cw_utils.get_metric_alarm_state(self.session_mock, CW_ALARM_NAME)
        self.mock_cw_service.describe_alarms.assert_called_once_with(AlarmNames=[CW_ALARM_NAME])
        self.assertEqual(CW_OK_STATE, response)

    def test_get_metric_alarm_state_missing_alarm(self):
        self.mock_cw_service.describe_alarms.return_value = {'MetricAlarms': []}
        self.assertRaises(Exception, cw_utils.get_metric_alarm_state, self.session_mock, CW_ALARM_NAME)

    def test_wait_for_metric_alarm_state(self):
        self.mock_cw_service.describe_alarms.side_effect = [
            describe_alarms_side_effect(CW_OK_STATE),
            describe_alarms_side_effect(CW_OK_STATE),
            describe_alarms_side_effect(CW_ALARM_STATE),
        ]
        response = cw_utils.wait_for_metric_alarm_state(self.session_mock, CW_ALARM_NAME, CW_ALARM_STATE, 100)
        self.assertEqual(True, response)
        self.mock_cw_service.describe_alarms.assert_has_calls([
            call(AlarmNames=[CW_ALARM_NAME]),
            call(AlarmNames=[CW_ALARM_NAME]),
            call(AlarmNames=[CW_ALARM_NAME]),
        ])

    def test_wait_for_metric_alarm_state_timeout(self):
        self.mock_cw_service.describe_alarms.side_effect = [
            describe_alarms_side_effect(CW_OK_STATE),
            describe_alarms_side_effect(CW_OK_STATE),
            describe_alarms_side_effect(CW_ALARM_STATE),
        ]
        self.assertRaises(Exception, cw_utils.wait_for_metric_alarm_state, self.session_mock, CW_ALARM_NAME,
                          CW_ALARM_STATE, 5)

    def test_wait_for_metric_alarm_state_missing_alarm(self):
        self.mock_cw_service.describe_alarms.side_effect = [
            {'MetricAlarms': []},
            {'MetricAlarms': []},
            {'MetricAlarms': []},
        ]
        self.assertRaises(Exception, cw_utils.wait_for_metric_alarm_state, self.session_mock, CW_ALARM_NAME,
                          CW_ALARM_STATE, 100)
