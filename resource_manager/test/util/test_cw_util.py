from resource_manager.src.util.enums.alarm_state import AlarmState
import unittest
import pytest
from unittest.mock import MagicMock, call
import resource_manager.src.util.cw_util as cw_utils
import resource_manager.src.util.boto3_client_factory as client_factory
from datetime import datetime
from resource_manager.src.util.enums.operator import Operator


CW_ALARM_NAME = 'alarm_name'
CW_OK_STATE = AlarmState.OK.name
CW_ALARM_STATE = AlarmState.ALARM.name

metric_name = 'test_metric_name'
metric_namespace = 'test_metric_namespace'
start_time_utc = datetime.now()
end_time_utc = datetime.now()
time_out_secs = 5
sleep_time_sec = 1
dimensions = {'TestKey': 'TestValue'}


def get_metric_statistics_calls(calls_number) -> []:
    calls = []
    for x in range(calls_number):
        calls.append(call(Namespace=metric_namespace,
                          MetricName=metric_name,
                          Dimensions=[{'Name': 'TestKey', 'Value': 'TestValue'}],
                          StartTime=start_time_utc,
                          EndTime=end_time_utc,
                          Period=60,
                          Statistics=["Maximum"],
                          Unit='Percent'))
    return calls


def describe_alarms_side_effect(state):
    return {
        'MetricAlarms': [{'StateValue': state}],
        'ResponseMetadata': {
            'HTTPStatusCode': 200
        }
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
        # Clean client factory cache after each test.
        client_factory.clients = {}
        client_factory.resources = {}

    def test_get_metric_alarm_state(self):
        self.mock_cw_service.describe_alarms.return_value = describe_alarms_side_effect(CW_OK_STATE)
        response = cw_utils.get_metric_alarm_state(self.session_mock, CW_ALARM_NAME)
        self.mock_cw_service.describe_alarms.assert_called_once_with(AlarmNames=[CW_ALARM_NAME])
        self.assertEqual(AlarmState.OK, response)

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

    def test_wait_for_metric_data_point_timeout_fail(self):
        self.mock_cw_service.get_metric_statistics.side_effect = [
            {'Datapoints': [{'Maximum': '1'}]},
            {'Datapoints': [{'Maximum': '5'}]},
            {'Datapoints': [{'Maximum': '7'}]},
            {'Datapoints': [{'Maximum': '6'}]},
            {'Datapoints': [{'Maximum': '5'}]},
            {'Datapoints': [{'Maximum': '7'}]},
        ]
        expected_datapoint = 60
        operator = Operator.MORE_OR_EQUAL
        self.assertRaises(Exception, cw_utils.wait_for_metric_data_point,
                          session=self.session_mock,
                          datapoint_threshold=expected_datapoint,
                          name=metric_name,
                          start_time_utc=start_time_utc,
                          end_time_utc=end_time_utc,
                          namespace=metric_namespace,
                          operator=operator,
                          time_out_secs=time_out_secs,
                          sleep_time_sec=sleep_time_sec,
                          dimensions=dimensions)
        self.mock_cw_service.get_metric_statistics.assert_has_calls(get_metric_statistics_calls(5))

    def test_wait_for_metric_data_point_me_success(self):
        self.mock_cw_service.get_metric_statistics.side_effect = [
            {'Datapoints': [{'Maximum': '50'}]},
            {'Datapoints': [{'Maximum': '60'}]},
            {'Datapoints': [{'Maximum': '75'}]},
        ]

        datapoint = 70
        operator = Operator.MORE_OR_EQUAL
        actual_datapoint = cw_utils.wait_for_metric_data_point(session=self.session_mock,
                                                               datapoint_threshold=datapoint,
                                                               name=metric_name,
                                                               start_time_utc=start_time_utc,
                                                               end_time_utc=end_time_utc,
                                                               namespace=metric_namespace,
                                                               operator=operator,
                                                               time_out_secs=time_out_secs,
                                                               sleep_time_sec=sleep_time_sec,
                                                               dimensions=dimensions)
        self.assertEqual(75.0, actual_datapoint)
        assert actual_datapoint >= datapoint
        self.mock_cw_service.get_metric_statistics.assert_has_calls(get_metric_statistics_calls(3))

    def test_wait_for_metric_data_point_le_success(self):
        self.mock_cw_service.get_metric_statistics.side_effect = [
            {'Datapoints': [{'Maximum': '50'}]},
            {'Datapoints': [{'Maximum': '60'}]},
            {'Datapoints': [{'Maximum': '3'}]},
        ]

        datapoint = 5
        operator = Operator.LESS_OR_EQUAL
        actual_datapoint = cw_utils.wait_for_metric_data_point(session=self.session_mock,
                                                               datapoint_threshold=datapoint,
                                                               name=metric_name,
                                                               start_time_utc=start_time_utc,
                                                               end_time_utc=end_time_utc,
                                                               namespace=metric_namespace,
                                                               operator=operator,
                                                               time_out_secs=time_out_secs,
                                                               sleep_time_sec=sleep_time_sec,
                                                               dimensions=dimensions)
        self.assertEqual(3.0, actual_datapoint)
        assert actual_datapoint <= datapoint
        self.mock_cw_service.get_metric_statistics.assert_has_calls(get_metric_statistics_calls(3))
