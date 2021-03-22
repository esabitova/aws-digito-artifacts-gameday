import logging
from datetime import datetime
from typing import List, Tuple, Union

import boto3

import botocore

sqs_client = boto3.client("sqs")


def transfer_messages(events: dict, context: dict) -> dict:
    def receive_messages_from_fifo(queue_url: str, max_number_of_messages: int) -> List[dict]:
        return sqs_client.receive_message(QueueUrl=queue_url,
                                          MaxNumberOfMessages=max_number_of_messages,
                                          AttributeNames=['All'])

    def receive_messages_from_standard(queue_url: str, max_number_of_messages: int):
        return sqs_client.receive_message(QueueUrl=queue_url,
                                          MaxNumberOfMessages=max_number_of_messages,
                                          AttributeNames=['All'])

    def send_messages_to_fifo(queue_url: str, messages_to_send: List[dict]) -> dict:
        return sqs_client.receive_message(QueueUrl=queue_url,
                                          Entries=messages_to_send)

    def send_messages_to_standard(queue_url: str, messages_to_send: List[dict]) -> dict:
        return sqs_client.receive_message(QueueUrl=queue_url,
                                          Entries=messages_to_send)

    def delete_messages(queue_url: str, messages_to_delete: List[dict], successfully_sent_results: List[dict]) -> dict:
        entries: List = []
        if successfully_sent_results is not None:
            for result in successfully_sent_results:
                message_id = result.get('MessageId')
                receipt_handle = find_receipt_handle(messages_to_delete, message_id)
                entries.append({'Id': message_id, 'ReceiptHandle': receipt_handle})

        delete_message_batch_response: dict = sqs_client.delete_message_batch(QueueUrl=queue_url, Entries=entries)
        return delete_message_batch_response.get('Failed')

    def get_statistics(send_messages_response: dict) -> Tuple[int, int]:
        successful_messages: dict = send_messages_response.get('Successful')
        if successful_messages is not None:
            successful_number = len(successful_messages)
        else:
            successful_number = 0

        failed_messages: dict = send_messages_response.get('Failed')
        if failed_messages is not None:
            failed_number = len(failed_messages)
        else:
            failed_number = 0

        return successful_number, failed_number

    def find_receipt_handle(messages_to_delete: List[dict], expected_message_id: str) -> Union[str, None]:
        if messages_to_delete is not None:
            for message in messages_to_delete:
                if expected_message_id == message.get('MessageId'):
                    return message.get('ReceiptHandle')
        return None

    """
    Move messages from one queue to another.
    """
    if "SourceQueueUrl" not in events or "TargetQueueUrl" not in events \
            or "NumberOfMessagesToTransfer" not in events or "MessagesTransferBatchSize" not in events:
        raise KeyError("Requires SourceQueueUrl and TargetQueueUrl and NumberOfMessagesToTransfer and "
                       "MessagesTransferBatchSize in events")

    start_execution = datetime.utcnow()
    source_queue_url: str = events['SourceQueueUrl']
    target_queue_url: str = events['TargetQueueUrl']
    number_of_messages_to_transfer: int = int(events['NumberOfMessagesToTransfer'])
    messages_transfer_batch_size: int = int(events['MessagesTransferBatchSize'])

    is_source_queue_fifo = True
    try:
        sqs_client.get_queue_attributes(QueueUrl=source_queue_url, AttributeNames=['FifoQueue'])
    except botocore.exceptions.BotoCoreError:  # todo replace by more narrow exception
        is_source_queue_fifo = False
        logging.info(f'Source queue with url = {source_queue_url} is not FIFO')

    is_target_queue_fifo = True
    try:
        sqs_client.get_queue_attributes(QueueUrl=target_queue_url, AttributeNames=['FifoQueue'])
    except botocore.exceptions.BotoCoreError:  # todo replace by more narrow exception
        is_target_queue_fifo = False
        logging.info(f'Target queue with url = {target_queue_url} is not FIFO')

    number_of_messages_to_transferred = 0
    number_of_messages_transferred_to_target = 0
    number_of_messages_failed_to_send_to_target = 0
    number_of_messages_failed_to_delete_from_source = 0
    start = now = datetime.now().seconds
    max_duration_seconds = 9 * 60
    while number_of_messages_to_transferred < number_of_messages_to_transfer or (now - start) < max_duration_seconds:
        response: dict = {}
        if is_source_queue_fifo and is_target_queue_fifo:  # If both queues are FIFO
            messages: List[dict] = receive_messages_from_fifo(source_queue_url, messages_transfer_batch_size)
            response: dict = send_messages_to_fifo(target_queue_url, messages)
        elif not is_source_queue_fifo and not is_target_queue_fifo:  # If both queues are standard
            messages: List[dict] = receive_messages_from_standard(source_queue_url, messages_transfer_batch_size)
            response: dict = send_messages_to_standard(target_queue_url, messages)
        elif is_source_queue_fifo and not is_target_queue_fifo:
            messages: List[dict] = receive_messages_from_fifo(source_queue_url, messages_transfer_batch_size)
            response: dict = send_messages_to_standard(target_queue_url, messages)
        elif not is_source_queue_fifo and is_target_queue_fifo:
            messages: List[dict] = receive_messages_from_standard(source_queue_url, messages_transfer_batch_size)
            response: dict = send_messages_to_fifo(target_queue_url, messages)

        delete_messages(source_queue_url, messages, response.get('Successful'))
        successful, failed = get_statistics(response)
        number_of_messages_transferred_to_target += successful
        number_of_messages_failed_to_send_to_target += failed
        now = datetime.now().seconds
        number_of_messages_to_transferred += len(messages)

    return {'NumberOfMessagesTransferredToTarget': number_of_messages_transferred_to_target,
            'NumberOfMessagesFailedToDeleteFromSource': number_of_messages_failed_to_delete_from_source,
            'NumberOfMessagesFailedToSendToTarget': number_of_messages_failed_to_send_to_target,
            'TimeElapsed': str((datetime.utcnow() - start_execution).total_seconds())}
