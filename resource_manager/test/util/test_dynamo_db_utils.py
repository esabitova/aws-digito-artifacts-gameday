import unittest
from unittest.mock import MagicMock, call, patch

import pytest
import resource_manager.src.util.boto3_client_factory as client_factory
from botocore.exceptions import ClientError

from documents.util.scripts.test.mock_sleep import MockSleep
from resource_manager.src.util.dynamo_db_utils import (
    _check_if_backup_exists, _check_if_replicas_exist, _check_if_table_deleted, _create_backup,
    _delete_backup, _delete_backup_if_exist, _describe_backup,
    _describe_continuous_backups, _describe_contributor_insights, _describe_table,
    _execute_boto3_dynamodb, get_secondary_indexes, _get_global_table_all_regions,
    _update_table, add_global_table_and_wait_for_active,
    create_backup_and_wait_for_available, delete_backup_and_wait,
    get_item_single, get_item_async_stress_test,
    _get_random_value, generate_random_item,
    drop_and_wait_dynamo_db_table_if_exists, get_continuous_backups_status,
    get_contributor_insights_status_for_table_and_indexes,
    get_earliest_recovery_point_in_time, get_kinesis_destinations, get_stream_settings,
    get_time_to_live, remove_global_table_and_wait_for_active, wait_table_to_be_active)
