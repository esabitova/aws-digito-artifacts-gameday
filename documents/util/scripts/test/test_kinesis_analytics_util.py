import unittest
import datetime
from unittest.mock import patch, MagicMock
import pytest

import resource_manager.src.util.boto3_client_factory as client_factory

from documents.util.scripts.src.kinesis_analytics_util import (
    restore_from_latest_snapshot, restore_from_custom_snapshot, verify_snapshot_exists,
    obtain_s3_object_version_id, obtain_conditional_token, get_kda_vpc_security_group)

MOCK_APPLICATION_NAME = 'KinesisAnalyticsFl_ewBYozhsrZPC'
MOCK_SNAPSHOT_NAME_1 = 'Test-KinesisAnalyticsFl_ewBYozhsrZPC-001'
MOCK_OBJECT_VERSION = '4HHNHcbjkCUKQNzdXk.9yRZymlj8CDhz'
MOCK_CONDITIONAL_TOKEN = '9432b6383defc8830c9551c3fa68cf7d'
MOCK_SNAPSHOT_NAME_2 = 'TEST-KinesisAnalyticsFl_ewBYozhsrZPC-0000000000000'
MOCK_BUCKET_ARN = 'arn:aws:s3:::ssm-test-resources-435978235099-us-east-1'
MOCK_BUCKET_KEY = 'kinesis-analytics-app/python-test-sink.zip'
MOCK_STATUS_1 = 'READY'
MOCK_STATUS_2 = 'CREATING'
MOCK_VERSION_ID_1 = 1
MOCK_VERSION_ID_2 = 12
MOCK_EVENTS = {'ApplicationName': MOCK_APPLICATION_NAME,
               'SnapshotName': MOCK_SNAPSHOT_NAME_1}
MOCK_UPDATE_APPLICATION_CONFIGURATION = {
    'ApplicationCodeConfigurationUpdate':
    {'CodeContentUpdate':
        {'S3ContentLocationUpdate':
         {'ObjectVersionUpdate': MOCK_OBJECT_VERSION}}}}
MOCK_UPDATE_RUN_CONFIGURATION_UPDATE = {
    'FlinkRunConfiguration': {'AllowNonRestoredState': True},
    'ApplicationRestoreConfiguration':
    {'ApplicationRestoreType': 'RESTORE_FROM_CUSTOM_SNAPSHOT',
        'SnapshotName': MOCK_SNAPSHOT_NAME_1}}
MOCK_SUBNET_IDS = ['subnet-0cd591fc9f13ec657']
MOCK_SECURITY_GROUP_ID = 'sg-0eff14e557fcb771a'
MOCK_VPC_ID = 'vpc-070c04233a3495dec'
MOCK_VPC_CONFIGURATION_ID = '3.1'


def mock_list_application_snapshots(ApplicationName,
                                    Limit,
                                    snapshot_status_1,
                                    snapshot_status_2):
    return {'SnapshotSummaries':
            [{'SnapshotName': MOCK_SNAPSHOT_NAME_1,
              'SnapshotStatus': snapshot_status_1,
              'ApplicationVersionId': MOCK_VERSION_ID_1,
              'SnapshotCreationTimestamp': datetime.datetime(2021, 8, 3, 14, 26, 21)},
             {'SnapshotName': MOCK_SNAPSHOT_NAME_2,
              'SnapshotStatus': snapshot_status_2,
              'ApplicationVersionId': MOCK_VERSION_ID_2,
              'SnapshotCreationTimestamp': datetime.datetime(2021, 8, 4, 9, 2, 32)}]}


def mock_zero_list_application_snapshots(ApplicationName,
                                         Limit):
    return {'SnapshotSummaries': []}


