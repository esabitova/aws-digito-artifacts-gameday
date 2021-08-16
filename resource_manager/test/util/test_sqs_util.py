import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

import resource_manager.src.util.sqs_utils as sqs_utils
from documents.util.scripts.test.mock_sleep import MockSleep
import resource_manager.src.util.boto3_client_factory as client_factory


SQS_QUEUE_URL = "https://this.is.some.url"
SQS_FIFO_QUEUE_URL = "https://this.is.some.url.fifo"
SQS_MESSAGE_BODY = "some message body"
SQS_FIFO_MESSAGE_GROUP = "message-group-id"
SQS_POLICY = '{"some-field": "some-value", "some-other-field": "some-other-value"}'
ATTRIBUTES = {
    'Attributes': {
        'ApproximateNumberOfMessages': "10",
        'Policy': SQS_POLICY}
}


def get_queue_attributes_side_effect(number_of_messages):
    return {
        'Attributes': {
            'ApproximateNumberOfMessages': number_of_messages,
            'Policy': SQS_POLICY
        }
    }


@pytest.mark.unit_test
class TestSQSUtil(unittest.TestCase):

    def setUp(self):
        self.mock_time = 0
        self.session_mock = MagicMock()
        self.mock_sqs_service = MagicMock()
        self.client_side_effect_map = {
            'sqs': self.mock_sqs_service,

        }
        self.session_mock.client.side_effect = lambda service_name, config=None: \
            self.client_side_effect_map.get(service_name)

    def tearDown(self):
        # Clean client factory cache after each test.
        client_factory.clients = {}
        client_factory.resources = {}

    def mock_sleep(self, time):
        """
        A mock sleep call to replace time.sleep which is called by dependencies
        """
        self.mock_time += time
        return time

    def test_send_message_to_queue(self):
        sqs_utils.send_message_to_standard_queue(self.session_mock, SQS_QUEUE_URL, SQS_MESSAGE_BODY)
        self.mock_sqs_service.send_message.assert_called_once_with(QueueUrl=SQS_QUEUE_URL, MessageBody=SQS_MESSAGE_BODY)

    def test_send_message_to_queue_with_attributes(self):
        sqs_utils.send_message_to_standard_queue(self.session_mock, SQS_QUEUE_URL, SQS_MESSAGE_BODY, ATTRIBUTES)
        self.mock_sqs_service.send_message.assert_called_once_with(QueueUrl=SQS_QUEUE_URL,
                                                                   MessageBody=SQS_MESSAGE_BODY,
                                                                   MessageAttributes=ATTRIBUTES)

    def test_send_message_to_fifo_queue(self):
        now = datetime.now().isoformat()
        sqs_utils.send_message_to_fifo_queue(self.session_mock, SQS_QUEUE_URL, SQS_MESSAGE_BODY, SQS_FIFO_MESSAGE_GROUP,
                                             now)
        self.mock_sqs_service.send_message.assert_called_once_with(
            QueueUrl=SQS_QUEUE_URL, MessageBody=SQS_MESSAGE_BODY, MessageGroupId=SQS_FIFO_MESSAGE_GROUP,
            MessageDeduplicationId=now
        )

    @patch('time.sleep')
    @patch('time.time')
    def test_send_messages_until_access_denied(self, patched_time, patched_sleep):
        mock_sleep = MockSleep()
        patched_time.side_effect = mock_sleep.time
        patched_sleep.side_effect = mock_sleep.sleep

        self.mock_sqs_service.send_message.side_effect = [
            {}, ClientError({'Error': {'Code': 'AccessDenied'}}, ''), {}
        ]
        sqs_utils.send_messages_until_access_denied(self.session_mock, SQS_QUEUE_URL, 50)
        self.assertEqual(2, self.mock_sqs_service.send_message.call_count)
        self.mock_sqs_service.send_message.reset_mock()

    @patch('time.sleep')
    @patch('time.time')
    def test_send_messages_until_access_denied_failed(self, patched_time, patched_sleep):
        mock_sleep = MockSleep()
        patched_time.side_effect = mock_sleep.time
        patched_sleep.side_effect = mock_sleep.sleep

        self.mock_sqs_service.send_message.side_effect = [
            {}, ClientError({'Error': {'Code': 'SomeErrorCode'}}, ''), {}
        ]
        self.assertRaises(
            ClientError, sqs_utils.send_messages_until_access_denied, self.session_mock, SQS_QUEUE_URL, 50
        )
        self.assertEqual(2, self.mock_sqs_service.send_message.call_count)
        self.mock_sqs_service.send_message.reset_mock()

    @patch('time.sleep')
    @patch('time.time')
    def test_send_messages_until_access_denied_timeout(self, patched_time, patched_sleep):
        mock_sleep = MockSleep()
        patched_time.side_effect = mock_sleep.time
        patched_sleep.side_effect = mock_sleep.sleep

        self.assertRaises(
            Exception, sqs_utils.send_messages_until_access_denied, self.session_mock, SQS_QUEUE_URL, 50
        )
        self.assertEqual(3, self.mock_sqs_service.send_message.call_count)

    @patch('time.sleep')
    @patch('time.time')
    def test_send_messages_until_success(self, patched_time, patched_sleep):
        mock_sleep = MockSleep()
        patched_time.side_effect = mock_sleep.time
        patched_sleep.side_effect = mock_sleep.sleep

        sqs_utils.send_messages_until_success(self.session_mock, SQS_QUEUE_URL, 50, 3)
        self.assertEqual(3, self.mock_sqs_service.send_message.call_count)

    @patch('time.sleep')
    @patch('time.time')
    def test_send_messages_until_success_failed(self, patched_time, patched_sleep):
        mock_sleep = MockSleep()
        patched_time.side_effect = mock_sleep.time
        patched_sleep.side_effect = mock_sleep.sleep

        self.mock_sqs_service.send_message.side_effect = [
            {}, ClientError({'Error': {'Code': 'SomeErrorCode'}}, ''), {}
        ]
        self.assertRaises(
            ClientError, sqs_utils.send_messages_until_success, self.session_mock, SQS_QUEUE_URL, 50, 2
        )
        self.assertEqual(2, self.mock_sqs_service.send_message.call_count)
        self.mock_sqs_service.send_message.reset_mock()

    @patch('time.sleep')
    @patch('time.time')
    def test_send_messages_until_success_access_denied(self, patched_time, patched_sleep):
        mock_sleep = MockSleep()
        patched_time.side_effect = mock_sleep.time
        patched_sleep.side_effect = mock_sleep.sleep

        self.mock_sqs_service.send_message.side_effect = [
            {}, ClientError({'Error': {'Code': 'AccessDenied'}}, ''), {}
        ]
        sqs_utils.send_messages_until_success(self.session_mock, SQS_QUEUE_URL, 50, 3)
        self.assertEqual(3, self.mock_sqs_service.send_message.call_count)
        self.mock_sqs_service.send_message.reset_mock()

    @patch('time.sleep')
    @patch('time.time')
    def test_send_messages_until_success_always_access_denied(self, patched_time, patched_sleep):
        mock_sleep = MockSleep()
        patched_time.side_effect = mock_sleep.time
        patched_sleep.side_effect = mock_sleep.sleep

        self.mock_sqs_service.send_message.side_effect = ClientError({'Error': {'Code': 'AccessDenied'}}, '')
        self.assertRaises(
            Exception, sqs_utils.send_messages_until_success, self.session_mock, SQS_QUEUE_URL, 50, 3
        )
        self.assertEqual(3, self.mock_sqs_service.send_message.call_count)
        self.mock_sqs_service.send_message.reset_mock()

    def test_get_number_of_messages(self):
        self.mock_sqs_service.get_queue_attributes.return_value = get_queue_attributes_side_effect(25)
        number_of_messages = sqs_utils.get_number_of_messages(self.session_mock, SQS_QUEUE_URL)
        self.mock_sqs_service.get_queue_attributes.assert_called_once_with(
            QueueUrl=SQS_QUEUE_URL, AttributeNames=['ApproximateNumberOfMessages']
        )
        self.assertEqual(25, number_of_messages)

    def test_get_number_of_messages_missing(self):
        self.mock_sqs_service.get_queue_attributes.return_value = {}
        self.assertRaises(Exception, sqs_utils.get_number_of_messages, self.session_mock, SQS_QUEUE_URL)

    def test_get_policy(self):
        self.mock_sqs_service.get_queue_attributes.return_value = get_queue_attributes_side_effect(5)
        policy = sqs_utils.get_policy(self.session_mock, SQS_QUEUE_URL)
        self.mock_sqs_service.get_queue_attributes.assert_called_once_with(
            QueueUrl=SQS_QUEUE_URL, AttributeNames=['Policy']
        )
        self.assertEqual({'some-field': 'some-value', 'some-other-field': 'some-other-value'}, policy)

    def test_get_policy_no_policy(self):
        self.mock_sqs_service.get_queue_attributes.return_value = {}
        policy = sqs_utils.get_policy(self.session_mock, SQS_QUEUE_URL)
        self.mock_sqs_service.get_queue_attributes.assert_called_once_with(
            QueueUrl=SQS_QUEUE_URL, AttributeNames=['Policy']
        )
        self.assertEqual({}, policy)

    def test_purge_queue_raise_error(self):
        self.mock_sqs_service.purge_queue.side_effect = \
            ClientError({'Error': {'Code': 'SomeDifferentCode'}}, "")
        self.assertRaises(Exception, sqs_utils.purge_queue, self.session_mock, SQS_QUEUE_URL)

    def test_purge_queue_continue_loop(self):
        self.mock_sqs_service.purge_queue.side_effect = [
            ClientError({'Error': {'Code': 'AWS.SimpleQueueService.PurgeQueueInProgress'}}, ""),
            {}]
        sqs_utils.purge_queue(self.session_mock, SQS_QUEUE_URL, purge_queue_duration=1)
