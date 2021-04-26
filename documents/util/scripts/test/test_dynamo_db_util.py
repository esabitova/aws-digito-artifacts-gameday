
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, call, patch
from parameterized import parameterized

import pytest
from documents.util.scripts.src.dynamo_db_util import (_describe_time_to_live, _execute_boto3_dynamodb,
                                                       _describe_contributor_insights,
                                                       _describe_kinesis_destinations,
                                                       _describe_table,
                                                       _get_global_table_all_regions,
                                                       _parse_date_time,
                                                       copy_active_kinesis_destinations,
                                                       _get_global_secondary_indexes,
                                                       get_global_table_active_regions,
                                                       parse_recovery_date_time,
                                                       set_up_replication,
                                                       update_table_stream,
                                                       _update_table,
                                                       _enable_kinesis_destinations,
                                                       _update_tags,
                                                       _list_tags,
                                                       copy_resource_tags,
                                                       copy_contributor_insights_settings,
                                                       _update_contributor_insights,
                                                       _update_time_to_live,
                                                       copy_time_to_live,
                                                       wait_replication_status_in_all_regions)


GENERIC_SUCCESS_RESULT = {
    "ResponseMetadata": {
        "HTTPStatusCode": 200
    }
}
UPDATE_TABLE_STREAM_RESPONSE = {
    **GENERIC_SUCCESS_RESULT,
    "StreamSpecification": {
        "StreamEnabled": True,
        "StreamViewType": 'NEW_IMAGE'
    }
}
DESCRIBE_KINESIS_DESTINATIONS_RESPONSE = {
    **GENERIC_SUCCESS_RESULT,
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
    **GENERIC_SUCCESS_RESULT,
    "StreamArn": "TestStreamArn1",
    "DestinationStatus": 'ENABLING',
    "DestinationStatusDescription": 'Description'
}

LIST_TAG_RESPONCE = {
    **GENERIC_SUCCESS_RESULT,
    "Tags": [
        {
            "Key": "Key",
            "Value": "Value"
        }
    ]
}

TAG_RESOURCE_RESPONCE = {
    **GENERIC_SUCCESS_RESULT
}

DESCRIBE_TABLE_RESPONCE = {
    **GENERIC_SUCCESS_RESULT,
    "Table": {
        "AttributeDefinitions": [
            {
                "AttributeName": "Partition_key",
                "AttributeType": "S"
            },
            {
                "AttributeName": "another-fkey",
                "AttributeType": "S"
            },
            {
                "AttributeName": "id",
                "AttributeType": "S"
            }
        ],
        "TableName": "myable",
        "KeySchema": [
            {
                "AttributeName": "id",
                "KeyType": "HASH"
            }
        ],
        "TableStatus": "ACTIVE",
        "CreationDateTime": "2021-04-08T18:25:03.335000+04:00",
        "ProvisionedThroughput": {
            "NumberOfDecreasesToday": 0,
            "ReadCapacityUnits": 5,
            "WriteCapacityUnits": 5
        },
        "TableSizeBytes": 0,
        "ItemCount": 0,
        "TableArn": "arn:aws:dynamodb:us-east-2:435978235099:table/myable",
        "TableId": "cd7e8790-c589-4d6d-9a5e-042d61c20fed",
        "GlobalSecondaryIndexes": [
            {
                "IndexName": "Partition_key-index",
                "KeySchema": [
                    {
                        "AttributeName": "Partition_key",
                        "KeyType": "HASH"
                    }
                ],
                "Projection": {
                    "ProjectionType": "ALL"
                },
                "IndexStatus": "ACTIVE",
                "ProvisionedThroughput": {
                    "NumberOfDecreasesToday": 0,
                    "ReadCapacityUnits": 5,
                    "WriteCapacityUnits": 5
                },
                "IndexSizeBytes": 0,
                "ItemCount": 0,
                "IndexArn": "arn:aws:dynamodb:us-east-2:435978235099:table/myable/index/Partition_key-index"
            },
            {
                "IndexName": "another-fkey-index",
                "KeySchema": [
                    {
                        "AttributeName": "another-fkey",
                        "KeyType": "HASH"
                    }
                ],
                "Projection": {
                    "ProjectionType": "ALL"
                },
                "IndexStatus": "ACTIVE",
                "ProvisionedThroughput": {
                    "NumberOfDecreasesToday": 0,
                    "ReadCapacityUnits": 5,
                    "WriteCapacityUnits": 5
                },
                "IndexSizeBytes": 0,
                "ItemCount": 0,
                "IndexArn": "arn:aws:dynamodb:us-east-2:435978235099:table/myable/index/another-fkey-index"
            }
        ],
        "StreamSpecification": {
            "StreamEnabled": True,
            "StreamViewType": "NEW_AND_OLD_IMAGES"
        },
        "LatestStreamLabel": "2021-04-11T16:50:33.128",
        "LatestStreamArn": "arn:aws:dynamodb:us-east-2:435978235099:table/myable/stream/2021-04-11T16:50:33.128",
        "GlobalTableVersion": "2019.11.21",
        "Replicas": [
            {
                "RegionName": "ap-southeast-1",
                "ReplicaStatus": "ACTIVE",
                "ReplicaStatusDescription": "Failed to describe settings for the replica in region: ‘ap-southeast-1’."
            }
        ]
    }
}

