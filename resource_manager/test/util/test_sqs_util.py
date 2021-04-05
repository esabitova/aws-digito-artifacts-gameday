import unittest
import pytest
from unittest.mock import MagicMock
from datetime import datetime
import resource_manager.src.util.sqs_utils as sqs_utils

SQS_QUEUE_URL = "https://this.is.some.url"
SQS_FIFO_QUEUE_URL = "https://this.is.some.url.fifo"
SQS_MESSAGE_BODY = "some message body"
SQS_FIFO_MESSAGE_GROUP = "message-group-id"
SQS_POLICY = '{"some-field": "some-value", "some-other-field": "some-other-value"}'


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
        self.session_mock = MagicMock()
        self.mock_sqs_service = MagicMock()
        self.client_side_effect_map = {
            'sqs': self.mock_sqs_service,

        }
        self.session_mock.client.side_effect = lambda service_name: self.client_side_effect_map.get(service_name)

    def tearDown(self):
        pass

    def test_send_message_to_queue(self):
        sqs_utils.send_message_to_standard_queue(self.session_mock, SQS_QUEUE_URL, SQS_MESSAGE_BODY)
        self.mock_sqs_service.send_message.assert_called_once_with(QueueUrl=SQS_QUEUE_URL, MessageBody=SQS_MESSAGE_BODY)

    def test_send_message_to_fifo_queue(self):
        now = datetime.now().isoformat()
        sqs_utils.send_message_to_fifo_queue(self.session_mock, SQS_QUEUE_URL, SQS_MESSAGE_BODY, SQS_FIFO_MESSAGE_GROUP,
                                             now)
        self.mock_sqs_service.send_message.assert_called_once_with(
            QueueUrl=SQS_QUEUE_URL, MessageBody=SQS_MESSAGE_BODY, MessageGroupId=SQS_FIFO_MESSAGE_GROUP,
            MessageDeduplicationId=now
        )

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
