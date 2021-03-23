import json
import unittest
import uuid
from unittest.mock import patch, MagicMock

import pytest

from documents.util.scripts.src.sqs_util import add_deny_in_sqs_policy, revert_sqs_policy


@pytest.mark.unit_test
class TestSqsUtil(unittest.TestCase):
    def setUp(self):
        self.empty_policy = {"Policy": ""}
        self.queue_url = "https://sqs.us-east-2.amazonaws.com/123456789012/MyQueue"
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
                                                                 Attributes=str(self.empty_policy))
