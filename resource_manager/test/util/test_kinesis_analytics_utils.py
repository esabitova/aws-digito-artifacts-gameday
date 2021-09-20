from datetime import datetime
import logging

import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

import resource_manager.src.util.boto3_client_factory as client_factory
import resource_manager.src.util.kinesis_analytics_utils as kinan_utils

TEST_APPLICATION_NAME = 'KinesisAnalyticsFl_Ve6KhqPQMAxk'
TEST_APP_TYPE_SQL = 'SQL'
TEST_APP_TYPE_FLINK = 'Apache Flink'
TEST_INPUT_ID = '1.1'
TEST_INPUT_STREAM = "KinesisAnalyticsTemplateFlink-ON-DEMAND-0-InputKinesisStream-0Ui8aSw19ky8"
TEST_SEC_INTERVAL = 0.2
TEST_SLEEP_INTERVAL = 0.05
TEST_WAIT_TO_START = 0.1
TEST_INTERVAL_AMONG_STREAM_RECORDS = 0.05
TEST_SNAPSHOT_NAME = 'Test-KinesisAnalyticsFl_ewBYozhsrZPC-001'
MOCK_SNAPSHOTS_NAMES_LIST = ['Test-KinesisAnalyticsFl_ewBYozhsrZPC-001', 'MyFirstSnapshot',
                             'MySecondSnapshot']


def mock_describe_flink_application(ApplicationName, mock_status):
    return {'ApplicationDetail':
            {'ApplicationName': ApplicationName,
             'ApplicationStatus': mock_status,
             'ApplicationConfigurationDescription':
             {'EnvironmentPropertyDescriptions':
              {'PropertyGroupDescriptions':
               [{},
                {'PropertyGroupId': 'producer.config.0',
                 'PropertyMap':
                 {'aws.region': 'us-east-1',
                  'output.stream.name': 'OutputStreamFlink'}},
                {'PropertyGroupId': 'consumer.config.0',
                 'PropertyMap':
                 {'aws.region': 'us-east-1',
                  'flink.stream.initpos': 'LATEST',
                  'input.stream.name': 'InputStreamFlink'}}]},
              'RunConfigurationDescription':
              {'ApplicationRestoreConfigurationDescription':
               {"ApplicationRestoreType": "SKIP_RESTORE_FROM_SNAPSHOT",
                'SnapshotName': TEST_SNAPSHOT_NAME}}}},
            'ResponseMetadata': {'HTTPStatusCode': 200}}


def mock_describe_sql_application(ApplicationName, mock_status):
    return {'ApplicationDetail':
            {'ApplicationName': ApplicationName,
             'ApplicationStatus': mock_status,
             'ApplicationConfigurationDescription':
             {'SqlApplicationConfigurationDescription':
              {'InputDescriptions':
               [{'InputId': '1.1',
                 'NamePrefix': 'DEMO_SOURCE_SQL_STREAM',
                 'InAppStreamNames': ['DEMO_SOURCE_SQL_STREAM_001']}],
               'OutputDescriptions':
               [{'OutputId': '2.1',
                 'Name': 'DESTINATION_SQL_STREAM'}]}}},
            'ResponseMetadata': {'HTTPStatusCode': 200}}


def mock_start_application(ApplicationName, RunConfiguration, status_code):
    logging.info(f"ApplicationName: {ApplicationName}")
    logging.info(f"RunConfiguration: {RunConfiguration}")
    return {'ResponseMetadata': {'HTTPStatusCode': status_code}}


def status_gen(status_list: tuple):
    i = 0
    while True:
        yield status_list[i]
        i += 1


def mock_stop_application(ApplicationName, app_status, Force=None):
    logging.info(f"ApplicationName: {ApplicationName}")
    logging.info(f"Force: {Force}")
    return {'ResponseMetadata': {'HTTPStatusCode': app_status}}


def mock_list_application_snapshots(ApplicationName, Limit, status_code):
    return {'SnapshotSummaries':
            [{'SnapshotName': 'Test-KinesisAnalyticsFl_ewBYozhsrZPC-001',
              'SnapshotStatus': 'READY',
              'ApplicationVersionId': 1},
             {'SnapshotName': 'MyFirstSnapshot',
              'SnapshotStatus': 'READY',
              'ApplicationVersionId': 1},
             {'SnapshotName': 'MySecondSnapshot',
              'SnapshotStatus': 'READY',
              'ApplicationVersionId': 1}],
            'ResponseMetadata': {'HTTPStatusCode': status_code}}


