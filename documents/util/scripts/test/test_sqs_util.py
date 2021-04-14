import json
import unittest
import uuid
from unittest.mock import patch, MagicMock, call

import pytest
from botocore.exceptions import ClientError

from documents.util.scripts.src.sqs_util import add_deny_in_sqs_policy, revert_sqs_policy, get_message_receipt_handle
from documents.util.scripts.src.sqs_util import get_dead_letter_queue_url, update_max_receive_count, transfer_messages
from documents.util.scripts.src.sqs_util import send_message_of_size, receive_message_by_id

SQS_STANDARD_QUEUE_URL = "https://sqs.us-east-2.amazonaws.com/123456789012/MyQueue"
SQS_STANDARD_DEST_QUEUE_URL = "https://sqs.us-east-2.amazonaws.com/123456789012/MyDestQueue"
SQS_FIFO_QUEUE_URL = "https://sqs.us-east-2.amazonaws.com/123456789012/MyQueue.fifo"

SUCCESSFUL_ID_1 = "28004ed8-264f-4070-9937-bceb040d4393"
SUCCESSFUL_RECEIPT_HANDLE_1 = "asads"
SUCCESSFUL_BODY_1 = "This is message 1.1"

SUCCESSFUL_ID_2 = "12344ed8-264f-4070-9937-bceb040d4890"
SUCCESSFUL_RECEIPT_HANDLE_2 = "asadasdasds"
SUCCESSFUL_BODY_2 = "This is message 1.2"

FAILED_TO_SEND_ID = "7b95db9e-e1a1-45fa-a3f7-69be3965e834"
FAILED_TO_SEND_BODY = "This is message 3"

FAILED_TO_DELETE_ID = "b0993f80-5629-49e9-be68-1c31fa15d14d"
FAILED_TO_DELETE_RECEIPT_HANDLE = "asdadsad"
FAILED_TO_DELETE_BODY = "This is message 2"

AWS_TRACE_HEADER = "1617093473357"

MESSAGE_DEDUPLICATION_ID = "2dc6c953-a523-4dee-9b76-14db5096c8cd"
MESSAGE_GROUP_ID = "70b31170-f246-46ba-b55c-d1f906887c5c"
message_attributes = {
    "test_attribute_name_1": {
        "StringValue": "test_attribute_value_1",
        "DataType": "String"
    }
}
RECEIVE_MESSAGE_RESPONSE_FROM_FIFO = {
    "Messages": [
        {
            "MessageId": SUCCESSFUL_ID_1,
            "ReceiptHandle": SUCCESSFUL_RECEIPT_HANDLE_1,
            "MD5OfBody": "17363d9618bbd089e643f59ff71cff86",
            "Body": SUCCESSFUL_BODY_1,
            "Attributes": {
                "SenderId": "AIDAWLAST5TNZEFJSIWHG",
                "ApproximateFirstReceiveTimestamp": "1617116187961",
                "ApproximateReceiveCount": "1",
                "SentTimestamp": "1617116181170",
                "MessageDeduplicationId": MESSAGE_DEDUPLICATION_ID,
                "MessageGroupId": MESSAGE_GROUP_ID,
                "AWSTraceHeader": AWS_TRACE_HEADER
            },
            "MD5OfMessageAttributes": "ba056227cfd9533dba1f72ad9816d233",
            "MessageAttributes": message_attributes
        },
        {
            "MessageId": SUCCESSFUL_ID_2,
            "ReceiptHandle": SUCCESSFUL_RECEIPT_HANDLE_2,
            "MD5OfBody": "17363d9618bbd089e643f59ff71cff86",
            "Body": SUCCESSFUL_BODY_2,
            "Attributes": {
                "SenderId": "AIDAWLAST5TNZEFJSIWHG",
                "ApproximateFirstReceiveTimestamp": "1617116187961",
                "ApproximateReceiveCount": "1",
                "SentTimestamp": "1617116181170",
                "MessageDeduplicationId": MESSAGE_DEDUPLICATION_ID,
                "MessageGroupId": MESSAGE_GROUP_ID,
                "AWSTraceHeader": AWS_TRACE_HEADER
            },
            "MD5OfMessageAttributes": "ba056227cfd9533dba1f72ad9816d233",
            "MessageAttributes": message_attributes
        },
        {
            "MessageId": FAILED_TO_DELETE_ID,
            "ReceiptHandle": FAILED_TO_DELETE_RECEIPT_HANDLE,
            "MD5OfBody": "6ea7555c95fea7ff1e840422be25d632",
            "Body": FAILED_TO_DELETE_BODY,
            "Attributes": {
                "SenderId": "AIDAWLAST5TNZEFJSIWHG",
                "ApproximateFirstReceiveTimestamp": "1617116188014",
                "ApproximateReceiveCount": "1",
                "SentTimestamp": "1617116181398",
                "MessageDeduplicationId": MESSAGE_DEDUPLICATION_ID,
                "MessageGroupId": MESSAGE_GROUP_ID,
                "AWSTraceHeader": AWS_TRACE_HEADER
            },
            "MD5OfMessageAttributes": "ba056227cfd9533dba1f72ad9816d233",
            "MessageAttributes": message_attributes
        },
        {
            "MessageId": FAILED_TO_SEND_ID,
            "ReceiptHandle": "asdasd",
            "MD5OfBody": "56b24f6d8b2e1555249bd38ae3668c2f",
            "Body": FAILED_TO_SEND_BODY,
            "Attributes": {
                "SenderId": "AIDAWLAST5TNZEFJSIWHG",
                "ApproximateFirstReceiveTimestamp": "1617116187963",
                "ApproximateReceiveCount": "1",
                "SentTimestamp": "1617116181640",
                "MessageDeduplicationId": MESSAGE_DEDUPLICATION_ID,
                "MessageGroupId": MESSAGE_GROUP_ID,
                "AWSTraceHeader": AWS_TRACE_HEADER
            },
            "MD5OfMessageAttributes": "ba056227cfd9533dba1f72ad9816d233",
            "MessageAttributes": message_attributes
        }
    ]}
