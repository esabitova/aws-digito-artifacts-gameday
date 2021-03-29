import json
import unittest
import uuid
from unittest.mock import patch, MagicMock

import pytest

from documents.util.scripts.src.sqs_util import add_deny_in_sqs_policy, revert_sqs_policy, transfer_messages
from documents.util.scripts.src.sqs_util import send_message_of_size

SQS_STANDARD_QUEUE_URL = "https://sqs.us-east-2.amazonaws.com/123456789012/MyQueue"
SQS_STANDARD_DEST_QUEUE_URL = "https://sqs.us-east-2.amazonaws.com/123456789012/MyDestQueue"
SQS_FIFO_QUEUE_URL = "https://sqs.us-east-2.amazonaws.com/123456789012/MyQueue.fifo"


@pytest.mark.unit_test
class TestSqsUtil(unittest.TestCase):
    def setUp(self):
        self.number_of_messages_to_transfer = 40
        self.messages_transfer_batch_size = 10
        self.queue_url = SQS_STANDARD_QUEUE_URL
        self.empty_policy = {"Policy": ""}
        self.resource = "arn:aws:sqs:us-east-2:444455556666:queue1"
        self.action_to_deny = "sqs:DeleteMessage"
        self.patcher = patch("documents.util.scripts.src.sqs_util.sqs_client")
        self.client = self.patcher.start()
        self.client.side_effect = MagicMock()

    def tearDown(self):
        self.patcher.stop()

    def test_add_deny_in_sqs_policy_empty_events(self):
        events = {}
        self.assertRaises(KeyError, add_deny_in_sqs_policy, events, None)

    def test_revert_sqs_policy_empty_events(self):
        events = {}
        self.assertRaises(KeyError, revert_sqs_policy, events, None)
        self.client.set_queue_attributes.assert_not_called()

    def test_add_deny_in_sqs_policy_empty_source_policy(self):
        events = {
            "ActionsToDeny": self.action_to_deny,
            "Resource": self.resource,
            "SourcePolicy": "{{SourcePolicyVariableFromSsmDocument}}"
        }
        response = add_deny_in_sqs_policy(events, None)
        self.assertIsNotNone(response["DenyPolicyStatementSid"])
        self.assertIsNotNone(response["PolicySid"])
        self.assertIsNotNone(response["Policy"])
        policy = json.loads(response["Policy"])
        self.assertIsNotNone(policy["Statement"])
        self.assertEqual(1, len(policy["Statement"]))

    def test_add_deny_in_sqs_policy_non_empty_source_policy(self):
        events = {
            "ActionsToDeny": "sqs:DeleteMessage",
            "Resource": "arn:aws:sqs:us-east-2:444455556666:queue1",
            "SourcePolicy": json.dumps({
                "Version": "2012-10-17",
                "Id": f"DenyPolicy-{uuid.uuid4()}",
                "Statement": [{
                    "Effect": "Deny",
                    "Sid": f"DenyPolicyStatement-{uuid.uuid4()}",
                    "Principal": "*",
                    "Action": self.action_to_deny,
                    "Resource": self.resource,
                }
                ]
            }
            )
        }
        response = add_deny_in_sqs_policy(events, None)
        self.assertIsNotNone(response["DenyPolicyStatementSid"])
        self.assertIsNotNone(response["PolicySid"])
        policy = json.loads(response["Policy"])
        self.assertIsNotNone(policy["Statement"])
        self.assertEqual(2, len(policy["Statement"]))

    def test_add_deny_in_sqs_policy_empty_statement(self):
        events = {
            "ActionsToDeny": "sqs:DeleteMessage",
            "Resource": "arn:aws:sqs:us-east-2:444455556666:queue1",
            "SourcePolicy": json.dumps({
                "Version": "2012-10-17",
                "Id": f"DenyPolicy-{uuid.uuid4()}",
                "Statement": []}
            )
        }
        self.assertRaises(KeyError, add_deny_in_sqs_policy, events, None)

    def test_revert_sqs_policy(self):
        events = {
            "QueueUrl": self.queue_url,
            "OptionalBackupPolicy": "some_policy"
        }
        revert_sqs_policy(events, None)
        self.client.set_queue_attributes.assert_called_once()

    def test_revert_sqs_policy_empty_optional_backup_policy(self):
        events = {
            "QueueUrl": self.queue_url,
            "OptionalBackupPolicy": "{{VariableFromSsmDocument}}"
        }
        revert_sqs_policy(events, None)
        self.client.set_queue_attributes.assert_called_once_with(QueueUrl=self.queue_url,
                                                                 Attributes=self.empty_policy)

    def test_send_message_of_size_standard(self):
        events = {
            "QueueUrl": SQS_STANDARD_QUEUE_URL,
            "MessageSize": 100
        }
        send_message_of_size(events, None)
        self.client.send_message.assert_called_once()
        self.assertEqual(100, len(self.client.send_message.call_args[1]['MessageBody']))

    def test_send_message_of_size_fifo_no_token(self):
        events = {
            "QueueUrl": SQS_FIFO_QUEUE_URL,
            "MessageSize": 100
        }
        self.assertRaises(KeyError, send_message_of_size, events, None)

    def test_send_message_of_size_fifo(self):
        events = {
            "QueueUrl": SQS_FIFO_QUEUE_URL,
            "MessageSize": 100,
            "MessageDeduplicationId": 'some-token'
        }
        send_message_of_size(events, None)
        self.client.send_message.assert_called_once()
        self.assertEqual(100, len(self.client.send_message.call_args[1]['MessageBody']))

    def test_transfer_messages_empty_events(self):
        events = {}
        self.assertRaises(KeyError, transfer_messages, events, None)
        self.client.receive_message.assert_not_called()

    def test_transfer_messages_empty_sqs_standard_queue_url(self):
        events = {
            "TargetQueueUrl": SQS_STANDARD_QUEUE_URL,
            "NumberOfMessagesToTransfer": 123,
            "MessagesTransferBatchSize": 123,
            "ForceExecution": True
        }
        self.assertRaises(KeyError, transfer_messages, events, None)
        self.client.receive_message.assert_not_called()

    def test_transfer_messages_empty_target_queue_url(self):
        events = {
            "SourceQueueUrl": SQS_STANDARD_QUEUE_URL,
            "NumberOfMessagesToTransfer": 123,
            "MessagesTransferBatchSize": 123,
            "ForceExecution": True
        }
        self.assertRaises(KeyError, transfer_messages, events, None)
        self.client.receive_message.assert_not_called()

    def test_transfer_messages_empty_number_of_messages_to_transfer(self):
        events = {
            "SourceQueueUrl": SQS_STANDARD_QUEUE_URL,
            "TargetQueueUrl": SQS_STANDARD_QUEUE_URL,
            "MessagesTransferBatchSize": 123,
            "ForceExecution": True
        }
        self.assertRaises(KeyError, transfer_messages, events, None)
        self.client.receive_message.assert_not_called()

    def test_transfer_messages_empty_messages_transfer_batch_size(self):
        events = {
            "SourceQueueUrl": SQS_STANDARD_QUEUE_URL,
            "TargetQueueUrl": SQS_STANDARD_QUEUE_URL,
            "NumberOfMessagesToTransfer": 123,
            "ForceExecution": True
        }
        self.assertRaises(KeyError, transfer_messages, events, None)
        self.client.receive_message.assert_not_called()

    def test_transfer_messages_empty_force_execution(self):
        events = {
            "SourceQueueUrl": SQS_STANDARD_QUEUE_URL,
            "TargetQueueUrl": SQS_STANDARD_QUEUE_URL,
            "MessagesTransferBatchSize": 123,
            "ForceExecution": True
        }
        self.assertRaises(KeyError, transfer_messages, events, None)
        self.client.receive_message.assert_not_called()

    # def test_transfer_messages(self):
    #     events = {
    #         "SourceQueueUrl": SQS_STANDARD_QUEUE_URL,
    #         "TargetQueueUrl": SQS_STANDARD_DEST_QUEUE_URL,
    #         "MessagesTransferBatchSize": self.messages_transfer_batch_size,
    #         "NumberOfMessagesToTransfer": self.number_of_messages_to_transfer,
    #         "ForceExecution": True
    #     }
    #     transfer_messages(events, None)
    #     self.client.get_queue_attributes.assert_called_once_with(QueueUrl=SQS_STANDARD_QUEUE_URL,
    #                                                              AttributeNames=['FifoQueue'])
    #     self.client.get_queue_attributes.assert_called_once_with(QueueUrl=SQS_STANDARD_DEST_QUEUE_URL,
    #                                                              AttributeNames=['FifoQueue'])
    #     self.client.receive_message.assert_called_with(QueueUrl=SQS_STANDARD_QUEUE_URL,
    #                                                    MaxNumberOfMessages=self.messages_transfer_batch_size,
    #                                                    MessageAttributeNames=['All'],
    #                                                    AttributeNames=['All'])
