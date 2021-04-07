
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from documents.util.scripts.src.dynamo_db_util import (_parse_recovery_date_time,
                                                       parse_recovery_date_time,
                                                       update_table_stream,
                                                       _update_table)

UPDATE_TABLE_STREAM_RESPONSE = {
    "ResponseMetadata": {
        "HTTPStatusCode": 200
    },
    "StreamSpecification": {
        "StreamEnabled": True,
        "StreamViewType": 'NEW_IMAGE'
    }
}


@pytest.mark.unit_test
class TestS3Util(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('boto3.client')
        self.client = self.patcher.start()
        self.dynamodb_client_mock = MagicMock()
        self.side_effect_map = {
            'dynamodb': self.dynamodb_client_mock
        }
        self.client.side_effect = lambda service_name: self.side_effect_map.get(service_name)
        self.dynamodb_client_mock.update_table.return_value = UPDATE_TABLE_STREAM_RESPONSE

    def tearDown(self):
        self.patcher.stop()

    def test__parse_recovery_date_time_correct_format_success(self):
        date_time_str = '2021-01-01T15:00:00+0400'

        result = _parse_recovery_date_time(restore_date_time_str=date_time_str,
                                           format="%Y-%m-%dT%H:%M:%S%z")

        tz = timezone(timedelta(seconds=14400))
        expected = datetime(2021, 1, 1, 15, 0, 0, tzinfo=tz)
        self.assertEquals(result, expected)

    def test__parse_recovery_date_time_correct_empty_input(self):
        date_time_str = ''

        result = _parse_recovery_date_time(restore_date_time_str=date_time_str,
                                           format="%Y-%m-%dT%H:%M:%S%z")

        self.assertIsNone(result)

    def test__parse_recovery_date_time_wrong_format(self):
        date_time_str = '02/01/2001T15:00:00+0400'

        result = _parse_recovery_date_time(restore_date_time_str=date_time_str,
                                           format="%Y-%m-%dT%H:%M:%S%z")

        self.assertIsNone(result)

    @patch('documents.util.scripts.src.dynamo_db_util._parse_recovery_date_time',
           return_value=datetime(2021, 1, 1, 4, 0, 0))
    def test_parse_recovery_date_time_input_valid(self, parse_mock):

        result = parse_recovery_date_time(events={
            'RecoveryPointDateTime': 'some_valid_date'
        }, context={})

        self.assertEqual(result['RecoveryPointDateTime'], '2021-01-01T04:00:00')
        self.assertEqual(result['UseLatestRecoveryPoint'], False)
        parse_mock.assert_called_with(restore_date_time_str='some_valid_date',
                                      format='%Y-%m-%dT%H:%M:%S%z')

    @patch('documents.util.scripts.src.dynamo_db_util._parse_recovery_date_time',
           return_value=None)
    def test_parse_recovery_date_time_input_not_valid(self, parse_mock):

        result = parse_recovery_date_time(events={
            'RecoveryPointDateTime': 'not_valid_date'
        }, context={})

        self.assertEqual(result['RecoveryPointDateTime'], 'None')
        self.assertEqual(result['UseLatestRecoveryPoint'], True)
        parse_mock.assert_called_with(restore_date_time_str='not_valid_date',
                                      format='%Y-%m-%dT%H:%M:%S%z')

    @patch('documents.util.scripts.src.dynamo_db_util._update_table',
           return_value={
               "StreamSpecification": {
                   "StreamEnabled": True,
                   "StreamViewType": 'NEW_IMAGE'
               }
           })
    def test_update_table_stream(self, update_mock):

        result = update_table_stream(events={
            "StreamEnabled": True,
            "StreamViewType": 'NEW_IMAGE',
            "TableName": "my_table"
        }, context={})

        self.assertEqual(result['StreamEnabled'], True)
        self.assertEqual(result['StreamViewType'], 'NEW_IMAGE')
        expected_input = {
            "StreamSpecification": {
                "StreamEnabled": True,
                "StreamViewType": 'NEW_IMAGE'
            }
        }
        update_mock.assert_called_with(table_name='my_table', **expected_input)

    def test__update_table(self):

        result = _update_table(table_name="my_table",
                               StreamSpecification={"StreamEnabled": True,
                                                    "StreamViewType": 'NEW_IMAGE'
                                                    }
                               )

        self.assertEqual(result['StreamSpecification']['StreamEnabled'], True)
        self.assertEqual(result['StreamSpecification']['StreamViewType'], 'NEW_IMAGE')