RECEIVE_MESSAGE_RESPONSE_FROM_STANDARD = {
    "Messages": [
        {
            "MessageId": SUCCESSFUL_ID_1,
            "ReceiptHandle": SUCCESSFUL_RECEIPT_HANDLE_1,
            "MD5OfBody": "17363d9618bbd089e643f59ff71cff86",
            "Body": SUCCESSFUL_BODY_1,
            "Attributes": {
                "SenderId": "AIDAWLAST5TNZEFJSIWHG",
                "ApproximateFirstReceiveTimestamp": "1617116187961",
                "ApproximateReceiveCount": "1",
                "SentTimestamp": "1617116181170",
                "AWSTraceHeader": AWS_TRACE_HEADER
            },
            "MD5OfMessageAttributes": "ba056227cfd9533dba1f72ad9816d233",
            "MessageAttributes": message_attributes
        }, {
            "MessageId": SUCCESSFUL_ID_2,
            "ReceiptHandle": SUCCESSFUL_RECEIPT_HANDLE_2,
            "MD5OfBody": "17363d9618bbd089e643f59ff71cff86",
            "Body": SUCCESSFUL_BODY_2,
            "Attributes": {
                "SenderId": "AIDAWLAST5TNZEFJSIWHG",
                "ApproximateFirstReceiveTimestamp": "1617116187961",
                "ApproximateReceiveCount": "1",
                "SentTimestamp": "1617116181170",
                "AWSTraceHeader": AWS_TRACE_HEADER
            },
            "MD5OfMessageAttributes": "ba056227cfd9533dba1f72ad9816d233",
            "MessageAttributes": message_attributes
        },
        {
            "MessageId": FAILED_TO_DELETE_ID,
            "ReceiptHandle": FAILED_TO_DELETE_RECEIPT_HANDLE,
            "MD5OfBody": "6ea7555c95fea7ff1e840422be25d632",
            "Body": FAILED_TO_DELETE_BODY,
            "Attributes": {
                "SenderId": "AIDAWLAST5TNZEFJSIWHG",
                "ApproximateFirstReceiveTimestamp": "1617116188014",
                "ApproximateReceiveCount": "1",
                "SentTimestamp": "1617116181398",
                "AWSTraceHeader": AWS_TRACE_HEADER
            },
            "MD5OfMessageAttributes": "ba056227cfd9533dba1f72ad9816d233",
            "MessageAttributes": message_attributes
        },
        {
            "MessageId": FAILED_TO_SEND_ID,
            "ReceiptHandle": "asdasd",
            "MD5OfBody": "56b24f6d8b2e1555249bd38ae3668c2f",
            "Body": FAILED_TO_SEND_BODY,
            "Attributes": {
                "SenderId": "AIDAWLAST5TNZEFJSIWHG",
                "ApproximateFirstReceiveTimestamp": "1617116187963",
                "ApproximateReceiveCount": "1",
                "SentTimestamp": "1617116181640",
                "AWSTraceHeader": AWS_TRACE_HEADER
            },
            "MD5OfMessageAttributes": "ba056227cfd9533dba1f72ad9816d233",
            "MessageAttributes": message_attributes
        }
    ]}