def mock_describe_application_snapshot(ApplicationName,
                                       SnapshotName,
                                       snapshot_status,
                                       status_code):
    return {'SnapshotDetails':
            {'SnapshotName': SnapshotName,
             'SnapshotStatus': snapshot_status,
             'ApplicationVersionId': MOCK_VERSION_ID_1,
             'SnapshotCreationTimestamp': datetime.datetime(2021, 8, 4, 21, 31, 53)},
            'ResponseMetadata':
            {'RequestId': '358abd39-3faf-48f8-a2cd-b066d8fba962',
             'HTTPStatusCode': status_code,
             'HTTPHeaders':
             {'x-amzn-requestid': '358abd39-3faf-48f8-a2cd-b066d8fba962',
              'content-type': 'application/x-amz-json-1.1',
              'content-length': '136',
              'date': 'Tue, 03 Aug 2021 11:26:23 GMT'},
             'RetryAttempts': 0}}


def mock_describe_application(ApplicationName, IncludeAdditionalDetails, status_code):
    return {'ApplicationDetail':
            {'ApplicationConfigurationDescription':
             {'VpcConfigurationDescriptions':
              [{'VpcConfigurationId': MOCK_VPC_CONFIGURATION_ID,
                'VpcId': MOCK_VPC_ID,
                'SubnetIds': MOCK_SUBNET_IDS,
                'SecurityGroupIds': [MOCK_SECURITY_GROUP_ID]}],
              'ApplicationCodeConfigurationDescription':
              {'CodeContentDescription':
               {'S3ApplicationCodeLocationDescription':
                {'BucketARN': MOCK_BUCKET_ARN,
                 'FileKey': MOCK_BUCKET_KEY}}}},
             'ConditionalToken': MOCK_CONDITIONAL_TOKEN},
            'ResponseMetadata': {'HTTPStatusCode': status_code}}


def mock_update_application(ApplicationName,
                            ConditionalToken,
                            ApplicationConfigurationUpdate,
                            RunConfigurationUpdate,
                            status_code):
    return {'ResponseMetadata': {'HTTPStatusCode': status_code}}


