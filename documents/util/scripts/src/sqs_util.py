import json
import logging
import time
import uuid
from datetime import datetime
from typing import List, Callable, Optional

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


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


def revert_sqs_policy(events: dict, context: dict) -> None:
    """
    Revert SQS policy to the initial state by providing the backup policy
    """
    if "QueueUrl" not in events or "OptionalBackupPolicy" not in events:
        raise KeyError("Requires QueueUrl and OptionalBackupPolicy in events")
    sqs_client = boto3.client("sqs")
    queue_url: str = events.get("QueueUrl")
    optional_backup_policy: str = events.get("OptionalBackupPolicy")
    optional_backup_policy = None if optional_backup_policy.startswith("{{") else optional_backup_policy
    if optional_backup_policy is None:
        sqs_client.set_queue_attributes(QueueUrl=queue_url, Attributes={"Policy": ""})
    else:
        sqs_client.set_queue_attributes(QueueUrl=queue_url, Attributes={"Policy": str(optional_backup_policy)})


def send_message_of_size(events, context):
    """
    Sends a message of given size in bytes. Character u'a' is equal to one byte
    """
    sqs_client = boto3.client("sqs")
    queue_url = events['QueueUrl']
    message_size = events['MessageSize']
    message_body = 'a' * message_size

    is_fifo = queue_url[-5:] == '.fifo'
    if is_fifo:
        message_deduplication_id = events['MessageDeduplicationId']
        message_group_id = 'digito-capacity-failure-test'
        response = sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=message_body,
            MessageGroupId=message_group_id,
            MessageDeduplicationId=message_deduplication_id
        )
    else:
        response = sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=message_body
        )
    return response


def get_message_receipt_handle(queue_url: str, message_id: str, timeout: int):
    """
    Loop through all messages on SQS queue, find message by ID and return its ReceiptHandle
    :param queue_url The URL of the queue
    :param message_id The message ID
    :param timeout Max time to wait until message found
    :return ReceiptHandle of the message
    """
    sqs_client = boto3.client("sqs")
    start = datetime.now()

    while True:
        response = sqs_client.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=10
        )

        if 'Messages' in response and len(response['Messages']):
            for message in response['Messages']:
                if message['MessageId'] == message_id:
                    return message['ReceiptHandle']

        if (datetime.now() - start).total_seconds() > timeout:
            raise Exception(f'Message {message_id} not found before timeout')


def delete_message_by_id(event, context):
    """
    Delete message by its ID
    """
    sqs_client = boto3.client("sqs")
    queue_url = event['QueueUrl']
    message_id = event['MessageId']
    timeout = int(event.get('TimeOut', 100))
    receipt_handle = get_message_receipt_handle(queue_url, message_id, timeout)
    response = sqs_client.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
    return response


def transform_message_and_attributes(message: dict) -> dict:
    """
    General method to transform one message
    :param message: Message to transform
    :return: transformed message
    """
    message_to_send = {'Id': message.get('MessageId'),
                       'MessageBody': message.get('Body')}
    if message.get('MessageAttributes') is not None:
        message_to_send['MessageAttributes'] = message.get('MessageAttributes')
    attributes = message.get('Attributes')
    if attributes is not None:
        aws_trace_header = attributes.get('AWSTraceHeader')
        if aws_trace_header is not None:
            message_to_send['MessageSystemAttributes'] = \
                {'AWSTraceHeader': {'StringValue': aws_trace_header,
                                    'DataType': 'String'}}
    return message_to_send


def transform_message_from_fifo_to_fifo(message: dict) -> dict:
    """
    Transform one message from FIFO to FIFO
    :param message: Message to transform
    :return: transformed message
    """
    message_to_send = transform_message_and_attributes(message)

    attributes = message.get('Attributes')
    if attributes is not None:
        message_to_send['MessageDeduplicationId'] = attributes.get('MessageDeduplicationId')
        message_to_send['MessageGroupId'] = str(attributes.get('MessageGroupId'))
    return message_to_send


def transform_message_from_standard_to_fifo(message: dict) -> dict:
    """
    Transform one message from Standard to FIFO
    :param message: Message to transform
    :return: transformed message
    """
    message_to_send = transform_message_and_attributes(message)
    message_to_send['MessageDeduplicationId'] = str(uuid.uuid4())
    message_to_send['MessageGroupId'] = str(uuid.uuid4())
    return message_to_send