MESSAGES_TO_SEND_FROM_FIFO_TO_FIFO = [
    {
        "Id": SUCCESSFUL_ID_1,
        "MessageBody": SUCCESSFUL_BODY_1,
        "MessageAttributes": message_attributes,
        "MessageDeduplicationId": MESSAGE_DEDUPLICATION_ID,
        "MessageGroupId": MESSAGE_GROUP_ID,
        'MessageSystemAttributes': {
            'AWSTraceHeader': {'StringValue': AWS_TRACE_HEADER, 'DataType': 'String'}
        }
    },
    {
        "Id": SUCCESSFUL_ID_2,
        "MessageBody": SUCCESSFUL_BODY_2,
        "MessageAttributes": message_attributes,
        "MessageDeduplicationId": MESSAGE_DEDUPLICATION_ID,
        "MessageGroupId": MESSAGE_GROUP_ID,
        'MessageSystemAttributes': {
            'AWSTraceHeader': {'StringValue': AWS_TRACE_HEADER, 'DataType': 'String'}
        }
    },
    {
        "Id": FAILED_TO_DELETE_ID,
        "MessageBody": FAILED_TO_DELETE_BODY,
        "MessageAttributes": message_attributes,
        "MessageDeduplicationId": MESSAGE_DEDUPLICATION_ID,
        "MessageGroupId": MESSAGE_GROUP_ID,
        'MessageSystemAttributes': {
            'AWSTraceHeader': {'StringValue': AWS_TRACE_HEADER, 'DataType': 'String'}
        }
    },
    {
        "Id": FAILED_TO_SEND_ID,
        "MessageBody": FAILED_TO_SEND_BODY,
        "MessageAttributes": message_attributes,
        "MessageDeduplicationId": MESSAGE_DEDUPLICATION_ID,
        "MessageGroupId": MESSAGE_GROUP_ID,
        'MessageSystemAttributes': {
            'AWSTraceHeader': {'StringValue': AWS_TRACE_HEADER, 'DataType': 'String'}
        }
    }
]
MESSAGES_TO_SEND_TO_STANDARD = [
    {
        "Id": SUCCESSFUL_ID_1,
        "MessageBody": SUCCESSFUL_BODY_1,
        "MessageAttributes": message_attributes,
        'MessageSystemAttributes': {
            'AWSTraceHeader': {'StringValue': AWS_TRACE_HEADER, 'DataType': 'String'}
        }
    }, {
        "Id": SUCCESSFUL_ID_2,
        "MessageBody": SUCCESSFUL_BODY_2,
        "MessageAttributes": message_attributes,
        'MessageSystemAttributes': {
            'AWSTraceHeader': {'StringValue': AWS_TRACE_HEADER, 'DataType': 'String'}
        }
    },
    {
        "Id": FAILED_TO_DELETE_ID,
        "MessageBody": FAILED_TO_DELETE_BODY,
        "MessageAttributes": message_attributes,
        'MessageSystemAttributes': {
            'AWSTraceHeader': {'StringValue': AWS_TRACE_HEADER, 'DataType': 'String'}
        }
    },
    {
        "Id": FAILED_TO_SEND_ID,
        "MessageBody": FAILED_TO_SEND_BODY,
        "MessageAttributes": message_attributes,
        'MessageSystemAttributes': {
            'AWSTraceHeader': {'StringValue': AWS_TRACE_HEADER, 'DataType': 'String'}
        }
    }
]

SEND_MESSAGE_BATCH_RESPONSE = {
    "Successful": [
        {
            "Id": SUCCESSFUL_ID_1,
            "MessageId": "d99dfb34-be9a-4f90-98d6-7a0d9173c7ec",
            "MD5OfMessageBody": "17363d9618bbd089e643f59ff71cff86",
            "MD5OfMessageAttributes": "ba056227cfd9533dba1f72ad9816d233"
        },
        {
            "Id": SUCCESSFUL_ID_2,
            "MessageId": "d99dfb34-be9a-4f90-98d6-7a0d9173c7ec",
            "MD5OfMessageBody": "17363d9618bbd089e643f59ff71cff86",
            "MD5OfMessageAttributes": "ba056227cfd9533dba1f72ad9816d233"
        },
        {
            "Id": FAILED_TO_DELETE_ID,
            "MessageId": "123dfb34-be9a-4f90-98d6-7a0d9173c7ec",
            "MD5OfMessageBody": "12363d9618bbd089e643f59ff71cff86",
            "MD5OfMessageAttributes": "12356227cfd9533dba1f72ad9816d233"
        },
    ],
    "Failed": [
        {
            "Id": FAILED_TO_SEND_ID,
            "SenderFault": True,
            "Code": "123456",
            "Message": "123456789"
        },
    ]
}

DELETE_MESSAGE_ENTRIES = [{"Id": SUCCESSFUL_ID_1, "ReceiptHandle": SUCCESSFUL_RECEIPT_HANDLE_1},
                          {"Id": SUCCESSFUL_ID_2, "ReceiptHandle": SUCCESSFUL_RECEIPT_HANDLE_2},
                          {'Id': FAILED_TO_DELETE_ID, 'ReceiptHandle': FAILED_TO_DELETE_RECEIPT_HANDLE}]

DELETE_MESSAGE_BATCH_RESPONSE = {"Successful": [{"Id": SUCCESSFUL_ID_1},
                                                {"Id": SUCCESSFUL_ID_2}],
                                 "Failed": [{"Id": FAILED_TO_DELETE_ID}]}

INVALID_ATTRIBUTE_NAME_ERROR = ClientError({'Error': {'Code': 'InvalidAttributeName'}}, "")


