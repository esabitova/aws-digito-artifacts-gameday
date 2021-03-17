import json
import uuid
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
        policy: dict = {
            "Policy": {
                "Version": "2012-10-17",
                "Id": uuid.uuid4().__str__(),
                "Statement": []
            }
        }
        sqs_client.set_queue_attributes(QueueUrl=queue_url, Attributes=str(policy))
    else:
        sqs_client.set_queue_attributes(QueueUrl=queue_url, Attributes={"Policy": str(optional_backup_policy)})