@pytest.mark.unit_test
class TestKinesisAnalyticsUtil(unittest.TestCase):

    def setUp(self):
        self.mock_kinesis_analytics = MagicMock()
        self.mock_s3 = MagicMock()
        self.mock_client = MagicMock()
        self.config = MagicMock()
        self.client_side_effect_map = {
            'kinesisanalyticsv2': self.mock_kinesis_analytics,
            's3': self.mock_s3
        }
        self.mock_client.side_effect = lambda service_name, config=None: \
            self.client_side_effect_map.get(service_name)
        self.mock_kinesis_analytics.describe_application.side_effect = lambda ApplicationName, \
            IncludeAdditionalDetails=True: \
            mock_describe_application(ApplicationName, True, 200)
        self.mock_s3.get_object.side_effect = lambda Bucket, Key: \
            {'VersionId': MOCK_OBJECT_VERSION}

    def tearDown(self):
        client_factory.clients = {}
        client_factory.resources = {}

    def test_restore_from_latest_snapshot_invalid_event_parameters(self):
        """
        test restore_from_latest_snapshot() foo under:
        - invalid input parameters
        """
        MOCK_FAULT_EVENTS = {'SnapshotName': MOCK_SNAPSHOT_NAME_1}
        with self.assertRaises(Exception):
            restore_from_latest_snapshot(MOCK_FAULT_EVENTS, None)

    def test_restore_from_custom_snapshot_invalid_event_parameters(self):
        """
        test restore_from_latest_snapshot() foo under:
        - invalid input parameters
        """
        MOCK_FAULT_EVENTS = {'SnapshotName': MOCK_SNAPSHOT_NAME_1}
        with self.assertRaises(Exception):
            restore_from_custom_snapshot(MOCK_FAULT_EVENTS, None)

    @patch('documents.util.scripts.src.kinesis_analytics_util.boto3')
    @patch('documents.util.scripts.src.kinesis_analytics_util.Config')
    def test_restore_from_latest_snapshot_correct_event_parameters(self, mock_config, mock_boto3):
        """
        test restore_from_latest_snapshot() foo under:
        - invalid input parameters
        """
        MOCK_EVENTS_RESTORE = {'ApplicationName': MOCK_APPLICATION_NAME,
                               'SnapshotName': 'LATEST',
                               'ObjectVersionId': MOCK_OBJECT_VERSION,
                               'ConditionalToken': MOCK_CONDITIONAL_TOKEN}
        mock_config.side_effect = lambda retries: self.config
        mock_boto3.client = self.mock_client
        mock_kda_client = self.mock_client('kinesisanalyticsv2', config=self.config)
        mock_kda_client.update_application.side_effect = lambda \
            ApplicationName, ConditionalToken, ApplicationConfigurationUpdate,\
            RunConfigurationUpdate, status_code=200:\
            mock_update_application(
                ApplicationName, ConditionalToken, ApplicationConfigurationUpdate,
                RunConfigurationUpdate, status_code)
        self.assertEqual(200, restore_from_latest_snapshot(MOCK_EVENTS_RESTORE, {}))

    @patch('documents.util.scripts.src.kinesis_analytics_util.boto3')
    @patch('documents.util.scripts.src.kinesis_analytics_util.Config')
    def test_restore_from_custom_snapshot_correct_event_parameters(self, mock_config, mock_boto3):
        """
        test restore_from_latest_snapshot() foo under:
        - invalid input parameters
        """
        MOCK_EVENTS_RESTORE = {'ApplicationName': MOCK_APPLICATION_NAME,
                               'SnapshotName': MOCK_SNAPSHOT_NAME_1,
                               'ObjectVersionId': MOCK_OBJECT_VERSION,
                               'ConditionalToken': MOCK_CONDITIONAL_TOKEN}
        mock_config.side_effect = lambda retries: self.config
        mock_boto3.client = self.mock_client
        mock_kda_client = self.mock_client('kinesisanalyticsv2', config=self.config)
        mock_kda_client.update_application.side_effect = lambda \
            ApplicationName, ConditionalToken, ApplicationConfigurationUpdate,\
            RunConfigurationUpdate, status_code=200:\
            mock_update_application(
                ApplicationName, ConditionalToken, ApplicationConfigurationUpdate,
                RunConfigurationUpdate, status_code)
        self.assertEqual(200, restore_from_custom_snapshot(MOCK_EVENTS_RESTORE, {}))

    @patch('documents.util.scripts.src.kinesis_analytics_util.boto3')
    @patch('documents.util.scripts.src.kinesis_analytics_util.Config')
    def test_verify_latest_snapshot_exists(self, mock_config, mock_boto3):
        """
        test verify_snapshot_exists
        """
        mock_config.side_effect = lambda retries: self.config
        mock_boto3.client = self.mock_client
        mock_events = {'SnapshotName': 'LATEST', 'ApplicationName': MOCK_APPLICATION_NAME}
        mock_kda_client = self.mock_client('kinesisanalyticsv2', config=self.config)
        mock_kda_client.list_application_snapshots.side_effect = lambda ApplicationName, Limit, \
            snapshot_status_1=MOCK_STATUS_1, snapshot_status_2=MOCK_STATUS_2: \
            mock_list_application_snapshots(ApplicationName, Limit, snapshot_status_1, snapshot_status_2)
        mock_kda_client.describe_application_snapshot.side_effect = lambda ApplicationName, SnapshotName, \
            snapshot_status=MOCK_STATUS_1, status_code = 200: \
            mock_describe_application_snapshot(ApplicationName, SnapshotName, snapshot_status, status_code)
        self.assertEqual(verify_snapshot_exists(mock_events, {}), "READY")

    @patch('documents.util.scripts.src.kinesis_analytics_util.boto3')
    @patch('documents.util.scripts.src.kinesis_analytics_util.Config')
    def test_verify_custom_snapshot_exists(self, mock_config, mock_boto3):
        """
        test verify_snapshot_exists()
        """
        mock_config.side_effect = lambda retries: self.config
        mock_boto3.client = self.mock_client
        mock_kda_client = self.mock_client('kinesisanalyticsv2', config=self.config)
        mock_kda_client.describe_application_snapshot.side_effect = lambda ApplicationName, SnapshotName, \
            snapshot_status=MOCK_STATUS_1, status_code = 200: \
            mock_describe_application_snapshot(ApplicationName, SnapshotName, snapshot_status, status_code)
        self.assertEqual(verify_snapshot_exists(MOCK_EVENTS, {}), "READY")

    @patch('documents.util.scripts.src.kinesis_analytics_util.boto3')
    @patch('documents.util.scripts.src.kinesis_analytics_util.Config')
    def test_obtain_s3_object_version_id(self, mock_config, mock_boto3):
        """
        test obtain_s3_object_version_id()
        """
        mock_config.side_effect = lambda retries: self.config
        mock_boto3.client = self.mock_client
        self.assertEqual(obtain_s3_object_version_id(MOCK_EVENTS, {})['VersionId'], MOCK_OBJECT_VERSION)

    @patch('documents.util.scripts.src.kinesis_analytics_util.boto3')
    @patch('documents.util.scripts.src.kinesis_analytics_util.Config')
    def test_obtain_conditional_token(self, mock_config, mock_boto3):
        """
        test obtain_conditional_token()
        """
        mock_config.side_effect = lambda retries: self.config
        mock_boto3.client = self.mock_client
        self.assertEqual(MOCK_CONDITIONAL_TOKEN, obtain_conditional_token(MOCK_EVENTS, {}))

    @patch('documents.util.scripts.src.kinesis_analytics_util.boto3')
    @patch('documents.util.scripts.src.kinesis_analytics_util.Config')
    def test_restore_from_latest_snapshot_fail_execution_existent_snapshot_faulty_snapshot_status(self,
                                                                                                  mock_config,
                                                                                                  mock_boto3):
        """
        test restore_from_latest_snapshot() foo under:
        - valid input parameters
        - snapshot exist - EXISTENT snapshot case
        - snapshot status NOT "READY'
        - i.e. this is a fail-style pipeline
        """
        mock_config.side_effect = lambda retries: self.config
        mock_boto3.client = self.mock_client
        self.mock_kinesis_analytics.describe_application_snapshot.side_effect = lambda ApplicationName, SnapshotName, \
            snapshot_status=MOCK_STATUS_2, status_code = 200: \
            mock_describe_application_snapshot(ApplicationName, SnapshotName, snapshot_status, status_code)
        # Test and assert:
        with self.assertRaises(Exception):
            restore_from_latest_snapshot(MOCK_EVENTS, None)

    @patch('documents.util.scripts.src.kinesis_analytics_util.boto3')
    @patch('documents.util.scripts.src.kinesis_analytics_util.Config')
    def test_restore_from_custom_snapshot_fail_execution_existent_snapshot_faulty_snapshot_status(self,
                                                                                                  mock_config,
                                                                                                  mock_boto3):
        """
        test restore_from_custom_snapshot() foo under:
        - valid input parameters
        - snapshot exist - EXISTENT snapshot case
        - snapshot status NOT "READY'
        - i.e. this is a fail-style pipeline
        """
        mock_config.side_effect = lambda retries: self.config
        mock_boto3.client = self.mock_client
        self.mock_kinesis_analytics.describe_application_snapshot.side_effect = lambda ApplicationName, SnapshotName, \
            snapshot_status=MOCK_STATUS_2, status_code = 200: \
            mock_describe_application_snapshot(ApplicationName, SnapshotName, snapshot_status, status_code)
        # Test and assert:
        with self.assertRaises(Exception):
            restore_from_custom_snapshot(MOCK_EVENTS, None)

    @patch('documents.util.scripts.src.kinesis_analytics_util.boto3')
    @patch('documents.util.scripts.src.kinesis_analytics_util.Config')
    def test_get_kda_vpc_security_group(self, mock_config, mock_boto3):
        """
        test get_kda_vpc_security_group
        """
        mock_config.side_effect = lambda retries: self.config
        mock_boto3.client = self.mock_client
        ttemp = "KinesisDataAnalyticsApplicationVPCSecurityGroupMappingOriginalValue"
        self.assertEqual(MOCK_SECURITY_GROUP_ID, get_kda_vpc_security_group(MOCK_EVENTS, {})[ttemp])