def transform_messages(messages: List[dict], transform_message_function: Callable) -> List[dict]:
    """
    Transform all messages
    :param messages: messages to transform
    :param transform_message_function: method to transform one message
    :return: transformed messages
    """
    transformed_messages: List[dict] = []
    for message in messages:
        message = transform_message_function(message)
        transformed_messages.append(message)
    return transformed_messages


def send_messages(messages_to_send: List[dict], target_queue_url: str) -> dict:
    """
    Send messages by batch operation
    :param messages_to_send: messages to send
    :param target_queue_url: URL of the queue to send
    :return: response of send_message_batch method
    """
    sqs_client = boto3.client("sqs")
    send_message_batch_response: dict = sqs_client.send_message_batch(QueueUrl=target_queue_url,
                                                                      Entries=messages_to_send)
    return send_message_batch_response


def receive_messages(source_queue_url: str, messages_transfer_batch_size: int) -> Optional[List[dict]]:
    """
    Receive messages
    :param messages_transfer_batch_size: how many messages to receive
    :param source_queue_url:  URL of the queue where from messages are received
    :return: response of receive_message method
    """
    sqs_client = boto3.client("sqs")
    receive_message_response: dict = \
        sqs_client.receive_message(QueueUrl=source_queue_url,
                                   MaxNumberOfMessages=messages_transfer_batch_size,
                                   MessageAttributeNames=['All'],
                                   AttributeNames=['All'])
    return receive_message_response.get('Messages')