@pytest.mark.unit_test
class TestSqsUtil(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('boto3.client')
        self.client = self.patcher.start()
        self.sqs_client_mock = MagicMock()
        self.side_effect_map = {
            'sqs': self.sqs_client_mock
        }
        self.client.side_effect = lambda service_name: self.side_effect_map.get(service_name)
        self.sqs_client_mock.send_message_batch.return_value = SEND_MESSAGE_BATCH_RESPONSE
        self.sqs_client_mock.delete_message_batch.return_value = DELETE_MESSAGE_BATCH_RESPONSE

        self.number_of_messages_to_transfer = 40
        self.messages_transfer_batch_size = 10
        self.queue_url = SQS_STANDARD_QUEUE_URL
        self.empty_policy = {"Policy": ""}
        self.resource = "arn:aws:sqs:us-east-2:444455556666:MyQueue"
        self.queue_name = "MyQueue"
        self.redrive_policy = {"deadLetterTargetArn": self.resource, "maxReceiveCount": 5}
        self.action_to_deny = "sqs:DeleteMessage"

    def tearDown(self):
        self.patcher.stop()

    def test_add_deny_in_sqs_policy_empty_events(self):
        events = {}
        self.assertRaises(KeyError, add_deny_in_sqs_policy, events, None)

    def test_get_message_receipt_handle_exception(self):
        self.sqs_client_mock.receive_message.return_value = {"Messages": []}
        self.assertRaises(Exception, get_message_receipt_handle, SQS_STANDARD_QUEUE_URL, SUCCESSFUL_ID_1, 1)

    def test_get_message_receipt_handle_valid_use_case(self):
        self.sqs_client_mock.receive_message.return_value = RECEIVE_MESSAGE_RESPONSE_FROM_STANDARD
        response = get_message_receipt_handle(SQS_STANDARD_QUEUE_URL, SUCCESSFUL_ID_1, 1)
        self.assertIsNotNone(response)
        self.assertEqual(response, SUCCESSFUL_RECEIPT_HANDLE_1)

    def test_revert_sqs_policy_empty_events(self):
        events = {}
        self.assertRaises(KeyError, revert_sqs_policy, events, None)
        self.sqs_client_mock.set_queue_attributes.assert_not_called()

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
        self.sqs_client_mock.set_queue_attributes.assert_called_once()

    def test_revert_sqs_policy_empty_optional_backup_policy(self):
        events = {
            "QueueUrl": self.queue_url,
            "OptionalBackupPolicy": "{{VariableFromSsmDocument}}"
        }
        revert_sqs_policy(events, None)
        self.sqs_client_mock.set_queue_attributes.assert_called_once_with(QueueUrl=self.queue_url,
                                                                          Attributes=self.empty_policy)

    def test_send_message_of_size_standard(self):
        events = {
            "QueueUrl": SQS_STANDARD_QUEUE_URL,
            "MessageSize": 100
        }
        send_message_of_size(events, None)
        self.sqs_client_mock.send_message.assert_called_once()
        self.assertEqual(100, len(self.sqs_client_mock.send_message.call_args[1]['MessageBody']))

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
        self.sqs_client_mock.send_message.assert_called_once()
        self.assertEqual(100, len(self.sqs_client_mock.send_message.call_args[1]['MessageBody']))

    def test_transfer_messages_empty_events(self):
        events = {}
        self.assertRaises(KeyError, transfer_messages, events, None)
        self.sqs_client_mock.receive_message.assert_not_called()

    def test_transfer_messages_empty_sqs_standard_queue_url(self):
        events = {
            "TargetQueueUrl": SQS_STANDARD_QUEUE_URL,
            "NumberOfMessagesToTransfer": 123,
            "MessagesTransferBatchSize": 123,
            "ForceExecution": True
        }
        self.assertRaises(KeyError, transfer_messages, events, None)
        self.sqs_client_mock.receive_message.assert_not_called()

    def test_transfer_messages_empty_target_queue_url(self):
        events = {
            "SourceQueueUrl": SQS_STANDARD_QUEUE_URL,
            "NumberOfMessagesToTransfer": 123,
            "MessagesTransferBatchSize": 123,
            "ForceExecution": True
        }
        self.assertRaises(KeyError, transfer_messages, events, None)
        self.sqs_client_mock.receive_message.assert_not_called()

    def test_transfer_messages_empty_number_of_messages_to_transfer(self):
        events = {
            "SourceQueueUrl": SQS_STANDARD_QUEUE_URL,
            "TargetQueueUrl": SQS_STANDARD_QUEUE_URL,
            "MessagesTransferBatchSize": 123,
            "ForceExecution": True
        }
        self.assertRaises(KeyError, transfer_messages, events, None)
        self.sqs_client_mock.receive_message.assert_not_called()

    def test_transfer_messages_empty_messages_transfer_batch_size(self):
        events = {
            "SourceQueueUrl": SQS_STANDARD_QUEUE_URL,
            "TargetQueueUrl": SQS_STANDARD_QUEUE_URL,
            "NumberOfMessagesToTransfer": 123,
            "ForceExecution": True
        }
        self.assertRaises(KeyError, transfer_messages, events, None)
        self.sqs_client_mock.receive_message.assert_not_called()

    def test_transfer_messages_empty_force_execution(self):
        events = {
            "SourceQueueUrl": SQS_STANDARD_QUEUE_URL,
            "TargetQueueUrl": SQS_STANDARD_QUEUE_URL,
            "MessagesTransferBatchSize": 123,
            "ForceExecution": True
        }
        self.assertRaises(KeyError, transfer_messages, events, None)
        self.sqs_client_mock.receive_message.assert_not_called()

    def test_transfer_messages_from_standard_to_standard(self):
        events = {
            "SourceQueueUrl": SQS_STANDARD_QUEUE_URL,
            "TargetQueueUrl": SQS_STANDARD_DEST_QUEUE_URL,
            "MessagesTransferBatchSize": self.messages_transfer_batch_size,
            "NumberOfMessagesToTransfer": self.number_of_messages_to_transfer,
            "ForceExecution": True
        }
        self.sqs_client_mock.receive_message.side_effect = [RECEIVE_MESSAGE_RESPONSE_FROM_STANDARD, {'Messages': []}]
        self.sqs_client_mock.get_queue_attributes.side_effect = INVALID_ATTRIBUTE_NAME_ERROR
        actual_response = transfer_messages(events, None)
        self.assertIsNotNone(actual_response)
        self.assertEqual(2, actual_response['NumberOfMessagesTransferredToTarget'])
        self.assertEqual(1, actual_response['NumberOfMessagesFailedToDeleteFromSource'])
        self.assertEqual(1, actual_response['NumberOfMessagesFailedToSendToTarget'])
        self.assertIsNotNone(actual_response['TimeElapsed'])
        self.sqs_client_mock.get_queue_attributes.assert_has_calls([
            call(QueueUrl=SQS_STANDARD_QUEUE_URL, AttributeNames=['FifoQueue']),
            call(QueueUrl=SQS_STANDARD_DEST_QUEUE_URL, AttributeNames=['FifoQueue'])
        ])
        self.sqs_client_mock.receive_message.assert_called_with(QueueUrl=SQS_STANDARD_QUEUE_URL,
                                                                MaxNumberOfMessages=self.messages_transfer_batch_size,
                                                                MessageAttributeNames=['All'],
                                                                AttributeNames=['All'],
                                                                WaitTimeSeconds=0)
        self.sqs_client_mock.send_message_batch.assert_called_with(QueueUrl=SQS_STANDARD_DEST_QUEUE_URL,
                                                                   Entries=MESSAGES_TO_SEND_TO_STANDARD)
        self.sqs_client_mock.delete_message_batch.assert_called_with(QueueUrl=SQS_STANDARD_QUEUE_URL,
                                                                     Entries=DELETE_MESSAGE_ENTRIES)

    def test_transfer_messages_from_standard_to_fifo(self):
        events = {
            "SourceQueueUrl": SQS_STANDARD_QUEUE_URL,
            "TargetQueueUrl": SQS_STANDARD_DEST_QUEUE_URL,
            "MessagesTransferBatchSize": self.messages_transfer_batch_size,
            "NumberOfMessagesToTransfer": self.number_of_messages_to_transfer,
            "ForceExecution": True
        }
        self.sqs_client_mock.receive_message.side_effect = [RECEIVE_MESSAGE_RESPONSE_FROM_STANDARD, {'Messages': []}]
        self.sqs_client_mock.get_queue_attributes.side_effect = [INVALID_ATTRIBUTE_NAME_ERROR, {}]
        actual_response = transfer_messages(events, None)
        self.assertIsNotNone(actual_response)
        self.assertEqual(2, actual_response['NumberOfMessagesTransferredToTarget'])
        self.assertEqual(1, actual_response['NumberOfMessagesFailedToDeleteFromSource'])
        self.assertEqual(1, actual_response['NumberOfMessagesFailedToSendToTarget'])
        self.assertIsNotNone(actual_response['TimeElapsed'])
        self.sqs_client_mock.get_queue_attributes.assert_has_calls([
            call(QueueUrl=SQS_STANDARD_QUEUE_URL, AttributeNames=['FifoQueue']),
            call(QueueUrl=SQS_STANDARD_DEST_QUEUE_URL, AttributeNames=['FifoQueue'])
        ])
        self.sqs_client_mock.receive_message.assert_called_with(QueueUrl=SQS_STANDARD_QUEUE_URL,
                                                                MaxNumberOfMessages=self.messages_transfer_batch_size,
                                                                MessageAttributeNames=['All'],
                                                                AttributeNames=['All'],
                                                                WaitTimeSeconds=0)
        actual_send_message_batch_args = self.sqs_client_mock.send_message_batch.call_args[1]
        self.assertEqual(SQS_STANDARD_DEST_QUEUE_URL, actual_send_message_batch_args['QueueUrl'])
        actual_send_message_batch_entries = actual_send_message_batch_args['Entries']
        for i in range(0, len(MESSAGES_TO_SEND_FROM_FIFO_TO_FIFO)):
            expected = MESSAGES_TO_SEND_FROM_FIFO_TO_FIFO[i]
            actual = actual_send_message_batch_entries[i]
            for k in expected:
                if k in ["MessageDeduplicationId", "MessageGroupId"]:
                    self.assertIsNotNone(actual[k])
                    continue
                self.assertEqual(expected[k], actual[k])

        self.sqs_client_mock.delete_message_batch.assert_called_with(QueueUrl=SQS_STANDARD_QUEUE_URL,
                                                                     Entries=DELETE_MESSAGE_ENTRIES)

    def test_transfer_messages_from_fifo_to_standard(self):
        events = {
            "SourceQueueUrl": SQS_STANDARD_QUEUE_URL,
            "TargetQueueUrl": SQS_STANDARD_DEST_QUEUE_URL,
            "MessagesTransferBatchSize": self.messages_transfer_batch_size,
            "NumberOfMessagesToTransfer": self.number_of_messages_to_transfer,
            "ForceExecution": True
        }
        self.sqs_client_mock.receive_message.side_effect = [RECEIVE_MESSAGE_RESPONSE_FROM_FIFO, {'Messages': []}]
        self.sqs_client_mock.get_queue_attributes.side_effect = [{}, INVALID_ATTRIBUTE_NAME_ERROR]
        actual_response = transfer_messages(events, None)
        self.assertIsNotNone(actual_response)
        self.assertEqual(2, actual_response['NumberOfMessagesTransferredToTarget'])
        self.assertEqual(1, actual_response['NumberOfMessagesFailedToDeleteFromSource'])
        self.assertEqual(1, actual_response['NumberOfMessagesFailedToSendToTarget'])
        self.assertIsNotNone(actual_response['TimeElapsed'])
        self.sqs_client_mock.get_queue_attributes.assert_has_calls([
            call(QueueUrl=SQS_STANDARD_QUEUE_URL, AttributeNames=['FifoQueue']),
            call(QueueUrl=SQS_STANDARD_DEST_QUEUE_URL, AttributeNames=['FifoQueue'])
        ])
        self.sqs_client_mock.receive_message.assert_called_with(QueueUrl=SQS_STANDARD_QUEUE_URL,
                                                                MaxNumberOfMessages=self.messages_transfer_batch_size,
                                                                MessageAttributeNames=['All'],
                                                                AttributeNames=['All'],
                                                                WaitTimeSeconds=0)
        self.sqs_client_mock.send_message_batch.assert_called_with(QueueUrl=SQS_STANDARD_DEST_QUEUE_URL,
                                                                   Entries=MESSAGES_TO_SEND_TO_STANDARD)
        self.sqs_client_mock.delete_message_batch.assert_called_with(QueueUrl=SQS_STANDARD_QUEUE_URL,
                                                                     Entries=DELETE_MESSAGE_ENTRIES)

    def test_transfer_messages_from_fifo_to_fifo(self):
        events = {
            "SourceQueueUrl": SQS_STANDARD_QUEUE_URL,
            "TargetQueueUrl": SQS_STANDARD_DEST_QUEUE_URL,
            "MessagesTransferBatchSize": self.messages_transfer_batch_size,
            "NumberOfMessagesToTransfer": self.number_of_messages_to_transfer,
            "ForceExecution": True
        }
        self.sqs_client_mock.receive_message.side_effect = [RECEIVE_MESSAGE_RESPONSE_FROM_FIFO, {'Messages': []}]
        self.sqs_client_mock.get_queue_attributes.side_effect = [{}, {}]
        actual_response = transfer_messages(events, None)
        self.assertIsNotNone(actual_response)
        self.assertEqual(2, actual_response['NumberOfMessagesTransferredToTarget'])
        self.assertEqual(1, actual_response['NumberOfMessagesFailedToDeleteFromSource'])
        self.assertEqual(1, actual_response['NumberOfMessagesFailedToSendToTarget'])
        self.assertIsNotNone(actual_response['TimeElapsed'])
        self.sqs_client_mock.get_queue_attributes.assert_has_calls([
            call(QueueUrl=SQS_STANDARD_QUEUE_URL, AttributeNames=['FifoQueue']),
            call(QueueUrl=SQS_STANDARD_DEST_QUEUE_URL, AttributeNames=['FifoQueue'])
        ])
        self.sqs_client_mock.receive_message.assert_called_with(QueueUrl=SQS_STANDARD_QUEUE_URL,
                                                                MaxNumberOfMessages=self.messages_transfer_batch_size,
                                                                MessageAttributeNames=['All'],
                                                                AttributeNames=['All'],
                                                                WaitTimeSeconds=0)
        self.sqs_client_mock.send_message_batch.assert_called_with(QueueUrl=SQS_STANDARD_DEST_QUEUE_URL,
                                                                   Entries=MESSAGES_TO_SEND_FROM_FIFO_TO_FIFO)
        self.sqs_client_mock.delete_message_batch.assert_called_with(QueueUrl=SQS_STANDARD_QUEUE_URL,
                                                                     Entries=DELETE_MESSAGE_ENTRIES)

    def test_transfer_messages_if_receive_messages_number_is_higher_than_number_of_messages_to_transfer(self):
        """
        Test :func:`documents.util.scripts.src.sqs_util.transfer_messages`
        when there are more messages available to receive but we want to transfer part of them
        """
        number_of_messages_to_transfer = 2
        events = {
            "SourceQueueUrl": SQS_STANDARD_QUEUE_URL,
            "TargetQueueUrl": SQS_STANDARD_DEST_QUEUE_URL,
            "MessagesTransferBatchSize": self.messages_transfer_batch_size,
            "NumberOfMessagesToTransfer": number_of_messages_to_transfer,
            "ForceExecution": True
        }
        self.sqs_client_mock.receive_message.side_effect = \
            [{'Messages': RECEIVE_MESSAGE_RESPONSE_FROM_STANDARD['Messages'][:2]}]
        self.sqs_client_mock.get_queue_attributes.side_effect = INVALID_ATTRIBUTE_NAME_ERROR
        self.sqs_client_mock.delete_message_batch.return_value = \
            {'Successful': DELETE_MESSAGE_BATCH_RESPONSE['Successful']}
        self.sqs_client_mock.send_message_batch.return_value = \
            {'Successful': SEND_MESSAGE_BATCH_RESPONSE['Successful'][:2]}
        actual_response = transfer_messages(events, None)
        self.assertIsNotNone(actual_response)
        self.assertEqual(number_of_messages_to_transfer, actual_response['NumberOfMessagesTransferredToTarget'])
        self.assertEqual(0, actual_response['NumberOfMessagesFailedToDeleteFromSource'])
        self.assertEqual(0, actual_response['NumberOfMessagesFailedToSendToTarget'])
        self.assertIsNotNone(actual_response['TimeElapsed'])
        self.sqs_client_mock.get_queue_attributes.assert_has_calls([
            call(QueueUrl=SQS_STANDARD_QUEUE_URL, AttributeNames=['FifoQueue']),
            call(QueueUrl=SQS_STANDARD_DEST_QUEUE_URL, AttributeNames=['FifoQueue'])
        ])
        self.sqs_client_mock.receive_message.assert_called_with(QueueUrl=SQS_STANDARD_QUEUE_URL,
                                                                MaxNumberOfMessages=number_of_messages_to_transfer,
                                                                MessageAttributeNames=['All'],
                                                                AttributeNames=['All'],
                                                                WaitTimeSeconds=0)
        self.sqs_client_mock.send_message_batch.assert_called_with(QueueUrl=SQS_STANDARD_DEST_QUEUE_URL,
                                                                   Entries=MESSAGES_TO_SEND_TO_STANDARD[:2])
        self.sqs_client_mock.delete_message_batch.assert_called_with(QueueUrl=SQS_STANDARD_QUEUE_URL,
                                                                     Entries=DELETE_MESSAGE_ENTRIES[:2])

    def test_transfer_messages_different_queue_types_and_force_execution_false(self):
        """
        Test :func:`documents.util.scripts.src.sqs_util.transfer_messages`
        when ForceExecution input parameter is False and the types of queues are different
        """
        events = {
            "SourceQueueUrl": SQS_STANDARD_QUEUE_URL,
            "TargetQueueUrl": SQS_STANDARD_DEST_QUEUE_URL,
            "MessagesTransferBatchSize": self.messages_transfer_batch_size,
            "NumberOfMessagesToTransfer": self.number_of_messages_to_transfer,
            "ForceExecution": False
        }
        self.sqs_client_mock.get_queue_attributes.side_effect = [INVALID_ATTRIBUTE_NAME_ERROR, {}]
        self.assertRaises(ValueError, transfer_messages, events, None)
        self.sqs_client_mock.get_queue_attributes.assert_has_calls([
            call(QueueUrl=SQS_STANDARD_QUEUE_URL, AttributeNames=['FifoQueue']),
            call(QueueUrl=SQS_STANDARD_DEST_QUEUE_URL, AttributeNames=['FifoQueue'])
        ])
        self.sqs_client_mock.receive_message.assert_not_called()
        self.sqs_client_mock.send_message_batch.assert_not_called()
        self.sqs_client_mock.delete_message_batch.assert_not_called()

    def test_transfer_messages_different_error(self):
        """
        Test :func:`documents.util.scripts.src.sqs_util.transfer_messages`
        when there is another error occurred while checking the type of queue
        """
        events = {
            "SourceQueueUrl": SQS_STANDARD_QUEUE_URL,
            "TargetQueueUrl": SQS_STANDARD_DEST_QUEUE_URL,
            "MessagesTransferBatchSize": self.messages_transfer_batch_size,
            "NumberOfMessagesToTransfer": self.number_of_messages_to_transfer,
            "ForceExecution": False
        }
        self.sqs_client_mock.get_queue_attributes.side_effect = ClientError({'Error': {'Code': 'Other'}}, "")
        self.assertRaises(Exception, transfer_messages, events, None)
        self.sqs_client_mock.get_queue_attributes.assert_has_calls([
            call(QueueUrl=SQS_STANDARD_QUEUE_URL, AttributeNames=['FifoQueue']),
        ])
        self.sqs_client_mock.receive_message.assert_not_called()
        self.sqs_client_mock.send_message_batch.assert_not_called()
        self.sqs_client_mock.delete_message_batch.assert_not_called()

    def test_transfer_messages_from_standard_to_standard_multiple_loop(self):
        """
        Test :func:`documents.util.scripts.src.sqs_util.transfer_messages`
        when it makes multiple loops
        """
        messages_transfer_batch_size = 1
        events = {
            "SourceQueueUrl": SQS_STANDARD_QUEUE_URL,
            "TargetQueueUrl": SQS_STANDARD_DEST_QUEUE_URL,
            "MessagesTransferBatchSize": messages_transfer_batch_size,
            "NumberOfMessagesToTransfer": self.number_of_messages_to_transfer,
            "ForceExecution": True
        }
        self.sqs_client_mock.receive_message.side_effect = \
            [{'Messages': [RECEIVE_MESSAGE_RESPONSE_FROM_STANDARD['Messages'][0]]},
             {'Messages': [RECEIVE_MESSAGE_RESPONSE_FROM_STANDARD['Messages'][1]]},
             {'Messages': []}]
        self.sqs_client_mock.get_queue_attributes.side_effect = INVALID_ATTRIBUTE_NAME_ERROR
        self.sqs_client_mock.delete_message_batch.side_effect = \
            [{'Successful': [DELETE_MESSAGE_BATCH_RESPONSE['Successful'][0]]},
             {'Successful': [DELETE_MESSAGE_BATCH_RESPONSE['Successful'][1]]}]
        self.sqs_client_mock.send_message_batch.side_effect = \
            [{'Successful': [SEND_MESSAGE_BATCH_RESPONSE['Successful'][0]]},
             {'Successful': [SEND_MESSAGE_BATCH_RESPONSE['Successful'][1]]}]
        actual_response = transfer_messages(events, None)
        self.assertIsNotNone(actual_response)
        self.assertEqual(2, actual_response['NumberOfMessagesTransferredToTarget'])
        self.assertEqual(0, actual_response['NumberOfMessagesFailedToDeleteFromSource'])
        self.assertEqual(0, actual_response['NumberOfMessagesFailedToSendToTarget'])
        self.assertIsNotNone(actual_response['TimeElapsed'])
        self.sqs_client_mock.get_queue_attributes.assert_has_calls([
            call(QueueUrl=SQS_STANDARD_QUEUE_URL, AttributeNames=['FifoQueue']),
            call(QueueUrl=SQS_STANDARD_DEST_QUEUE_URL, AttributeNames=['FifoQueue'])
        ])
        self.sqs_client_mock.receive_message.assert_called_with(QueueUrl=SQS_STANDARD_QUEUE_URL,
                                                                MaxNumberOfMessages=messages_transfer_batch_size,
                                                                MessageAttributeNames=['All'],
                                                                AttributeNames=['All'],
                                                                WaitTimeSeconds=0)
        self.sqs_client_mock.send_message_batch.assert_has_calls([
            call(QueueUrl=SQS_STANDARD_DEST_QUEUE_URL, Entries=[MESSAGES_TO_SEND_TO_STANDARD[0]]),
            call(QueueUrl=SQS_STANDARD_DEST_QUEUE_URL, Entries=[MESSAGES_TO_SEND_TO_STANDARD[1]])
        ])
        self.sqs_client_mock.delete_message_batch.assert_has_calls([
            call(QueueUrl=SQS_STANDARD_QUEUE_URL, Entries=[DELETE_MESSAGE_ENTRIES[0]]),
            call(QueueUrl=SQS_STANDARD_QUEUE_URL, Entries=[DELETE_MESSAGE_ENTRIES[1]])
        ])

    def test_update_max_receive_count(self):
        events = {
            "MaxReceiveCount": 1,
            "SourceRedrivePolicy": json.dumps(self.redrive_policy)
        }
        response = update_max_receive_count(events, None)
        updated_redrive_policy = json.loads(response["RedrivePolicy"])
        self.assertIsNotNone(updated_redrive_policy["deadLetterTargetArn"])
        self.assertEqual(self.resource, updated_redrive_policy["deadLetterTargetArn"])
        self.assertIsNotNone(updated_redrive_policy["maxReceiveCount"])
        self.assertEqual(1, updated_redrive_policy["maxReceiveCount"])

    def test_update_max_receive_count_empty_events(self):
        events = {}
        self.assertRaises(KeyError, update_max_receive_count, events, None)

    def test_update_max_receive_count_empty_redrive_policy(self):
        events = {
            "MaxReceiveCount": 1,
            "SourceRedrivePolicy": ""
        }
        self.assertRaises(KeyError, update_max_receive_count, events, None)

    def test_update_max_receive_count_max_recieve_count_lower_than_range(self):
        events = {
            "MaxReceiveCount": 0,
            "SourceRedrivePolicy": json.dumps(self.redrive_policy)
        }
        self.assertRaises(KeyError, update_max_receive_count, events, None)

    def test_update_max_receive_count_max_recieve_count_upper_than_range(self):
        events = {
            "MaxReceiveCount": 1001,
            "SourceRedrivePolicy": json.dumps(self.redrive_policy)
        }
        self.assertRaises(KeyError, update_max_receive_count, events, None)

    def test_get_dead_letter_queue_url(self):
        events = {
            "SourceRedrivePolicy": json.dumps(self.redrive_policy)
        }
        self.sqs_client_mock.get_queue_url.return_value = \
            {'QueueUrl': self.queue_url}
        response = get_dead_letter_queue_url(events, None)
        self.sqs_client_mock.get_queue_url.assert_called_once_with(QueueName=self.queue_name)
        self.assertIsNotNone(response)
        self.assertEqual(self.queue_url, response['QueueUrl'])

    def test_get_dead_letter_queue_url_empty_events(self):
        events = {}
        self.assertRaises(KeyError, get_dead_letter_queue_url, events, None)

    def test_get_dead_letter_queue_url_empty_source_redrive_policy(self):
        events = {
            "SourceRedrivePolicy": ""
        }
        self.assertRaises(KeyError, get_dead_letter_queue_url, events, None)

    def test_receive_message_by_id(self):
        events = {
            'QueueUrl': SQS_STANDARD_QUEUE_URL,
            'MessageId': SUCCESSFUL_ID_1,
            'Count': 1
        }
        self.sqs_client_mock.receive_message.return_value = RECEIVE_MESSAGE_RESPONSE_FROM_STANDARD
        response = receive_message_by_id(events, None)
        self.assertIsNotNone(response['Messages'])
        self.assertEqual(RECEIVE_MESSAGE_RESPONSE_FROM_STANDARD['Messages'][0], response['Messages'][0])

    def test_receive_message_by_id_empty_events(self):
        events = {}
        self.assertRaises(KeyError, receive_message_by_id, events, None)

    def test_receive_message_by_id_max_number_of_messages_lower_than_range(self):
        events = {
            'QueueUrl': SQS_STANDARD_QUEUE_URL,
            'MessageId': SUCCESSFUL_ID_1,
            'MaxNumberOfMessages': 0
        }
        self.assertRaises(KeyError, receive_message_by_id, events, None)

    def test_receive_message_by_id_max_number_of_messages_upper_than_range(self):
        events = {
            'QueueUrl': SQS_STANDARD_QUEUE_URL,
            'MessageId': SUCCESSFUL_ID_1,
            'MaxNumberOfMessages': 11
        }
        self.assertRaises(KeyError, receive_message_by_id, events, None)
