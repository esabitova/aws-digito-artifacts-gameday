import unittest
from unittest.mock import MagicMock, patch
import pytest
import resource_manager.src.util.boto3_client_factory as client_factory
from resource_manager.src.util import kinesis_data_streams_utils

STREAM_NAME = "SomeKinesisDataStream"
MESSAGES_NUMBER = 10
THREAD_NUMBER = 5
DELAY_SEC = 0
RECORDS = [{'Data': b'0', 'PartitionKey': '3a9e646d-508b-4313-ab9c-a5e9fc568dec'},
           {'Data': b'1', 'PartitionKey': 'c17921bb-db01-4fc7-a06a-7adaeb9bb20a'},
           {'Data': b'2', 'PartitionKey': '8e72547a-8d40-4f6a-85c8-1f62f654e4ee'},
           {'Data': b'3', 'PartitionKey': 'f49d0355-004a-4bdd-934e-0c8dd9ed548a'},
           {'Data': b'4', 'PartitionKey': '08d4f23b-bbe8-4120-a25a-4ea9b6d522eb'}]
SHARD_ITERATOR = "shard iterator"
LIMIT = 3


@pytest.mark.unit_test
class KinesisDataStreamsTestUtils(unittest.TestCase):

    def setUp(self):
        self.mock_time = 0
        self.session_mock = MagicMock()
        self.mock_kinesis_service = MagicMock()
        self.client_side_effect_map = {
            'kinesis': self.mock_kinesis_service
        }

        self.session_mock.client.side_effect = lambda service_name, config=None: \
            self.client_side_effect_map.get(service_name)

    def tearDown(self):
        client_factory.clients = {}
        client_factory.resources = {}

    def test_generate_records(self):
        records = kinesis_data_streams_utils.generate_records(5)
        self.assertEqual(5, len(records))

    @patch('resource_manager.src.util.kinesis_data_streams_utils.put_records',
           return_value=False)
    def test_put_records_in_batch_async(self, put_records_mock):
        kinesis_data_streams_utils.put_records_in_batch_async(self.session_mock, STREAM_NAME, MESSAGES_NUMBER,
                                                              THREAD_NUMBER, DELAY_SEC)
        self.mock_kinesis_service.called
        self.assertEqual(put_records_mock.call_count, 5)

    def test_put_records(self):
        kinesis_data_streams_utils.put_records(self.session_mock, STREAM_NAME, RECORDS)
        self.mock_kinesis_service.called
        self.mock_kinesis_service.put_records.assert_called_with(StreamName=STREAM_NAME, Records=RECORDS)

    def test_get_records(self):
        kinesis_data_streams_utils.get_records(self.session_mock, SHARD_ITERATOR, LIMIT)
        self.mock_kinesis_service.called
        self.mock_kinesis_service.get_records.assert_called_with(ShardIterator=SHARD_ITERATOR, Limit=LIMIT)

    @patch('resource_manager.src.util.kinesis_data_streams_utils.get_records',
           return_value=False)
    def test_get_records_in_batch_async(self, get_records_mock):
        shard_id = self.mock_kinesis_service.describe_stream(StreamName=STREAM_NAME)['StreamDescription']['Shards'][0]
        ['ShardId']
        kinesis_data_streams_utils.get_records_in_batch_async(self.session_mock, STREAM_NAME, MESSAGES_NUMBER,
                                                              THREAD_NUMBER, DELAY_SEC)
        self.mock_kinesis_service.called
        self.mock_kinesis_service.describe_stream.assert_called_with(StreamName=STREAM_NAME)
        self.mock_kinesis_service.get_shard_iterator.assert_called_with(StreamName=STREAM_NAME, ShardId=shard_id,
                                                                        ShardIteratorType='TRIM_HORIZON')
        self.assertEqual(get_records_mock.call_count, 5)