from boto3.dynamodb.types import STRING, NUMBER, BINARY, Binary

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
DESCRIBE_TABLE_RESPONSE = {
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
UPDATE_TTL_RESPONSE = {
    **GENERIC_SUCCESS_RESULT,
    'TimeToLiveSpecification': {
        'Enabled': True,
        'AttributeName': 'End_Date'
    }
}
ENABLE_KINESIS_DESTINATIONS_RESPONSE = {
    **GENERIC_SUCCESS_RESULT,
    "StreamArn": "TestStreamArn1",
    "DestinationStatus": 'ENABLING',
    "DestinationStatusDescription": 'Description'
}
DELETE_BACKUP_RESPONSE = {
    **GENERIC_SUCCESS_RESULT,
    "BackupDescription": {
        "BackupDetails": {
            "BackupArn": "arn:aws:dynamodb:us-east-2:435978235099:table/myable/backup/01618662389955-43f7af5d",
            "BackupName": "mybackup",
            "BackupSizeBytes": 83,
            "BackupStatus": "DELETED",
            "BackupType": "USER",
            "BackupCreationDateTime": "2021-04-17T16:26:29.955000+04:00"
        },
        "SourceTableDetails": {
            "TableName": "myable",
            "TableId": "cd7e8790-c589-4d6d-9a5e-042d61c20fed",
            "TableArn": "arn:aws:dynamodb:us-east-2:435978235099:table/myable",
            "TableSizeBytes": 83,
            "KeySchema": [
                {
                    "AttributeName": "id",
                    "KeyType": "HASH"
                }
            ],
            "TableCreationDateTime": "2021-04-08T18:25:03.335000+04:00",
            "ProvisionedThroughput": {
                "ReadCapacityUnits": 5,
                "WriteCapacityUnits": 5
            },
            "ItemCount": 1,
            "BillingMode": "PROVISIONED"
        },
        "SourceTableFeatureDetails": {
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
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 5,
                        "WriteCapacityUnits": 5
                    }
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
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 5,
                        "WriteCapacityUnits": 5
                    }
                }
            ],
            "StreamDescription": {
                "StreamEnabled": True,
                "StreamViewType": "NEW_AND_OLD_IMAGES"
            }
        }
    }
}
DESCRIBE_BACKUP_RESPONSE = {
    **GENERIC_SUCCESS_RESULT,
    "BackupDescription": {
        "BackupDetails": {
            "BackupArn": "arn:aws:dynamodb:us-east-2:435978235099:table/myable/backup/01618662389955-43f7af5d",
            "BackupName": "mybackup",
            "BackupSizeBytes": 83,
            "BackupStatus": "AVAILABLE",
            "BackupType": "USER",
            "BackupCreationDateTime": "2021-04-17T16:26:29.955000+04:00"
        },
        "SourceTableDetails": {
            "TableName": "myable",
            "TableId": "cd7e8790-c589-4d6d-9a5e-042d61c20fed",
            "TableArn": "arn:aws:dynamodb:us-east-2:435978235099:table/myable",
            "TableSizeBytes": 83,
            "KeySchema": [
                {
                    "AttributeName": "id",
                    "KeyType": "HASH"
                }
            ],
            "TableCreationDateTime": "2021-04-08T18:25:03.335000+04:00",
            "ProvisionedThroughput": {
                "ReadCapacityUnits": 5,
                "WriteCapacityUnits": 5
            },
            "ItemCount": 1,
            "BillingMode": "PROVISIONED"
        },
        "SourceTableFeatureDetails": {
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
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 5,
                        "WriteCapacityUnits": 5
                    }
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
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 5,
                        "WriteCapacityUnits": 5
                    }
                }
            ],
            "StreamDescription": {
                "StreamEnabled": True,
                "StreamViewType": "NEW_AND_OLD_IMAGES"
            }
        }
    }
}
CREATE_BACKUP_RESPONSE = {
    **GENERIC_SUCCESS_RESULT,
    "BackupDetails": {
        "BackupArn": "arn:aws:dynamodb:us-east-2:435978235099:table/myable/backup/01618664635471-dddafc01",
        "BackupName": "mybackup",
        "BackupSizeBytes": 83,
        "BackupStatus": "CREATING",
        "BackupType": "USER",
        "BackupCreationDateTime": "2021-04-17T17:03:55.471000+04:00"
    }
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
DESCRIBE_TTL_RESPONSE = {
    **GENERIC_SUCCESS_RESULT,
    "TimeToLiveDescription": {
        "TimeToLiveStatus": "ENABLED",
        "AttributeName": "End_Date"
    }
}
DESCRIBE_CONTINUOUS_BACKUPS_RESPONSE = {
    **GENERIC_SUCCESS_RESULT,
    "ContinuousBackupsDescription": {
        "ContinuousBackupsStatus": "ENABLED",
        "PointInTimeRecoveryDescription": {
            "EarliestRestorableDateTime": "some time",
            "PointInTimeRecoveryStatus": "ENABLED"
        }
    }
}
RESOURCE_NOT_FOUND_ERROR = ClientError({'Error': {'Code': 'ResourceNotFoundException'}}, "")
BACKUP_NOT_FOUND_ERROR = ClientError({'Error': {'Code': 'BackupNotFoundException'}}, "")
RESOURCE_IN_USE_ERROR = ClientError({'Error': {'Code': 'ResourceInUseException'}}, "")


@pytest.mark.unit_test
class TestDynamoDbUtil(unittest.TestCase):

    def setUp(self):
        self.session_mock = MagicMock()
        self.dynamodb_client_mock = MagicMock()
        self.client_side_effect_map = {
            'dynamodb': self.dynamodb_client_mock,

        }
        self.session_mock.client.side_effect = lambda service_name, config=None: \
            self.client_side_effect_map.get(service_name)

        self.dynamodb_client_mock.update_table.return_value = UPDATE_TABLE_STREAM_RESPONSE
        self.dynamodb_client_mock.describe_table.return_value = DESCRIBE_TABLE_RESPONSE
        self.dynamodb_client_mock.describe_continuous_backups.return_value = DESCRIBE_CONTINUOUS_BACKUPS_RESPONSE
        self.dynamodb_client_mock.update_time_to_live.return_value = UPDATE_TTL_RESPONSE
        self.dynamodb_client_mock.delete_backup.return_value = DELETE_BACKUP_RESPONSE
        self.dynamodb_client_mock.describe_backup.return_value = DESCRIBE_BACKUP_RESPONSE
        self.dynamodb_client_mock.create_backup.return_value = CREATE_BACKUP_RESPONSE
        self.dynamodb_client_mock.describe_time_to_live.return_value = DESCRIBE_TTL_RESPONSE
        self.dynamodb_client_mock.describe_contributor_insights.return_value = \
            DESCRIBE_CONTRIBUTOR_INSIGHTS_FOR_TABLE_RESPONCE

        self.dynamodb_client_mock\
            .describe_kinesis_streaming_destination\
            .return_value = DESCRIBE_KINESIS_DESTINATIONS_RESPONSE

        self.dynamodb_client_mock\
            .enable_kinesis_streaming_destination\
            .return_value = ENABLE_KINESIS_DESTINATIONS_RESPONSE

    def tearDown(self):
        # Clean client factory cache after each test.
        client_factory.clients = {}
        client_factory.resources = {}

    def test__execute_boto3_dynamodb_raises_exception(self):
        with self.assertRaises(Exception) as context:
            _execute_boto3_dynamodb(self.session_mock,
                                    lambda x: {'ResponseMetadata': {'HTTPStatusCode': 500}})

        self.assertTrue(isinstance(context.exception, ValueError))

    def test_get_time_to_live(self):
        result = get_time_to_live(boto3_session=self.session_mock, table_name='my_table')

        self.assertEqual(result, DESCRIBE_TTL_RESPONSE['TimeToLiveDescription'])

    def test__update_table(self):

        result = _update_table(boto3_session=self.session_mock,
                               table_name="my_table",
                               StreamSpecification={"StreamEnabled": True,
                                                    "StreamViewType": 'NEW_IMAGE'
                                                    }
                               )

        self.assertEqual(result['StreamSpecification']['StreamEnabled'], True)
        self.assertEqual(result['StreamSpecification']['StreamViewType'], 'NEW_IMAGE')

    def test__describe_table(self):

        result = _describe_table(boto3_session=self.session_mock,
                                 table_name="my_table")

        self.assertEqual(result, DESCRIBE_TABLE_RESPONSE)

    def test_get_secondary_indexes(self):

        result = get_secondary_indexes(boto3_session=self.session_mock,
                                       table_name="my_table")

        self.assertEqual(result, ['Partition_key-index', 'another-fkey-index'])

    def test__describe_contributor_insights_for_table(self):

        result = _describe_contributor_insights(boto3_session=self.session_mock,
                                                table_name="my_table")

        self.assertEqual(result, DESCRIBE_CONTRIBUTOR_INSIGHTS_FOR_TABLE_RESPONCE)
        self.dynamodb_client_mock\
            .describe_contributor_insights\
            .assert_called_with(TableName='my_table')

    def test__describe_contributor_insights_for_index(self):
        self.dynamodb_client_mock.describe_contributor_insights.return_value =\
            DESCRIBE_CONTRIBUTOR_INSIGHTS_FOR_TABLE_AND_INDEX_RESPONCE

        result = _describe_contributor_insights(boto3_session=self.session_mock,
                                                table_name="my_table",
                                                index_name="my_index")

        self.assertEqual(result, DESCRIBE_CONTRIBUTOR_INSIGHTS_FOR_TABLE_AND_INDEX_RESPONCE)
        self.dynamodb_client_mock\
            .describe_contributor_insights\
            .assert_called_with(TableName='my_table', IndexName="my_index")

    def test_get_kinesis_destinations(self):

        result = get_kinesis_destinations(boto3_session=self.session_mock, table_name="my_table")

        self.assertEqual(result, DESCRIBE_KINESIS_DESTINATIONS_RESPONSE['KinesisDataStreamDestinations'])

    @patch('resource_manager.src.util.dynamo_db_utils._describe_table',
           return_value=DESCRIBE_TABLE_RESPONSE)
    def test_get_stream_settings(self, describe_mock):
        is_enabled, stream_type = get_stream_settings(boto3_session=self.session_mock,
                                                      table_name="my_table")
        self.assertTrue(is_enabled)
        self.assertEqual(stream_type, 'NEW_AND_OLD_IMAGES')
        describe_mock.assert_has_calls([
            call(boto3_session=self.session_mock,
                 table_name='my_table')
        ])

    @patch('resource_manager.src.util.dynamo_db_utils._describe_continuous_backups',
           return_value=DESCRIBE_CONTINUOUS_BACKUPS_RESPONSE)
    def test_get_continuous_backups_status(self, describe_mock):
        result = get_continuous_backups_status(boto3_session=self.session_mock,
                                               table_name="my_table")
        self.assertEqual(result, 'ENABLED')
        describe_mock.assert_has_calls([
            call(boto3_session=self.session_mock,
                 table_name='my_table')
        ])

    @patch('resource_manager.src.util.dynamo_db_utils._describe_contributor_insights',
           side_effect=[DESCRIBE_CONTRIBUTOR_INSIGHTS_FOR_TABLE_RESPONCE,
                        DESCRIBE_CONTRIBUTOR_INSIGHTS_FOR_TABLE_AND_INDEX_RESPONCE])
    @patch('resource_manager.src.util.dynamo_db_utils.get_secondary_indexes',
           return_value=["Partition_key-index"])
    def test_get_contributor_insights_status_for_table_and_indexes(self, get_indexes_mock, describe_mock):

        result = get_contributor_insights_status_for_table_and_indexes(boto3_session=self.session_mock,
                                                                       table_name="my_table")

        self.assertEqual(result, ('ENABLED', [{'IndexName': 'Partition_key-index', 'Status': 'ENABLED'}]))
        describe_mock.assert_has_calls([
            call(boto3_session=self.session_mock,
                 table_name='my_table'),
            call(boto3_session=self.session_mock,
                 table_name='my_table',
                 index_name='Partition_key-index')
        ])

        get_indexes_mock.assert_called_with(boto3_session=self.session_mock,
                                            table_name="my_table")

    def test__describe_continuous_backups(self):

        result = _describe_continuous_backups(boto3_session=self.session_mock,
                                              table_name="my_table")

        self.assertEqual(result, DESCRIBE_CONTINUOUS_BACKUPS_RESPONSE)

    def test__delete_backup(self):

        result = _delete_backup(boto3_session=self.session_mock,
                                backup_arn="arn")

        self.assertEqual(result, DELETE_BACKUP_RESPONSE)

    def test__describe_backup(self):

        result = _describe_backup(boto3_session=self.session_mock,
                                  backup_arn="arn")

        self.assertEqual(result, DESCRIBE_BACKUP_RESPONSE)

    def test__create_backup(self):

        result = _create_backup(boto3_session=self.session_mock,
                                table_name="my_table", backup_name="my_backup")

        self.assertEqual(result, CREATE_BACKUP_RESPONSE)

    @patch('resource_manager.src.util.dynamo_db_utils._get_global_table_all_regions',
           return_value=['my-region-1'])
    def test__check_if_replicas_exist__exists(self, describe_mock):

        replicas, exists = _check_if_replicas_exist(boto3_session=self.session_mock,
                                                    table_name="my_table")

        self.assertTrue(exists)
        self.assertEqual(replicas, ['my-region-1'])
        describe_mock.assert_called_with(boto3_session=self.session_mock,
                                         table_name="my_table")

    @patch('resource_manager.src.util.dynamo_db_utils._describe_table',
           return_value={'Table': {'Replicas': ['my-region-1']}})
    def test__get_global_table_all_regions(self, describe_mock):

        result = _get_global_table_all_regions(boto3_session=self.session_mock,
                                               table_name="my_table")

        self.assertTrue(result)
        describe_mock.assert_called_with(boto3_session=self.session_mock,
                                         table_name="my_table")

    @patch('resource_manager.src.util.dynamo_db_utils._delete_backup',
           return_value={})
    def test__delete_backup_if_exist__exists(self, delete_mock):

        result = _delete_backup_if_exist(boto3_session=self.session_mock,
                                         backup_arn="arn")

        self.assertTrue(result)
        delete_mock.assert_called_with(boto3_session=self.session_mock,
                                       backup_arn="arn")

    @patch('resource_manager.src.util.dynamo_db_utils._delete_backup',
           side_effect=BACKUP_NOT_FOUND_ERROR)
    def test__delete_backup_if_exist__not_exists(self, delete_mock):

        result = _delete_backup_if_exist(boto3_session=self.session_mock,
                                         backup_arn="arn")

        self.assertFalse(result)
        delete_mock.assert_called_with(boto3_session=self.session_mock,
                                       backup_arn="arn")

    @patch('resource_manager.src.util.dynamo_db_utils._delete_backup',
           side_effect=RESOURCE_IN_USE_ERROR)
    def test__delete_backup_if_exist__client_error(self, delete_mock):

        with self.assertRaises(ClientError):
            _delete_backup_if_exist(boto3_session=self.session_mock,
                                    backup_arn="arn")

            delete_mock.assert_called_with(boto3_session=self.session_mock,
                                           backup_arn="arn")

    @patch('resource_manager.src.util.dynamo_db_utils._describe_backup',
           return_value={'BackupDescription': {
               'BackupDetails': {
                   'BackupStatus': 'DELETED'
               }
           }})
    def test__check_if_backup_exists_deleted_status(self, describe_mock):

        result = _check_if_backup_exists(boto3_session=self.session_mock,
                                         backup_arn="arn")
        self.assertFalse(result)
        describe_mock.assert_called_with(boto3_session=self.session_mock,
                                         backup_arn="arn")

    @patch('resource_manager.src.util.dynamo_db_utils._describe_backup',
           side_effect=BACKUP_NOT_FOUND_ERROR)
    def test__check_if_backup_exists_does_not_exist(self, describe_mock):

        result = _check_if_backup_exists(boto3_session=self.session_mock,
                                         backup_arn="arn")
        self.assertFalse(result)
        describe_mock.assert_called_with(boto3_session=self.session_mock,
                                         backup_arn="arn")

    @patch('resource_manager.src.util.dynamo_db_utils._describe_backup',
           side_effect=RESOURCE_IN_USE_ERROR)
    def test__check_if_backup_exists__client_error(self, describe_mock):

        with self.assertRaises(ClientError):
            _check_if_backup_exists(boto3_session=self.session_mock,
                                    backup_arn="arn")
            describe_mock.assert_called_with(boto3_session=self.session_mock,
                                             backup_arn="arn")

    @patch('resource_manager.src.util.dynamo_db_utils._describe_backup',
           return_value={'BackupDescription': {
               'BackupDetails': {
                   'BackupStatus': 'DELETING'
               }
           }})
    def test__check_if_backup_exists__deleting(self, describe_mock):

        result = _check_if_backup_exists(boto3_session=self.session_mock,
                                         backup_arn="arn")
        self.assertTrue(result)
        describe_mock.assert_called_with(boto3_session=self.session_mock,
                                         backup_arn="arn")

    @patch('resource_manager.src.util.dynamo_db_utils._delete_backup_if_exist',
           return_value=True)
    @patch('resource_manager.src.util.dynamo_db_utils._check_if_backup_exists',
           return_value=False)
    def test_delete_backup_and_wait(self, describe_mock, check_mock):

        delete_backup_and_wait(boto3_session=self.session_mock,
                               backup_arn="arn",
                               wait_sec=1,
                               delay_sec=1)

        check_mock.assert_called_with(boto3_session=self.session_mock,
                                      backup_arn="arn")
        describe_mock.assert_called_with(boto3_session=self.session_mock,
                                         backup_arn="arn")

    @patch('resource_manager.src.util.dynamo_db_utils._delete_backup_if_exist',
           return_value=True)
    @patch('resource_manager.src.util.dynamo_db_utils._check_if_backup_exists',
           return_value=True)
    @patch('time.sleep')
    @patch('time.time')
    def test_delete_backup_and_wait__timeout(self, patched_time, patched_sleep, describe_mock, check_mock):
        mock_sleep = MockSleep()
        patched_time.side_effect = mock_sleep.time
        patched_sleep.side_effect = mock_sleep.sleep

        with self.assertRaises(TimeoutError):
            delete_backup_and_wait(boto3_session=self.session_mock,
                                   backup_arn="arn",
                                   wait_sec=1,
                                   delay_sec=1)

            check_mock.assert_called_with(boto3_session=self.session_mock,
                                          backup_arn="arn")
            describe_mock.assert_called_with(boto3_session=self.session_mock,
                                             backup_arn="arn")

    @patch('resource_manager.src.util.dynamo_db_utils._create_backup',
           return_value={'BackupDetails': {'BackupArn': 'arn'}})
    @patch('resource_manager.src.util.dynamo_db_utils._describe_backup',
           return_value={'BackupDescription': {
               'BackupDetails': {
                   'BackupStatus': 'AVAILABLE'
               }
           }})
    def test_create_backup_and_wait_for_active(self, describe_mock, create_mock):

        create_backup_and_wait_for_available(boto3_session=self.session_mock,
                                             table_name="my_table",
                                             backup_name="my_backup",
                                             wait_sec=1,
                                             delay_sec=1)

        create_mock.assert_called_with(boto3_session=self.session_mock,
                                       backup_name='my_backup',
                                       table_name='my_table')
        describe_mock.assert_called_with(boto3_session=self.session_mock,
                                         backup_arn="arn")

    @patch('resource_manager.src.util.dynamo_db_utils._create_backup',
           return_value={'BackupDetails': {'BackupArn': 'arn'}})
    @patch('resource_manager.src.util.dynamo_db_utils._describe_backup',
           return_value={'BackupDescription': {
               'BackupDetails': {
                   'BackupStatus': 'CREATING'
               }
           }})
    @patch('time.sleep')
    @patch('time.time')
    def test_create_backup_and_wait_for_active__timeout(self, patched_time, patched_sleep, describe_mock, create_mock):
        mock_sleep = MockSleep()
        patched_time.side_effect = mock_sleep.time
        patched_sleep.side_effect = mock_sleep.sleep

        with self.assertRaises(TimeoutError):
            create_backup_and_wait_for_available(boto3_session=self.session_mock,
                                                 table_name="my_table",
                                                 backup_name="my_backup",
                                                 wait_sec=1,
                                                 delay_sec=1)

            create_mock.assert_called_with(boto3_session=self.session_mock,
                                           backup_name='my_backup',
                                           table_name='my_table')
            describe_mock.assert_called_with(boto3_session=self.session_mock,
                                             backup_arn="arn")

    @patch('resource_manager.src.util.dynamo_db_utils._describe_table',
           return_value={'Table': {'TableStatus': 'DELETING'}})
    def test__check_if_table_deleted__deleting(self, describe_mock):

        result = _check_if_table_deleted(boto3_session=self.session_mock,
                                         table_name="my_table")

        self.assertFalse(result)

    @patch('resource_manager.src.util.dynamo_db_utils._describe_table',
           side_effect=RESOURCE_NOT_FOUND_ERROR)
    def test__check_if_table_deleted__deleted(self, describe_mock):
        result = _check_if_table_deleted(boto3_session=self.session_mock,
                                         table_name="my_table")

        self.assertTrue(result)

    @patch('resource_manager.src.util.dynamo_db_utils._describe_table',
           return_value={'Table': {'TableStatus:': 'CREATING'}})
    @patch('time.sleep')
    @patch('time.time')
    def test_wait_table_to_be_active_timeout(self, patched_time, patched_sleep, describe_mock):
        mock_sleep = MockSleep()
        patched_time.side_effect = mock_sleep.time
        patched_sleep.side_effect = mock_sleep.sleep
        with self.assertRaises(TimeoutError):
            wait_table_to_be_active(boto3_session=self.session_mock,
                                    table_name="my_table",
                                    wait_sec=1,
                                    delay_sec=1)

        describe_mock.assert_called_with(boto3_session=self.session_mock,
                                         table_name="my_table")

    @patch('resource_manager.src.util.dynamo_db_utils._describe_table',
           return_value={'Table': {'TableStatus': 'ACTIVE'}})
    def test_wait_table_to_be_active(self, describe_mock):
        wait_table_to_be_active(boto3_session=self.session_mock,
                                table_name="my_table",
                                wait_sec=1,
                                delay_sec=1)

        describe_mock.assert_called_with(boto3_session=self.session_mock,
                                         table_name="my_table")

    @patch('resource_manager.src.util.dynamo_db_utils._update_table',
           return_value={})
    @patch('resource_manager.src.util.dynamo_db_utils._describe_table',
           return_value={**DESCRIBE_TABLE_RESPONSE})
    @patch('time.sleep')
    @patch('time.time')
    def test_add_global_table_and_wait_to_active(self, patched_time, patched_sleep, describe_mock, update_mock):
        mock_sleep = MockSleep()
        patched_time.side_effect = mock_sleep.time
        patched_sleep.side_effect = mock_sleep.sleep

        add_global_table_and_wait_for_active(boto3_session=self.session_mock,
                                             table_name="my_table",
                                             global_table_regions=['region-1'],
                                             wait_sec=1,
                                             delay_sec=1,
                                             )

        update_mock.assert_called_with(boto3_session=self.session_mock,
                                       table_name="my_table",
                                       ReplicaUpdates=[{'Create': {'RegionName': 'region-1'}}]
                                       )
        describe_mock.assert_called_with(boto3_session=self.session_mock,
                                         table_name="my_table"
                                         )

    @patch('resource_manager.src.util.dynamo_db_utils._update_table',
           return_value={})
    @patch('resource_manager.src.util.dynamo_db_utils._describe_table',
           return_value={'Table': {
               "TableStatus": "NOT_ACTIVE_YET",
               "Replicas": [
                   {
                       "RegionName": "my_region",
                       "ReplicaStatus": "NOT_ACTIVE_YET"
                   }
               ]}})
    @patch('time.sleep')
    @patch('time.time')
    def test_add_global_table_and_wait_to_active_timeout(self, patched_time, patched_sleep, describe_mock, update_mock):
        mock_sleep = MockSleep()
        patched_time.side_effect = mock_sleep.time
        patched_sleep.side_effect = mock_sleep.sleep
        with self.assertRaises(TimeoutError):
            add_global_table_and_wait_for_active(boto3_session=self.session_mock,
                                                 table_name="my_table",
                                                 global_table_regions=['region-1'],
                                                 wait_sec=1,
                                                 delay_sec=1
                                                 )

            update_mock.assert_called_with(boto3_session=self.session_mock,
                                           table_name="my_table",
                                           ReplicaUpdates=[{'Create': {'RegionName': 'region-1'}}]
                                           )
            describe_mock.assert_called_with(boto3_session=self.session_mock,
                                             table_name="my_table"
                                             )

    @patch('resource_manager.src.util.dynamo_db_utils._describe_continuous_backups',
           return_value=DESCRIBE_CONTINUOUS_BACKUPS_RESPONSE)
    def test_get_earliest_recovery_point_in_time(self, describe_backups_mock):
        result = get_earliest_recovery_point_in_time(boto3_session=self.session_mock,
                                                     table_name="my_table"
                                                     )
        self.assertEqual(result, 'some time')
        describe_backups_mock.assert_called_with(boto3_session=self.session_mock,
                                                 table_name="my_table")

    @patch('resource_manager.src.util.dynamo_db_utils._describe_continuous_backups',
           return_value={})
    def test_get_earliest_recovery_point_in_time__backups_disabled(self, describe_backups_mock):
        with self.assertRaises(ValueError):
            get_earliest_recovery_point_in_time(boto3_session=self.session_mock,
                                                table_name="my_table")
        describe_backups_mock.assert_called_with(boto3_session=self.session_mock,
                                                 table_name="my_table")

    @patch('resource_manager.src.util.dynamo_db_utils._update_table',
           return_value={})
    @patch('resource_manager.src.util.dynamo_db_utils._check_if_replicas_exist',
           side_effect=[(["Replica"], True), (["Replica"], True), ([], False)])
    @patch('resource_manager.src.util.dynamo_db_utils.time.sleep',
           return_value=None)
    def test_remove_global_table_and_wait_to_active(self, time_mock, check_mock, update_mock):
        remove_global_table_and_wait_for_active(boto3_session=self.session_mock,
                                                table_name="my_table",
                                                global_table_regions=['region-1'],
                                                wait_sec=1,
                                                delay_sec=1,
                                                )

        update_mock.assert_called_with(boto3_session=self.session_mock,
                                       table_name="my_table",
                                       ReplicaUpdates=[{'Delete': {'RegionName': 'region-1'}}]
                                       )
        check_mock.assert_called_with(boto3_session=self.session_mock,
                                      table_name="my_table"
                                      )

    @patch('resource_manager.src.util.dynamo_db_utils._update_table',
           side_effect=[ClientError(
                error_response={"Error": {"Code": "ValidationException"}},
                operation_name='UpdateTable'
            ), {}])
    @patch('resource_manager.src.util.dynamo_db_utils._check_if_replicas_exist',
           side_effect=[(["Replica"], True), (["Replica"], True), ([], False)])
    @patch('resource_manager.src.util.dynamo_db_utils.time.sleep',
           return_value=None)
    def test_remove_global_table_and_wait_to_active_busy(self, time_mock, check_mock, update_mock):
        remove_global_table_and_wait_for_active(boto3_session=self.session_mock,
                                                table_name="my_table",
                                                global_table_regions=['region-1'],
                                                wait_sec=1,
                                                delay_sec=1,
                                                )

        update_mock.assert_called_with(boto3_session=self.session_mock,
                                       table_name="my_table",
                                       ReplicaUpdates=[{'Delete': {'RegionName': 'region-1'}}]
                                       )
        check_mock.assert_called_with(boto3_session=self.session_mock,
                                      table_name="my_table"
                                      )

    @patch('resource_manager.src.util.dynamo_db_utils._update_table',
           return_value={})
    @patch('resource_manager.src.util.dynamo_db_utils._check_if_replicas_exist',
           return_value=(["Replica"], True))
    def test_remove_global_table_and_wait_to_active_timeout(self, check_mock, try_remove_mock):
        with self.assertRaises(TimeoutError):
            remove_global_table_and_wait_for_active(boto3_session=self.session_mock,
                                                    table_name="my_table",
                                                    global_table_regions=['region-1'],
                                                    wait_sec=1,
                                                    delay_sec=1,
                                                    )

        try_remove_mock.assert_called_with(boto3_session=self.session_mock,
                                           table_name="my_table",
                                           ReplicaUpdates=[{'Delete': {'RegionName': 'region-1'}}]
                                           )
        check_mock.assert_called_with(boto3_session=self.session_mock,
                                      table_name="my_table"
                                      )

    @patch('resource_manager.src.util.dynamo_db_utils._execute_boto3_dynamodb',
           return_value={})
    @patch('resource_manager.src.util.dynamo_db_utils._check_if_table_deleted',
           return_value=True)
    @patch('resource_manager.src.util.dynamo_db_utils.time.sleep',
           return_value=None)
    def test_drop_and_wait_dynamo_db_table_if_exists(self, time_mock, check_mock, execute_mock):
        drop_and_wait_dynamo_db_table_if_exists(boto3_session=self.session_mock,
                                                table_name="my_table",
                                                wait_sec=1,
                                                delay_sec=1,
                                                )

        execute_mock.assert_called()
        check_mock.assert_called_with(boto3_session=self.session_mock,
                                      table_name="my_table")

    @patch('resource_manager.src.util.dynamo_db_utils._execute_boto3_dynamodb',
           side_effect=RESOURCE_NOT_FOUND_ERROR)
    @patch('resource_manager.src.util.dynamo_db_utils._check_if_table_deleted',
           return_value=True)
    @patch('resource_manager.src.util.dynamo_db_utils.time.sleep',
           return_value=None)
    def test_drop_and_wait_dynamo_db_table_if_exists__not_exists(self, time_mock, check_mock, execute_mock):
        drop_and_wait_dynamo_db_table_if_exists(boto3_session=self.session_mock,
                                                table_name="my_table",
                                                wait_sec=1,
                                                delay_sec=1,
                                                )

        execute_mock.assert_called()
        self.assertFalse(check_mock.called)

    @patch('resource_manager.src.util.dynamo_db_utils._execute_boto3_dynamodb',
           return_value={})
    @patch('resource_manager.src.util.dynamo_db_utils._check_if_table_deleted',
           return_value=False)
    @patch('time.sleep')
    @patch('time.time')
    def test_drop_and_wait_dynamo_db_table_if_exists__timeout(
            self, patched_time, patched_sleep, check_mock, execute_mock):
        mock_sleep = MockSleep()
        patched_time.side_effect = mock_sleep.time
        patched_sleep.side_effect = mock_sleep.sleep

        with self.assertRaises(TimeoutError):
            drop_and_wait_dynamo_db_table_if_exists(boto3_session=self.session_mock,
                                                    table_name="my_table",
                                                    wait_sec=1,
                                                    delay_sec=1,
                                                    )

            execute_mock.assert_called()
            check_mock.assert_called_with(boto3_session=self.session_mock,
                                          table_name="my_table")

    def test_get_item_single(self):
        test_key = {'some_key': 'some_value'}
        get_item_single(boto3_session=self.session_mock, table_name='my_table', key=test_key)
        self.dynamodb_client_mock.get_item.assert_called_with(
            TableName='my_table', Key=test_key, ConsistentRead=True
        )

    @patch('resource_manager.src.util.dynamo_db_utils.get_item_single',
           return_value=False)
    def test_get_item_async_stress_test(self, get_item_mock):
        test_key = {'some_key': 'some_value'}
        get_item_async_stress_test(
            boto3_session=self.session_mock, table_name='my_table', number=10, item=test_key
        )
        self.assertEqual(get_item_mock.call_count, 10)

    def test_get_random_value_s(self):
        output = _get_random_value(STRING, 10)
        self.assertIsInstance(output, str)
        self.assertEqual(10, len(output))

    def test_get_random_value_n(self):
        output = _get_random_value(NUMBER, 10)
        self.assertIsInstance(output, int)
        self.assertLessEqual(len(str(output)), 10)

    def test_get_random_value_b(self):
        output = _get_random_value(BINARY, 10)
        self.assertIsInstance(output, Binary)
        self.assertEqual(10, len(output.value))

    def test_generate_random_item(self):
        output = generate_random_item(self.session_mock, 'table_name')
        self.assertIsInstance(output['id']['S'], str)
        self.assertEqual(5, len(output['id']['S']))