@pytest.mark.unit_test
class KinesisAnalyticsTestUtils(unittest.TestCase):

    def setUp(self):
        self.session_mock = MagicMock()
        self.mock_kinesis = MagicMock()
        self.put_records = MagicMock()
        self.put_record = MagicMock()
        self.mock_kinesis_analytics = MagicMock()
        # next mock is for kinesis (stream) methods - NOT for kinesis analytics methods
        self.mock_kinesis_methods_effect_map = {
            'put_records': self.put_records,
            'put_record': self.put_record
        }
        self.client_side_effect_map = {
            'kinesisanalyticsv2': self.mock_kinesis_analytics,
            'kinesis': self.mock_kinesis,
        }
        self.session_mock.client.side_effect = lambda service_name, config=None: \
            self.client_side_effect_map.get(service_name)

    def tearDown(self):
        client_factory.clients = {}
        client_factory.resources = {}

    @patch('resource_manager.src.util.kinesis_analytics_utils.random')
    def test__get_hotspot(self, mock_random):
        mock_test_field = {'left': 0, 'width': 10, 'top': 0, 'height': 10}
        mock_hotspot_size = 1
        mock_random.random.side_effect = lambda: 0.8
        self.assertTrue(0 < kinan_utils._get_hotspot(mock_test_field, mock_hotspot_size)['left'] <= 10)
        self.assertTrue(0 < kinan_utils._get_hotspot(mock_test_field, mock_hotspot_size)['width'] <= 10)
        self.assertTrue(0 < kinan_utils._get_hotspot(mock_test_field, mock_hotspot_size)['top'] <= 10)
        self.assertTrue(0 < kinan_utils._get_hotspot(mock_test_field, mock_hotspot_size)['height'] <= 10)

    @patch('resource_manager.src.util.kinesis_analytics_utils.random')
    def test__get_record(self, mock_random):
        mock_test_field = {'left': 0, 'width': 10, 'top': 0, 'height': 10}
        mock_random.random.side_effect = lambda: 0.8
        mock_hotspot_weight = 0.2
        hotspot = None
        self.assertEqual(kinan_utils._get_record(mock_test_field, hotspot, mock_hotspot_weight),
                         {'Data': '{"x": 8.0, "y": 8.0, "is_hot": "N"}', 'PartitionKey': 'partition_key'})
        hotspot = {'left': 4.0, 'width': 1.0, 'top': 3.2, 'height': 1.0}
        mock_hotspot_weight = 0.9
        self.assertEqual(kinan_utils._get_record(mock_test_field, hotspot, mock_hotspot_weight),
                         {'Data': '{"x": 4.8, "y": 4.0, "is_hot": "Y"}', 'PartitionKey': 'partition_key'})

    @patch('resource_manager.src.util.kinesis_analytics_utils.random')
    @patch('resource_manager.src.util.kinesis_analytics_utils.datetime')
    def test__get_ticker_data(self, mock_datetime, mock_random):
        temp = datetime.strptime('Jun 1 2021  1:33PM', '%b %d %Y %I:%M%p')
        mock_random.random.side_effect = lambda: 0.6565
        mock_random.choice.side_effect = lambda x: x[0]
        mock_datetime.utcnow.side_effect = lambda: temp
        self.assertEqual(kinan_utils._get_ticker_data(), {'event_time': mock_datetime.utcnow().isoformat(),
                                                          'ticker': 'AAPL',
                                                          'price': 65.65})

    @patch('resource_manager.src.util.kinesis_analytics_utils.random')
    def test_generate_ml_stream(self, mock_random):
        mock_random.random.side_effect = lambda: 0.8
        self.mock_kinesis.put_records.side_effect = lambda StreamName, Records: \
            self.mock_kinesis_methods_effect_map.get('put_records')
        kinan_utils.generate_ml_stream(TEST_INPUT_STREAM,
                                       TEST_SEC_INTERVAL,
                                       self.session_mock,
                                       interval_among_stream_records=TEST_INTERVAL_AMONG_STREAM_RECORDS)
        self.assertTrue(int(TEST_SEC_INTERVAL / TEST_INTERVAL_AMONG_STREAM_RECORDS) - 1
                        <= self.mock_kinesis.put_records.call_count
                        <= int(TEST_SEC_INTERVAL / TEST_INTERVAL_AMONG_STREAM_RECORDS))

    @patch('resource_manager.src.util.kinesis_analytics_utils.random')
    @patch('resource_manager.src.util.kinesis_analytics_utils.json')
    def test_generate_dummy_ticker_stream(self, mock_json, mock_random):
        mock_random.random.side_effect = lambda: 0.834
        mock_json.dumps.side_effect = lambda x: '2005-06-01T13:33:00'
        self.mock_kinesis.put_record.side_effect = lambda StreamName, Data, PartitionKey: \
            self.mock_kinesis_methods_effect_map.get('put_record')
        kinan_utils.generate_dummy_ticker_stream(TEST_INPUT_STREAM,
                                                 TEST_SEC_INTERVAL,
                                                 self.session_mock,
                                                 interval_among_stream_records=TEST_INTERVAL_AMONG_STREAM_RECORDS)
        self.assertEqual(self.mock_kinesis.put_record.call_count,
                         int(TEST_SEC_INTERVAL / TEST_INTERVAL_AMONG_STREAM_RECORDS))

    @patch('resource_manager.src.util.kinesis_analytics_utils.random')
    @patch('resource_manager.src.util.kinesis_analytics_utils.json')
    def test_produce_dummy_ticker_stream_records(self, mock_json, mock_random):
        mock_random.random.side_effect = lambda: 0.834
        mock_json.dumps.side_effect = lambda x: '2005-06-01T13:33:00'
        self.mock_kinesis.put_record.side_effect = lambda StreamName, Data, PartitionKey: \
            self.mock_kinesis_methods_effect_map.get('put_record')
        kinan_utils.produce_dummy_ticker_stream_records(TEST_INPUT_STREAM,
                                                        self.session_mock,
                                                        3,
                                                        TEST_INTERVAL_AMONG_STREAM_RECORDS)
        self.assertEqual(self.mock_kinesis.put_record.call_count, 3)

    def test_cache_kinan_app_seperate_flink_sql(self):
        # test SQL application type:
        self.mock_kinesis_analytics.describe_application.side_effect = lambda ApplicationName: \
            mock_describe_sql_application(ApplicationName, 'RUNNING')
        sql_inp_id, sql_output_id = kinan_utils.cache_kinan_app_seperate_flink_sql(
            application_name=TEST_APPLICATION_NAME, app_type=TEST_APP_TYPE_SQL, session=self.session_mock)
        # test Flink application type:
        self.mock_kinesis_analytics.describe_application.side_effect = lambda ApplicationName: \
            mock_describe_flink_application(ApplicationName, 'RUNNING')
        sql_inp_id, sql_output_id = kinan_utils.cache_kinan_app_seperate_flink_sql(
            application_name=TEST_APPLICATION_NAME, app_type=TEST_APP_TYPE_FLINK, session=self.session_mock)
        # test incorrect application type:
        with self.assertRaises(KeyError):
            flink_inp_id, flink_output_id = kinan_utils.cache_kinan_app_seperate_flink_sql(
                application_name=TEST_APPLICATION_NAME, app_type='Zeppelin', session=self.session_mock)

    def test_start_kinesis_analytics_app_test_running(self):
        self.mock_kinesis_analytics.start_application.side_effect = lambda ApplicationName, RunConfiguration: 1
        # test status 'RUNNING':
        self.mock_kinesis_analytics.describe_application.side_effect = lambda ApplicationName: \
            mock_describe_flink_application(ApplicationName, 'RUNNING')
        kinan_utils.start_kinesis_analytics_app(application_name=TEST_APPLICATION_NAME,
                                                input_id=TEST_INPUT_ID,
                                                app_type=TEST_APP_TYPE_FLINK,
                                                session=self.session_mock,
                                                sleep_interval=TEST_SLEEP_INTERVAL,
                                                wait_to_start=TEST_WAIT_TO_START)
        self.mock_kinesis_analytics.start_application.assert_not_called()

    def test_start_kinesis_analytics_app_test_ready_sql(self):
        # test status 'READY' for SQL application:
        start_with_delay_generator = status_gen(('READY', 'STARTING', 'STARTING', 'RUNNING', 'RUNNING', 'RUNNING'))
        self.mock_kinesis_analytics.start_application.side_effect = lambda ApplicationName, RunConfiguration: \
            mock_start_application(ApplicationName, RunConfiguration, 200)
        self.mock_kinesis_analytics.describe_application.side_effect = lambda ApplicationName: \
            mock_describe_flink_application(ApplicationName, next(start_with_delay_generator))
        kinan_utils.start_kinesis_analytics_app(application_name=TEST_APPLICATION_NAME,
                                                input_id=TEST_INPUT_ID,
                                                app_type=TEST_APP_TYPE_SQL,
                                                session=self.session_mock,
                                                sleep_interval=TEST_SLEEP_INTERVAL,
                                                wait_to_start=3 * TEST_WAIT_TO_START)
        self.assertEqual(self.mock_kinesis_analytics.start_application.call_count, 1)

    def test_start_kinesis_analytics_app_test_ready_flink(self):
        # test status 'READY' for Flink application:
        start_with_delay_generator = status_gen(('READY', 'STARTING', 'STARTING', 'RUNNING', 'RUNNING', 'RUNNING'))
        self.mock_kinesis_analytics.start_application.side_effect = lambda ApplicationName, RunConfiguration: \
            mock_start_application(ApplicationName, RunConfiguration, 200)
        self.mock_kinesis_analytics.describe_application.side_effect = lambda ApplicationName: \
            mock_describe_flink_application(ApplicationName, next(start_with_delay_generator))
        kinan_utils.start_kinesis_analytics_app(application_name=TEST_APPLICATION_NAME,
                                                input_id=TEST_INPUT_ID,
                                                app_type=TEST_APP_TYPE_FLINK,
                                                session=self.session_mock,
                                                sleep_interval=TEST_SLEEP_INTERVAL,
                                                wait_to_start=3 * TEST_WAIT_TO_START)
        self.assertEqual(self.mock_kinesis_analytics.start_application.call_count, 1)

    def test_start_kinesis_analytics_app_test_no_other_app(self):
        # test only SQL and Flink apps:
        self.mock_kinesis_analytics.describe_application.side_effect = lambda ApplicationName: \
            mock_describe_flink_application(ApplicationName, 'READY')
        with self.assertRaises(KeyError):
            kinan_utils.start_kinesis_analytics_app(application_name=TEST_APPLICATION_NAME,
                                                    input_id=TEST_INPUT_ID,
                                                    app_type='Zeppelin',
                                                    session=self.session_mock,
                                                    sleep_interval=TEST_SLEEP_INTERVAL,
                                                    wait_to_start=TEST_WAIT_TO_START)

    def test_start_kinesis_analytics_app_test_other_status(self):
        # test other status:
        self.mock_kinesis_analytics.describe_application.side_effect = lambda ApplicationName: \
            mock_describe_flink_application(ApplicationName, 'UPDATING')
        with self.assertRaises(RuntimeError):
            kinan_utils.start_kinesis_analytics_app(application_name=TEST_APPLICATION_NAME,
                                                    input_id=TEST_INPUT_ID,
                                                    app_type=TEST_APP_TYPE_FLINK,
                                                    session=self.session_mock,
                                                    sleep_interval=TEST_SLEEP_INTERVAL,
                                                    wait_to_start=TEST_WAIT_TO_START)

    def test_stop_kinesis_analytics_app_norm(self):
        # test normal stop:
        stop_status_generator = status_gen(('RUNNING', 'STOPPING'))
        self.mock_kinesis_analytics.stop_application.side_effect = lambda ApplicationName, Force=None:\
            mock_stop_application(ApplicationName, Force, 200)
        self.mock_kinesis_analytics.describe_application.side_effect = lambda ApplicationName: \
            mock_describe_flink_application(ApplicationName, next(stop_status_generator))
        kinan_utils.stop_kinesis_analytics_app(app_name=TEST_APPLICATION_NAME,
                                               session=self.session_mock,
                                               sleep_interval=0.05)
        self.mock_kinesis_analytics.stop_application.assert_called_once()

    def test_stop_kinesis_analytics_app_force(self):
        # force stop test:
        force_stop_status_generator = status_gen(('RUNNING', 'RUNNING', 'RUNNING', 'RUNNING', 'STOPPING'))
        self.mock_kinesis_analytics.stop_application.side_effect = lambda ApplicationName, Force=None:\
            mock_stop_application(ApplicationName, Force, 200)
        self.mock_kinesis_analytics.describe_application.side_effect = lambda ApplicationName: \
            mock_describe_flink_application(ApplicationName, next(force_stop_status_generator))
        kinan_utils.stop_kinesis_analytics_app(app_name=TEST_APPLICATION_NAME,
                                               session=self.session_mock,
                                               sleep_interval=TEST_SLEEP_INTERVAL)
        self.assertEqual(self.mock_kinesis_analytics.stop_application.call_count, 4)

    def test_stop_kinesis_analytics_app_warn_force_failed(self):
        # unsuccessful force stop: warning
        self.mock_kinesis_analytics.stop_application.side_effect = lambda ApplicationName, Force=None:\
            mock_stop_application(ApplicationName, Force, 200)
        self.mock_kinesis_analytics.describe_application.side_effect = lambda ApplicationName: \
            mock_describe_flink_application(ApplicationName, 'RUNNING')
        kinan_utils.stop_kinesis_analytics_app(app_name=TEST_APPLICATION_NAME,
                                               session=self.session_mock,
                                               sleep_interval=TEST_SLEEP_INTERVAL)
        self.assertEqual(self.mock_kinesis_analytics.stop_application.call_count, 6)

    def test_stop_kinesis_analytics_app_warn_initial_status_not_running(self):
        # initial status not running:
        self.mock_kinesis_analytics.stop_application.side_effect = lambda ApplicationName, Force=None:\
            mock_stop_application(ApplicationName, Force, 200)
        self.mock_kinesis_analytics.describe_application.side_effect = lambda ApplicationName: \
            mock_describe_flink_application(ApplicationName, 'UPDATING')
        kinan_utils.stop_kinesis_analytics_app(app_name=TEST_APPLICATION_NAME,
                                               session=self.session_mock,
                                               sleep_interval=TEST_SLEEP_INTERVAL)
        self.mock_kinesis_analytics.stop_application.assert_not_called()

    def test_cache_kinan_app_snapshpots_list(self):
        self.mock_kinesis_analytics.list_application_snapshots = lambda ApplicationName,\
            Limit=kinan_utils.SNAPSHOTS_QUOTA, status_code=200: mock_list_application_snapshots(
                ApplicationName, Limit, status_code)
        testresult = kinan_utils.cache_kinan_app_snapshpots_list(app_name=TEST_APPLICATION_NAME,
                                                                 session=self.session_mock)
        self.assertEqual(testresult, MOCK_SNAPSHOTS_NAMES_LIST)

    def test_provide_test_snapshot_name(self):
        self.assertEqual(kinan_utils.provide_test_snapshot_name(
            TEST_APPLICATION_NAME, TEST_SNAPSHOT_NAME), TEST_SNAPSHOT_NAME)

    def test_extract_running_app_snapshot_name(self):
        self.mock_kinesis_analytics.describe_application.side_effect = lambda ApplicationName,\
            IncludeAdditionalDetails=True: mock_describe_flink_application(ApplicationName, 'RUNNING')
        self.assertEqual(kinan_utils.extract_running_app_snapshot_name(
            TEST_APPLICATION_NAME, self.session_mock), TEST_SNAPSHOT_NAME)

    def test_provide_latest_snapshot(self):
        self.mock_kinesis_analytics.list_application_snapshots = lambda ApplicationName,\
            Limit=kinan_utils.SNAPSHOTS_QUOTA, status_code=200: mock_list_application_snapshots(
                ApplicationName, Limit, status_code)
        testresult = kinan_utils.provide_latest_snapshot(TEST_APPLICATION_NAME, self.session_mock)
        self.assertEqual(testresult, 'MySecondSnapshot')

    def test_extract_running_app_status_code(self):
        self.mock_kinesis_analytics.describe_application.side_effect = lambda ApplicationName,\
            IncludeAdditionalDetails=True: mock_describe_flink_application(ApplicationName, 'RUNNING')
        self.assertEqual(
            kinan_utils.extract_running_app_status_code(TEST_APPLICATION_NAME, self.session_mock), '200')

    def test_extract_restore_type(self):
        self.mock_kinesis_analytics.describe_application.side_effect = lambda ApplicationName,\
            IncludeAdditionalDetails=True: mock_describe_flink_application(ApplicationName, 'RUNNING')
        self.assertEqual(
            kinan_utils.extract_restore_type(TEST_APPLICATION_NAME, self.session_mock),
            "SKIP_RESTORE_FROM_SNAPSHOT")

    def test_prove_snapshot_exist_or_confect_snapshot_exists(self):
        """
        test prove_snapshot_exist_or_confect if snapshot exists
        """
        self.mock_kinesis_analytics.list_application_snapshots = lambda ApplicationName,\
            Limit=kinan_utils.SNAPSHOTS_QUOTA, status_code=200: mock_list_application_snapshots(
                ApplicationName, Limit, status_code)
        self.assertEqual(kinan_utils.prove_snapshot_exist_or_confect(
            TEST_APPLICATION_NAME, TEST_SNAPSHOT_NAME, self.session_mock), (False, None))

    def test_prove_snapshot_exist_or_confect_latest(self):
        """
        test prove_snapshot_exist_or_confect if snapshot exists
        """
        self.mock_kinesis_analytics.list_application_snapshots = lambda ApplicationName,\
            Limit=kinan_utils.SNAPSHOTS_QUOTA, status_code=200: mock_list_application_snapshots(
                ApplicationName, Limit, status_code)
        self.assertEqual(kinan_utils.prove_snapshot_exist_or_confect(
            TEST_APPLICATION_NAME, 'Latest', self.session_mock), (False, None))

    def test_prove_snapshot_exist_or_confect_new_one_ok(self):
        """
        test prove_snapshot_exist_or_confect if snapshot exists
        """
        self.mock_kinesis_analytics.list_application_snapshots = lambda ApplicationName,\
            Limit=kinan_utils.SNAPSHOTS_QUOTA, status_code=200: mock_list_application_snapshots(
                ApplicationName, Limit, status_code)
        self.mock_kinesis_analytics.create_application_snapshot.side_effect = lambda \
            ApplicationName, SnapshotName: {'ResponseMetadata': {'HTTPStatusCode': 200}}
        self.assertEqual(kinan_utils.prove_snapshot_exist_or_confect(
            TEST_APPLICATION_NAME, 'NoSuchSnapshot', self.session_mock),
            (True, 'NoSuchSnapshot'))

    def test__wait_for_status_fail(self):
        """
        test _wait_for_status()
        """
        self.mock_kinesis_analytics.describe_application.side_effect = lambda ApplicationName,\
            IncludeAdditionalDetails=True: mock_describe_flink_application(ApplicationName, 'RUNNING')
        with self.assertRaises(RuntimeError):
            kinan_utils._wait_for_status(
                kinesis_analytics_client=self.client_side_effect_map.get('kinesisanalyticsv2'),
                app_name=TEST_APPLICATION_NAME,
                status='RUNNING',
                wait_period=0,
                interval_to_sleep=-0.001)

    @patch('resource_manager.src.util.kinesis_analytics_utils.choices')
    def test__snapshot_postfix(self, mock_choices):
        """
        test _snapshot_postfix()
        """
        mock_choices.side_effect = lambda t, k: "gorx12"
        self.assertEqual(kinan_utils._snapshot_postfix(postfix_digits=6), "gorx12")

    @patch('resource_manager.src.util.kinesis_analytics_utils.choices')
    def test__new_test_standard_snapshot_name(self, mock_choices):
        """
        test _new_test_standard_snapshot_name()
        """
        mock_choices.side_effect = lambda t, k=6: "gorx12"
        self.assertEqual(kinan_utils._new_test_standard_snapshot_name(TEST_APPLICATION_NAME),
                         "TEST-KinesisAnalyticsFl_Ve6KhqPQMAxk-gorx12")
