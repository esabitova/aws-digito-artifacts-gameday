
import json
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from documents.util.scripts.src.dynamo_db_util import (_describe_kinesis_destinations,
                                                       _parse_recovery_date_time,
                                                       get_active_kinesis_destinations,
                                                       parse_recovery_date_time,
                                                       update_table_stream,
                                                       _update_table,
                                                       _enable_kinesis_destinations,
                                                       add_kinesis_destinations,
                                                       _update_tags,
                                                       _list_tags,
                                                       list_resource_tags,
                                                       update_resource_tags)

UPDATE_TABLE_STREAM_RESPONSE = {
    "ResponseMetadata": {
        "HTTPStatusCode": 200
    },
    "StreamSpecification": {
        "StreamEnabled": True,
        "StreamViewType": 'NEW_IMAGE'
    }
}
DESCRIBE_KINESIS_DESTINATIONS_RESPONSE = {
    "ResponseMetadata": {
        "HTTPStatusCode": 200
    },
    "KinesisDataStreamDestinations": [{
        "StreamArn": "TestStreamArn1",
        "DestinationStatus": 'ENABLING',
        "DestinationStatusDescription": 'Description'
    },
        {
        "StreamArn": "TestStreamArn2",
        "DestinationStatus": 'ENABLE_FAILED',
        "DestinationStatusDescription": 'Description'
    }]
}

ENABLE_KINESIS_DESTINATIONS_RESPONSE = {
    "ResponseMetadata": {
        "HTTPStatusCode": 200
    },
    "StreamArn": "TestStreamArn1",
    "DestinationStatus": 'ENABLING',
    "DestinationStatusDescription": 'Description'
}

LIST_TAG_RESPONCE = {
    "ResponseMetadata": {
        "HTTPStatusCode": 200
    },
    "Tags": [
        {
            "Key": "Key",
            "Value": "Value"
        }
    ]
}

TAG_RESOURCE_RESPONCE = {
    "ResponseMetadata": {
        "HTTPStatusCode": 200
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
        self.dynamodb_client_mock.list_tags_of_resource.return_value = LIST_TAG_RESPONCE
        self.dynamodb_client_mock.tag_resource.return_value = TAG_RESOURCE_RESPONCE

        self.dynamodb_client_mock\
            .describe_kinesis_streaming_destination\
            .return_value = DESCRIBE_KINESIS_DESTINATIONS_RESPONSE

        self.dynamodb_client_mock\
            .enable_kinesis_streaming_destination\
            .return_value = ENABLE_KINESIS_DESTINATIONS_RESPONSE

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

    def test__describe_kinesis_destinations(self):

        result = _describe_kinesis_destinations(table_name="my_table")

        self.assertEqual(result, DESCRIBE_KINESIS_DESTINATIONS_RESPONSE)

    @patch('documents.util.scripts.src.dynamo_db_util._describe_kinesis_destinations',
           return_value=DESCRIBE_KINESIS_DESTINATIONS_RESPONSE)
    def test_get_active_kinesis_destinations(self, get_destination_mock):
        result = get_active_kinesis_destinations(events={
            "TableName": "my_table"
        }, context={})

        expected_output = {
            "KinesisDestinations": json.dumps([{
                "StreamArn": "TestStreamArn1",
                "DestinationStatus": 'ENABLING',
                "DestinationStatusDescription": 'Description'
            }])
        }
        self.assertEqual(result, expected_output)
        get_destination_mock.assert_called_with(table_name='my_table')

    def test__enable_kinesis_destinations(self):

        result = _enable_kinesis_destinations(table_name="my_table", kds_arn='arn')

        self.assertEqual(result, ENABLE_KINESIS_DESTINATIONS_RESPONSE)

    @patch('documents.util.scripts.src.dynamo_db_util._enable_kinesis_destinations',
           return_value=DESCRIBE_KINESIS_DESTINATIONS_RESPONSE)
    def test_add_kinesis_destinations(self, enable_mock):
        active_destinations = [{
            "StreamArn": "TestStreamArn1",
            "DestinationStatus": 'ENABLING',
            "DestinationStatusDescription": 'Description'
        }]

        result = add_kinesis_destinations(events={
            "TableName": "my_table",
            "Destinations": json.dumps(active_destinations)
        }, context={})

        expected_output = {
            "KinesisDestinations": json.dumps([{
                "StreamArn": "TestStreamArn1",
                "DestinationStatus": 'ENABLING',
                "DestinationStatusDescription": 'Description'
            }])
        }

        self.assertEqual(result, expected_output)
        enable_mock.assert_called_with(table_name='my_table', kds_arn='TestStreamArn1')

    def test__list_tags(self):

        result = _list_tags(resource_arn="my_table")

        self.assertEqual(result, LIST_TAG_RESPONCE)

    @patch('documents.util.scripts.src.dynamo_db_util._list_tags',
           return_value=LIST_TAG_RESPONCE)
    def test_list_resource_tags(self, mock_list_tags):
        result = list_resource_tags(events={
            "TableName": "my_table",
            "Region": "us-west-1",
            "Account": "1234567890"
        }, context={})

        self.assertEqual(result, {"Tags": json.dumps(LIST_TAG_RESPONCE["Tags"])})
        mock_list_tags.assert_called_with(resource_arn='arn:aws:dynamodb:us-west-1:1234567890:table/my_table')

    def test__update_tags(self):

        result = _update_tags(resource_arn="my_table", tags=[])

        self.assertEqual(result, TAG_RESOURCE_RESPONCE)

    @patch('documents.util.scripts.src.dynamo_db_util._update_tags',
           return_value=TAG_RESOURCE_RESPONCE)
    @patch('documents.util.scripts.src.dynamo_db_util.list_resource_tags',
           return_value=LIST_TAG_RESPONCE)
    def test_update_resource_tags(self, list_mock, update_mock):
        events = {
            "TableName": "my_table",
            "Region": "us-west-1",
            "Account": "1234567890",
            "Tags": json.dumps(LIST_TAG_RESPONCE['Tags'])
        }
        result = update_resource_tags(events=events, context={})

        self.assertEqual(result, {"Tags": json.dumps(LIST_TAG_RESPONCE["Tags"])})
        update_mock.assert_called_with(resource_arn='arn:aws:dynamodb:us-west-1:1234567890:table/my_table',
                                       tags=LIST_TAG_RESPONCE['Tags'])
        list_mock.assert_called_with(events=events, context={})