GET_CONTRIBUTOR_INSIGHTS_RESPONSE = {
    "TableContributorInsightsStatus": "DISABLED",
    "IndexesContributorInsightsStatus":
    "[{\"IndexName\": \"digito-index-1\", \"ContributorInsightsStatus\": \"DISABLED\"}]"
}
DESCRIBE_CONTRIBUTOR_INSIGHTS_FOR_TABLE_RESPONCE = {
    **GENERIC_SUCCESS_RESULT,
    "TableName": "myable",
    "ContributorInsightsRuleList": [
        "DynamoDBContributorInsights-PKC-myable-Partition_key-index-1618028180292",
        "DynamoDBContributorInsights-PKT-myable-Partition_key-index-1618028180292"
    ],
    "ContributorInsightsStatus": "ENABLED",
    "LastUpdateDateTime": "2021-04-10T08:16:20.426000+04:00"
}

DESCRIBE_CONTRIBUTOR_INSIGHTS_FOR_TABLE_AND_INDEX_RESPONCE = {
    **GENERIC_SUCCESS_RESULT,
    "TableName": "myable",
    "IndexName": "Partition_key-index",
    "ContributorInsightsRuleList": [
        "DynamoDBContributorInsights-PKC-myable-Partition_key-index-1618028180292",
        "DynamoDBContributorInsights-PKT-myable-Partition_key-index-1618028180292"
    ],
    "ContributorInsightsStatus": "ENABLED",
    "LastUpdateDateTime": "2021-04-10T08:16:20.426000+04:00"
}
UPDATE_CONTRIBUTOR_INSIGHTS_FOR_TABLE_RESPONCE = {
    **GENERIC_SUCCESS_RESULT,
    "TableName": "myable",
    "ContributorInsightsStatus": "ENABLING",
}
UPDATE_CONTRIBUTOR_INSIGHTS_FOR_TABLE_AND_INDEX_RESPONCE = {
    **GENERIC_SUCCESS_RESULT,
    "TableName": "myable",
    "IndexName": "Partition_key-index",
    "ContributorInsightsStatus": "ENABLING",
}
UPDATE_TTL_RESPONSE = {
    **GENERIC_SUCCESS_RESULT,
    'TimeToLiveSpecification': {
        'Enabled': True,
        'AttributeName': 'End_Date'
    }
}
DESCRIBE_TTL_RESPONSE = {
    **GENERIC_SUCCESS_RESULT,
    "TimeToLiveDescription": {
        "TimeToLiveStatus": "ENABLED",
        "AttributeName": "End_Date"
    }
}


