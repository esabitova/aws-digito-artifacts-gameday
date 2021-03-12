import json
import uuid
from typing import List

import boto3

sqs_client = boto3.client('sqs')


def add_deny_in_sqs_policy(events: dict, context: dict) -> dict:
    """
    Add deny policy statement(-s) to the SQS policy whether it is empty or not
    :return: updated SQS policy with deny
    """
    if 'ActionsToDeny' not in events or 'Resource' not in events:
        raise KeyError('Requires ActionsToDeny and Resource  in events')

    actions_to_deny: List = events.get('ActionsToDeny')
    resource: str = events.get('Resource')
    optional_source_policy: str = events.get('OptionalSourcePolicy')

    deny_policy_statement_id: str = f'DenyPolicyStatement-{uuid.uuid4()}'
    actions: str = "[" + ', '.join(f'"{action}"' for action in actions_to_deny) + "]"
    deny_policy_statement: dict = {
        "Effect": "Deny",
        "Sid": deny_policy_statement_id,
        "Principal": "*",
        "Action": actions,
        "Resource": resource,
    }

    if optional_source_policy is None:
        policy_id: str = f'DenyPolicy-{uuid.uuid4()}'
        sqs_policy: dict = {
            "Version": "2012-10-17",
            "Id": policy_id,
            "Statement": [deny_policy_statement]
        }
        return {'SQSPolicy': json.dumps(sqs_policy),
                "PolicySid": policy_id,
                "DenyPolicyStatementSid": deny_policy_statement_id}
    else:
        source_policy: dict = json.loads(optional_source_policy)
        statement: List = source_policy.get('Statement')
        if statement is None:
            raise KeyError('Requires Statement in SQS Policy')
        statement.extend(deny_policy_statement)
        return {'SQSPolicy': json.dumps(source_policy),
                "PolicySid": source_policy.get('Id'),
                "DenyPolicyStatementSid": deny_policy_statement_id}