def transfer_messages(events: dict, context: dict) -> dict:
    """
    Move received_messages from one queue to another.
    """
    if "SourceQueueUrl" not in events or "TargetQueueUrl" not in events \
            or "NumberOfMessagesToTransfer" not in events or "ForceExecution" not in events \
            or "MessagesTransferBatchSize" not in events:
        raise KeyError("Requires SourceQueueUrl and TargetQueueUrl and NumberOfMessagesToTransfer and "
                       "MessagesTransferBatchSize and ForceExecution in events")
    sqs_client = boto3.client("sqs")
    start_execution = datetime.utcnow()

    source_queue_url: str = events['SourceQueueUrl']
    target_queue_url: str = events['TargetQueueUrl']
    force_execution: bool = bool(events['ForceExecution'])
    number_of_messages_to_transfer: int = int(events['NumberOfMessagesToTransfer'])
    messages_transfer_batch_size: int = int(events['MessagesTransferBatchSize'])

    is_source_queue_fifo: bool = is_queue_fifo(source_queue_url, sqs_client)
    is_target_queue_fifo: bool = is_queue_fifo(target_queue_url, sqs_client)

    if force_execution is False and is_source_queue_fifo != is_target_queue_fifo:
        raise ValueError(f'The source queue and target queue have different types when ForceExecution '
                         f'parameter is {force_execution}: ')

    number_of_messages_transferred_to_target = 0
    number_of_messages_failed_to_send_to_target = 0
    number_of_messages_failed_to_delete_from_source = 0
    start = now = int(time.time())
    max_duration_seconds = 9 * 60
    loop_count = 1
    number_of_messages_received_from_source = 0

    while number_of_messages_received_from_source < number_of_messages_to_transfer \
            and (now - start) < max_duration_seconds:
        logger.debug(f'Entered into loop #{loop_count} '
                     f'with number_of_messages_transferred_to_target < number_of_messages_to_transfer = '
                     f'{number_of_messages_transferred_to_target} < {number_of_messages_to_transfer}, '
                     f'(now - start) < max_duration_seconds = {now - start} < {max_duration_seconds}')

        messages_transfer_batch_size_for_each_call = \
            min((number_of_messages_to_transfer - number_of_messages_received_from_source),
                messages_transfer_batch_size)

        received_messages: Optional[List[dict]] = receive_messages(source_queue_url,
                                                                   messages_transfer_batch_size_for_each_call)
        if received_messages is None or len(received_messages) == 0:
            return get_statistics(loop_count, now, number_of_messages_failed_to_delete_from_source,
                                  number_of_messages_failed_to_send_to_target,
                                  number_of_messages_transferred_to_target, source_queue_url, start,
                                  start_execution, max_duration_seconds)
        else:
            number_of_messages_received_from_source += len(received_messages)

        messages_to_send: List[dict] = []
        if is_source_queue_fifo and is_target_queue_fifo:  # If both queues are FIFO
            messages_to_send = transform_messages(received_messages, transform_message_from_fifo_to_fifo)
        elif not is_source_queue_fifo and not is_target_queue_fifo:  # If both queues are standard
            messages_to_send = transform_messages(received_messages, transform_message_and_attributes)
        elif is_source_queue_fifo and not is_target_queue_fifo:
            messages_to_send = transform_messages(received_messages, transform_message_and_attributes)
        elif not is_source_queue_fifo and is_target_queue_fifo:
            messages_to_send = transform_messages(received_messages, transform_message_from_standard_to_fifo)

        send_message_batch_response: dict = send_messages(messages_to_send, target_queue_url)
        successfully_sent_results = send_message_batch_response.get('Successful')
        if successfully_sent_results is not None:
            successfully_sent_results_number = len(successfully_sent_results)
            logger.info(f'Succeed to send {successfully_sent_results_number} message(-s) '
                        f'during the loop #{loop_count}: '
                        f'{successfully_sent_results}')

            message_id_to_receipt_handle = {message.get('MessageId'): message.get('ReceiptHandle')
                                            for message in received_messages}
            delete_message_entries: List = [{'Id': result.get('Id'),
                                             'ReceiptHandle': message_id_to_receipt_handle.get(result.get('Id'))}
                                            for result in successfully_sent_results]
            delete_message_batch_response: dict = sqs_client.delete_message_batch(QueueUrl=source_queue_url,
                                                                                  Entries=delete_message_entries)
            failed_delete_messages: List[dict] = delete_message_batch_response.get('Failed')
            if failed_delete_messages is not None:
                failed_delete_messages_number = len(failed_delete_messages)
                logger.info(f'Failed to delete {failed_delete_messages_number} message(-s) '
                            f'during the loop #{loop_count}: '
                            f'{failed_delete_messages}')
                number_of_messages_failed_to_delete_from_source += failed_delete_messages_number

            succeed_delete_messages = delete_message_batch_response.get('Successful')
            if succeed_delete_messages is not None:
                logger.info(f'Succeed to delete {len(succeed_delete_messages)} message(-s) '
                            f'during the loop #{loop_count}: '
                            f'{succeed_delete_messages}')
                number_of_messages_transferred_to_target += len(succeed_delete_messages)

        failed_send_results: dict = send_message_batch_response.get('Failed')
        if failed_send_results is not None:
            failed_send_results_number = len(failed_send_results)
            logger.info(f'Failed to send {failed_send_results_number} message(-s) '
                        f'during the loop #{loop_count}: '
                        f'{failed_send_results}')
            number_of_messages_failed_to_send_to_target += failed_send_results_number

        now = int(time.time())
        loop_count += 1

    return get_statistics(loop_count, now, number_of_messages_failed_to_delete_from_source,
                          number_of_messages_failed_to_send_to_target,
                          number_of_messages_transferred_to_target, source_queue_url, start,
                          start_execution, max_duration_seconds)


def get_statistics(loop_count: int, now, number_of_messages_failed_to_delete_from_source: int,
                   number_of_messages_failed_to_send_to_target: int,
                   number_of_messages_transferred_to_target: int,
                   source_queue_url: str, start, start_execution, max_duration_seconds: int):
    statistics = {'NumberOfMessagesTransferredToTarget': number_of_messages_transferred_to_target,
                  'NumberOfMessagesFailedToDeleteFromSource':
                      number_of_messages_failed_to_delete_from_source,
                  'NumberOfMessagesFailedToSendToTarget': number_of_messages_failed_to_send_to_target,
                  'TimeElapsed': str((datetime.utcnow() - start_execution).total_seconds())}
    logger.info(f'Quiting the loop to receive the messages from source queue with URL = {source_queue_url} '
                f'because there are no messages received during the loop #{loop_count} and {(now - start)} '
                f'second(-s) of script\'s execution or the maximum time in {max_duration_seconds} was elapsed. '
                f'Statistics: {statistics}')
    return statistics


def is_queue_fifo(queue_url: str, sqs_client):
    try:
        sqs_client.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['FifoQueue'])
    except ClientError as e:
        if e.response['Error']['Code'] == 'InvalidAttributeName':
            logger.info(f'The queue with url = {queue_url} is not a FIFO')
            return False
        else:
            logger.error(e)
            raise e
    return True