@pytest.mark.unit_test
class TestDynamoDbUtil(unittest.TestCase):
    CALLS_COUNTER = 0

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
        self.dynamodb_client_mock.update_time_to_live.return_value = UPDATE_TTL_RESPONSE
        self.dynamodb_client_mock.tag_resource.return_value = TAG_RESOURCE_RESPONCE
        self.dynamodb_client_mock.describe_table.return_value = DESCRIBE_TABLE_RESPONCE
        self.dynamodb_client_mock.describe_time_to_live.return_value = DESCRIBE_TTL_RESPONSE
        self.dynamodb_client_mock.describe_contributor_insights.return_value = \
            DESCRIBE_CONTRIBUTOR_INSIGHTS_FOR_TABLE_RESPONCE
        self.dynamodb_client_mock.update_contributor_insights.return_value = \
            UPDATE_CONTRIBUTOR_INSIGHTS_FOR_TABLE_RESPONCE

        self.dynamodb_client_mock\
            .describe_kinesis_streaming_destination\
            .return_value = DESCRIBE_KINESIS_DESTINATIONS_RESPONSE

        self.dynamodb_client_mock\
            .enable_kinesis_streaming_destination\
            .return_value = ENABLE_KINESIS_DESTINATIONS_RESPONSE
        TestDynamoDbUtil.CALLS_COUNTER = 0

    def tearDown(self):
        self.patcher.stop()

    @staticmethod
    def get_global_table_all_regions_mock(**kwargs):
        if TestDynamoDbUtil.CALLS_COUNTER == 0:
            TestDynamoDbUtil.CALLS_COUNTER += 1
            return [{
                "RegionName": "ap-southeast-1",
                "ReplicaStatus": "ENABLING"
            }]
        else:
            TestDynamoDbUtil.CALLS_COUNTER += 1
            return [{
                "RegionName": "ap-southeast-1",
                "ReplicaStatus": "ACTIVE"
            }]

    @staticmethod
    def describe_contributor_mock(**kwargs):
        if "table_name" in kwargs and "index_name" in kwargs:
            return DESCRIBE_CONTRIBUTOR_INSIGHTS_FOR_TABLE_AND_INDEX_RESPONCE
        else:
            return DESCRIBE_CONTRIBUTOR_INSIGHTS_FOR_TABLE_RESPONCE

    def test__execute_boto3_dynamodb_raises_exception(self):
        with self.assertRaises(ValueError):
            _execute_boto3_dynamodb(lambda x: {'ResponseMetadata': {'HTTPStatusCode': 500}})

    @parameterized.expand([({}, {})])
    def test_get_global_table_active_regions_raises_exception(self, events, context):
        with self.assertRaises(KeyError):
            get_global_table_active_regions(events=events, context={})

    @parameterized.expand([
        ({}, {}),
        ({'TableName': 'my_table'}, {})
    ])
    def test_set_up_replication_raises_exception(self, events, context):
        with self.assertRaises(KeyError):
            set_up_replication(events=events, context=context)

    @parameterized.expand([
        ({}, {}),
        ({'TableName': 'my_table'}, {}),
        ({'TableName': 'my_table', 'ReplicasRegionsToWait': 'somevalue'}, {})
    ])
    def test_wait_replication_status_in_all_regions_raises_exception(self, events, context):
        with self.assertRaises(KeyError):
            wait_replication_status_in_all_regions(events=events, context=context)

    def test_wait_replication_status_in_all_regions_raises_timeout(self):
        events = {
            "TableName": 'my_table',
            "ReplicasRegionsToWait": ['ap-southeast-1'],
            "WaitTimeoutSeconds": 0
        }
        with self.assertRaises(TimeoutError):
            wait_replication_status_in_all_regions(events=events, context={})

    @parameterized.expand([
        ({}, {}),
        ({'SourceTableName': 'my_table'}, {})
    ])
    def test_copy_contributor_insights_settings_raises_exception(self, events, context):
        with self.assertRaises(KeyError):
            copy_contributor_insights_settings(events=events, context=context)

    @parameterized.expand([
        ({}, {}),
        ({'SourceTableName': 'my_table'}, {}),
        ({'SourceTableName': 'my_table', 'TargetTableName': 'my_table'}, {}),
        ({'SourceTableName': 'my_table', 'TargetTableName': 'my_table', 'Region': 'Region'}, {})
    ])
    def test_update_resource_tags_raises_exception(self, events, context):
        with self.assertRaises(KeyError):
            copy_resource_tags(events=events, context=context)

    @parameterized.expand([
        ({}, {}),
        ({'SourceTableName': 'my_table'}, {})
    ])
    def test_copy_time_to_live_raises_exception(self, events, context):
        with self.assertRaises(KeyError):
            copy_time_to_live(events=events, context=context)

    @parameterized.expand([
        ({}, {}),
        ({'SourceTableName': 'my_table'}, {})
    ])
    def test_copy_active_kinesis_destinations_raises_exception(self, events, context):
        with self.assertRaises(KeyError):
            copy_active_kinesis_destinations(events=events, context=context)

    @parameterized.expand([
        ({}, {}),
        ({'TableName': 'my_table'}, {}),
        ({'TableName': 'my_table', 'StreamEnabled': 'StreamEnabled'}, {})
    ])
    def test_update_table_stream_raises_exception(self, events, context):
        with self.assertRaises(KeyError):
            update_table_stream(events=events, context=context)

    @parameterized.expand([({}, {})])
    def test_parse_recovery_date_time_raises_exception(self, events, context):
        with self.assertRaises(KeyError):
            parse_recovery_date_time(events=events, context=context)

    def test__parse_recovery_date_time_correct_format_success(self):
        date_time_str = '2021-01-01T15:00:00+0400'

        result = _parse_date_time(date_time_str=date_time_str,
                                  format="%Y-%m-%dT%H:%M:%S%z")

        tz = timezone(timedelta(seconds=14400))
        expected = datetime(2021, 1, 1, 15, 0, 0, tzinfo=tz)
        self.assertEquals(result, expected)

    def test__parse_recovery_date_time_correct_empty_input(self):
        date_time_str = ''

        result = _parse_date_time(date_time_str=date_time_str,
                                  format="%Y-%m-%dT%H:%M:%S%z")

        self.assertIsNone(result)

    def test__parse_recovery_date_time_wrong_format(self):
        date_time_str = '02/01/2001T15:00:00+0400'

        result = _parse_date_time(date_time_str=date_time_str,
                                  format="%Y-%m-%dT%H:%M:%S%z")

        self.assertIsNone(result)

    def test__describe_time_to_live(self):
        result = _describe_time_to_live(table_name='my_table')

        self.assertEqual(result, DESCRIBE_TTL_RESPONSE)

    @patch('documents.util.scripts.src.dynamo_db_util._describe_table',
           return_value=DESCRIBE_TABLE_RESPONCE)
    def test__get_global_table_all_regions(self, describe_mock):
        result = _get_global_table_all_regions(table_name='my_table')

        self.assertEqual(result, [
            {
                "RegionName": "ap-southeast-1",
                "ReplicaStatus": "ACTIVE",
                "ReplicaStatusDescription": "Failed to describe settings for the replica in region: ‘ap-southeast-1’."
            }
        ])

        describe_mock.assert_called_with(table_name='my_table')

    @patch('documents.util.scripts.src.dynamo_db_util._get_global_table_all_regions',
           new_callable=lambda: TestDynamoDbUtil.get_global_table_all_regions_mock)
    @patch('documents.util.scripts.src.dynamo_db_util.time.sleep')
    def test_wait_replication_status_in_all_regions(self, sleep_mock, get_mock):
        events = {
            "TableName": 'my_table',
            "ReplicasRegionsToWait": ['ap-southeast-1'],
            "WaitTimeoutSeconds": 2
        }
        result = wait_replication_status_in_all_regions(events=events, context={})

        self.assertEqual(result['GlobalTableRegionsActive'], ['ap-southeast-1'])
        self.assertEqual(TestDynamoDbUtil.CALLS_COUNTER, 2)
        sleep_mock.assert_has_calls([call(20)])

    def test_wait_replication_status_in_all_regions_no_regions(self):
        events = {
            "TableName": 'my_table',
            "ReplicasRegionsToWait": [],
            "WaitTimeoutSeconds": 1
        }
        result = wait_replication_status_in_all_regions(events=events, context={})

        self.assertEqual(result['GlobalTableRegionsActive'], [])

    @patch('documents.util.scripts.src.dynamo_db_util._update_table',
           return_value={})
    def test_set_up_replication(self, update_mock):
        events = {
            "TableName": 'my_table',
            "GlobalTableRegions": ['ap-southeast-1']
        }
        result = set_up_replication(events=events, context={})

        self.assertEqual(result['GlobalTableRegionsAdded'], ['ap-southeast-1'])

        update_mock.assert_called_with(table_name='my_table',
                                       ReplicaUpdates=[{
                                           'Create': {
                                               'RegionName': 'ap-southeast-1'
                                           }}])

    @patch('documents.util.scripts.src.dynamo_db_util._get_global_table_all_regions',
           return_value=[
               {
                   "RegionName": "ap-southeast-1",
                   "ReplicaStatus": "ACTIVE",
                   "ReplicaStatusDescription": ""
               }
           ])
    def test_get_global_table_active_regions(self, describe_mock):
        events = {
            "TableName": 'my_table'
        }
        result = get_global_table_active_regions(events=events, context={})

        self.assertEqual(result['GlobalTableRegions'], ['ap-southeast-1'])

        describe_mock.assert_called_with(table_name='my_table')

    @patch('documents.util.scripts.src.dynamo_db_util._parse_date_time',
           return_value=datetime(2021, 1, 1, 4, 0, 0))
    def test_parse_recovery_date_time_input_valid(self, parse_mock):

        result = parse_recovery_date_time(events={
            'RecoveryPointDateTime': 'some_valid_date'
        }, context={})

        self.assertEqual(result['RecoveryPointDateTime'], '2021-01-01T04:00:00')
        self.assertEqual(result['UseLatestRecoveryPoint'], False)
        parse_mock.assert_called_with(date_time_str='some_valid_date',
                                      format='%Y-%m-%dT%H:%M:%S%z')

    @patch('documents.util.scripts.src.dynamo_db_util._parse_date_time',
           return_value=None)
    def test_parse_recovery_date_time_input_not_valid(self, parse_mock):

        result = parse_recovery_date_time(events={
            'RecoveryPointDateTime': 'not_valid_date'
        }, context={})

        self.assertEqual(result['RecoveryPointDateTime'], 'None')
        self.assertEqual(result['UseLatestRecoveryPoint'], True)
        parse_mock.assert_called_with(date_time_str='not_valid_date',
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
    @patch('documents.util.scripts.src.dynamo_db_util._enable_kinesis_destinations',
           return_value=DESCRIBE_KINESIS_DESTINATIONS_RESPONSE)
    def test_copy_active_kinesis_destinations(self, enable_mock, get_destination_mock):
        result = copy_active_kinesis_destinations(events={
            "SourceTableName": "my_table",
            "TargetTableName": "my_table_target"
        }, context={})

        expected_output = ["TestStreamArn1"]
        self.assertEqual(result, expected_output)
        get_destination_mock.assert_called_with(table_name='my_table')
        enable_mock.assert_has_calls([call(table_name='my_table_target', kds_arn='TestStreamArn1')])

    def test__enable_kinesis_destinations(self):

        result = _enable_kinesis_destinations(table_name="my_table", kds_arn='arn')

        self.assertEqual(result, ENABLE_KINESIS_DESTINATIONS_RESPONSE)

    def test__update_time_to_live(self):

        result = _update_time_to_live(table_name="my_table", is_enabled=True, attribute_name="End_Date")

        self.assertEqual(result, UPDATE_TTL_RESPONSE)
        self.dynamodb_client_mock\
            .update_time_to_live\
            .assert_called_with(TableName="my_table",
                                TimeToLiveSpecification={
                                    "Enabled": True,
                                    "AttributeName": 'End_Date'
                                })

    @patch('documents.util.scripts.src.dynamo_db_util._update_time_to_live',
           return_value=UPDATE_TTL_RESPONSE)
    @patch('documents.util.scripts.src.dynamo_db_util._describe_time_to_live',
           return_value=DESCRIBE_TTL_RESPONSE)
    def test_copy_time_to_live_enable(self, describe_mock, update_mock):

        result = copy_time_to_live(events={
            "SourceTableName": "my_table",
            "TargetTableName": "my_table_target",
        }, context={})

        self.assertEqual(result, {'TTLAttribute': 'End_Date', 'TTLCopied': True})
        describe_mock.assert_called_with(table_name='my_table')
        update_mock.assert_called_with(table_name='my_table_target', is_enabled=True, attribute_name='End_Date')

    @patch('documents.util.scripts.src.dynamo_db_util._update_time_to_live',
           return_value=UPDATE_TTL_RESPONSE)
    @patch('documents.util.scripts.src.dynamo_db_util._describe_time_to_live',
           return_value={"TimeToLiveDescription": {}})
    def test_copy_time_to_live_disabled(self, describe_mock, update_mock: MagicMock):

        result = copy_time_to_live(events={
            "SourceTableName": "my_table",
            "TargetTableName": "my_table_target",
        }, context={})

        self.assertEqual(result, {'TTLAttribute': '', 'TTLCopied': False})
        update_mock.assert_not_called()

    def test__list_tags(self):

        result = _list_tags(resource_arn="my_table")

        self.assertEqual(result, LIST_TAG_RESPONCE)

    def test__update_tags(self):

        result = _update_tags(resource_arn="my_table", tags=[])

        self.assertEqual(result, TAG_RESOURCE_RESPONCE)

    @patch('documents.util.scripts.src.dynamo_db_util._update_tags',
           return_value=TAG_RESOURCE_RESPONCE)
    @patch('documents.util.scripts.src.dynamo_db_util._list_tags',
           return_value=LIST_TAG_RESPONCE)
    def test_update_resource_tags(self, list_mock, update_mock):
        events = {
            "SourceTableName": "my_table",
            "TargetTableName": "my_table_target",
            "Region": "us-west-1",
            "Account": "1234567890"
        }
        result = copy_resource_tags(events=events, context={})

        self.assertEqual(result, {"Tags": LIST_TAG_RESPONCE["Tags"]})
        update_mock.assert_called_with(resource_arn='arn:aws:dynamodb:us-west-1:1234567890:table/my_table_target',
                                       tags=LIST_TAG_RESPONCE['Tags'])
        list_mock.assert_called_with(resource_arn='arn:aws:dynamodb:us-west-1:1234567890:table/my_table')

    def test__describe_table(self):

        result = _describe_table(table_name="my_table")

        self.assertEqual(result, DESCRIBE_TABLE_RESPONCE)

    @patch('documents.util.scripts.src.dynamo_db_util._describe_table',
           return_value=DESCRIBE_TABLE_RESPONCE)
    def test__get_global_secondary_indexes(self, describe_mock):
        result = _get_global_secondary_indexes(table_name="my_table")

        self.assertEqual(result, ['Partition_key-index', 'another-fkey-index'])
        describe_mock.assert_called_with(table_name='my_table')

    def test__describe_contributor_insights_for_table(self):

        result = _describe_contributor_insights(table_name="my_table")

        self.assertEqual(result, DESCRIBE_CONTRIBUTOR_INSIGHTS_FOR_TABLE_RESPONCE)
        self.dynamodb_client_mock\
            .describe_contributor_insights\
            .assert_called_with(TableName='my_table')

    def test__describe_contributor_insights_for_index(self):
        self.dynamodb_client_mock.describe_contributor_insights.return_value =\
            DESCRIBE_CONTRIBUTOR_INSIGHTS_FOR_TABLE_AND_INDEX_RESPONCE

        result = _describe_contributor_insights(table_name="my_table", index_name="my_index")

        self.assertEqual(result, DESCRIBE_CONTRIBUTOR_INSIGHTS_FOR_TABLE_AND_INDEX_RESPONCE)
        self.dynamodb_client_mock\
            .describe_contributor_insights\
            .assert_called_with(TableName='my_table', IndexName="my_index")

    @patch('documents.util.scripts.src.dynamo_db_util._describe_contributor_insights',
           new_callable=lambda: TestDynamoDbUtil.describe_contributor_mock)
    @patch('documents.util.scripts.src.dynamo_db_util._update_contributor_insights',
           return_value={})
    @patch('documents.util.scripts.src.dynamo_db_util._get_global_secondary_indexes',
           return_value=["Partition_key-index"])
    def test_copy_contributor_insights_settings(self, get_indexes_mock, update_mock, describe_mock):
        events = {
            "SourceTableName": "my_table",
            "TargetTableName": "my_table_target",
            "Indexes": ["Partition_key-index"]
        }
        result = copy_contributor_insights_settings(events=events, context={})

        get_indexes_mock.assert_called_with(table_name='my_table')
        update_mock.assert_has_calls([
            call(table_name='my_table_target',
                 status='ENABLE'),
            call(table_name='my_table_target',
                 status='ENABLE',
                 index_name="Partition_key-index")
        ])

        self.assertEqual(result['CopiedTableContributorInsightsStatus'], 'ENABLED')
        self.assertEqual(result['CopiedIndexesContributorInsightsStatus'],
                         [{"IndexName": "Partition_key-index", "ContributorInsightsStatus": "ENABLED"}])

    def test__update_contributor_insights_of_table(self):
        _update_contributor_insights(table_name='my_table', status='ENABLE')

        self.dynamodb_client_mock\
            .update_contributor_insights\
            .assert_called_with(TableName='my_table',
                                ContributorInsightsAction='ENABLE')

    def test__update_contributor_insights_of_index(self):
        self.dynamodb_client_mock.update_contributor_insights.return_value = \
            UPDATE_CONTRIBUTOR_INSIGHTS_FOR_TABLE_AND_INDEX_RESPONCE

        _update_contributor_insights(table_name='my_table',
                                     index_name='Partition_key-index',
                                     status='ENABLE')

        self.dynamodb_client_mock\
            .update_contributor_insights\
            .assert_called_with(TableName='my_table',
                                IndexName='Partition_key-index',
                                ContributorInsightsAction='ENABLE')
