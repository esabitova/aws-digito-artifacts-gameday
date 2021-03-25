import json
import uuid
import logging
from typing import List

import boto3

sqs_client = boto3.client("sqs")


def add_deny_in_sqs_policy(events: dict, context: dict) -> dict:
    """
    Add deny policy statement(-s) to the SQS policy whether it is empty or not
    :return: updated SQS policy with deny
    """
    if "ActionsToDeny" not in events or "Resource" not in events or "SourcePolicy" not in events:
        raise KeyError("Requires ActionsToDeny and Resource and SourcePolicy in events")

    actions_to_deny: List = events.get("ActionsToDeny")
    resource: str = events.get("Resource")
    source_policy: str = events.get("SourcePolicy")
    source_policy = None if source_policy.startswith("{{") else source_policy

    deny_policy_statement_id: str = f"DenyPolicyStatement-{uuid.uuid4()}"
    deny_policy_statement: dict = {
        "Effect": "Deny",
        "Sid": deny_policy_statement_id,
        "Principal": "*",
        "Action": actions_to_deny,
        "Resource": resource,
    }

    if source_policy is None:
        policy_id: str = f"DenyPolicy-{uuid.uuid4()}"
        sqs_policy: dict = {
            "Version": "2012-10-17",
            "Id": policy_id,
            "Statement": [deny_policy_statement]
        }
        return {"Policy": json.dumps(sqs_policy),
                "PolicySid": policy_id,
                "DenyPolicyStatementSid": deny_policy_statement_id}
    else:
        source_policy: dict = json.loads(source_policy)
        statement: List = source_policy.get("Statement")
        if statement is None or len(statement) == 0:
            raise KeyError("Requires not empty Statement in SQS Policy")
        statement.append(deny_policy_statement)
        return {"Policy": json.dumps(source_policy),
                "PolicySid": source_policy.get("Id"),
                "DenyPolicyStatementSid": deny_policy_statement_id}


def revert_sqs_policy(events: dict, context: dict) -> dict:
    """
    Revert SQS policy to the initial state by providing the backup policy
    """
    if "QueueUrl" not in events or "OptionalBackupPolicy" not in events:
        raise KeyError("Requires QueueUrl and OptionalBackupPolicy in events")

    queue_url: List = events.get("QueueUrl")
    optional_backup_policy: str = events.get("OptionalBackupPolicy")
    optional_backup_policy = None if optional_backup_policy.startswith("{{") else optional_backup_policy
    if optional_backup_policy is None:
        sqs_client.set_queue_attributes(QueueUrl=queue_url, Attributes={"Policy": ""})
    else:
        sqs_client.set_queue_attributes(QueueUrl=queue_url, Attributes={"Policy": str(optional_backup_policy)})


def update_sqs_redrive_policy(events: dict, context: dict) -> dict:
    """
    Update SQS Redrive Policy with new value of MaxReceiveCount
    """
    if "SourceRedrivePolicy" not in events or "MaxReceiveCount" not in events:
        raise KeyError("Requires SourceRedrivePolicy and MaxReceiveCount in events")

    source_redrive_policy: str = events.get("SourceRedrivePolicy")
    max_receive_count: int = events.get("MaxReceiveCount")
    if not 1 <= max_receive_count <= 1000:
        raise KeyError("Requires MaxReceiveCount to be in a range 1...1000")

    source_redrive_policy: dict = json.loads(source_redrive_policy)
    redrive_policy: dict = {
        "deadLetterTargetArn": source_redrive_policy.get("deadLetterTargetArn"),
        "maxReceiveCount": max_receive_count
    }
    return {"RedrivePolicy": json.dumps(redrive_policy)}


def get_dead_letter_queue_url(events: dict, context: dict) -> dict:
    """
    Retrieves dead-letter queue URL
    """
    if "SourceRedrivePolicy" not in events:
        raise KeyError("Requires SourceRedrivePolicy in events")

    source_redrive_policy: str = events.get("SourceRedrivePolicy")
    print(f'Redrive Policy is: {source_redrive_policy}')
    source_redrive_policy: dict = json.loads(source_redrive_policy)
    dead_letter_queue_arn: str = source_redrive_policy.get("deadLetterTargetArn")
    print(f'Dead Letter queue ARN is: {dead_letter_queue_arn}')
    dead_letter_queue_name: str = dead_letter_queue_arn.split(':', 5)[5]
    print(f'Dead Letter queue name is: {dead_letter_queue_name}')
    get_queue_url_response: dict = sqs_client.get_queue_url(QueueName=dead_letter_queue_name)
    print(f'Response of get_queue_url method is: {get_queue_url_response}')
    dead_letter_queue_url: str = get_queue_url_response['QueueUrl']
    print(f'Dead Letter queue URL is: {dead_letter_queue_url}')
    return {"QueueUrl": dead_letter_queue_url}
