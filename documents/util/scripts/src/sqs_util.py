import time
import uuid
from datetime import datetime
from typing import List

import boto3
from botocore.exceptions import ClientError

sqs_client = boto3.client("sqs")


def transfer_messages(events: dict, context: dict) -> dict:
    """
    Move messages from one queue to another.
    """
    if "SourceQueueUrl" not in events or "TargetQueueUrl" not in events \
            or "NumberOfMessagesToTransfer" not in events or "ForceExecution" not in events \
            or "MessagesTransferBatchSize" not in events:
        raise KeyError("Requires SourceQueueUrl and TargetQueueUrl and NumberOfMessagesToTransfer and "
                       "MessagesTransferBatchSize and ForceExecution in events")

    start_execution = datetime.utcnow()

    source_queue_url: str = events['SourceQueueUrl']
    target_queue_url: str = events['TargetQueueUrl']
    force_execution: bool = bool(events['ForceExecution'])
    number_of_messages_to_transfer: int = int(events['NumberOfMessagesToTransfer'])
    messages_transfer_batch_size: int = int(events['MessagesTransferBatchSize'])

    is_source_queue_fifo: bool = True
    try:
        sqs_client.get_queue_attributes(QueueUrl=source_queue_url, AttributeNames=['FifoQueue'])
    except ClientError as e:
        if e.response['Error']['Code'] == 'InvalidAttributeName':
            is_source_queue_fifo = False
            print(f'Source queue with url = {source_queue_url} is not FIFO')
        else:
            print(e)
            raise e

    is_target_queue_fifo: bool = True
    try:
        sqs_client.get_queue_attributes(QueueUrl=target_queue_url, AttributeNames=['FifoQueue'])
    except ClientError as e:
        if e.response['Error']['Code'] == 'InvalidAttributeName':
            is_target_queue_fifo = False
            print(f'Target queue with url = {target_queue_url} is not FIFO')
        else:
            print(e)
            raise e

    if force_execution is False and is_source_queue_fifo != is_target_queue_fifo:
        raise ValueError(f'The source queue and target queue have different types when ForceExecution '
                         f'parameter is {force_execution}: ')

    number_of_messages_transferred = 0
    number_of_messages_transferred_to_target = 0
    number_of_messages_failed_to_send_to_target = 0
    number_of_messages_failed_to_delete_from_source = 0
    start = now = int(time.time())
    max_duration_seconds = 9 * 60
    loop_count = 1

    while number_of_messages_transferred < number_of_messages_to_transfer and (now - start) < max_duration_seconds:
        print(f'Entered into loop #{loop_count} with number_of_messages_transferred < number_of_messages_to_transfer = '
              f'{number_of_messages_transferred} < {number_of_messages_to_transfer}, '
              f'(now - start) < max_duration_seconds = {now - start} < {max_duration_seconds}')

        send_message_batch_response: dict = {}

        if is_source_queue_fifo and is_target_queue_fifo:  # If both queues are FIFO
            receive_message_response: dict = \
                sqs_client.receive_message(QueueUrl=source_queue_url,
                                           MaxNumberOfMessages=messages_transfer_batch_size,
                                           MessageAttributeNames=['All'],
                                           AttributeNames=['All'])
            print(f'receive_message response: {receive_message_response}')
            messages_to_send: List[dict] = []
            received_messages: List[dict] = receive_message_response.get('Messages')

            if received_messages is not None:
                for received_message in received_messages:
                    deduplication_id = received_message.get('Attributes').get('MessageDeduplicationId')
                    message_group_id = received_message.get('Attributes').get('MessageGroupId')
                    message_to_send = {'Id': received_message.get('MessageId'),
                                       'MessageBody': received_message.get('Body'),
                                       'MessageDeduplicationId': deduplication_id,
                                       'MessageGroupId': message_group_id}

                    if received_message.get('MessageAttributes') is not None:
                        message_to_send['MessageAttributes'] = received_message.get('MessageAttributes')
                    attributes = received_message.get('Attributes')
                    if attributes is not None:
                        aws_trace_header = attributes.get('AWSTraceHeader')
                        if aws_trace_header is not None:
                            message_to_send['MessageSystemAttributes'] = \
                                {'AWSTraceHeader': {'StringValue': aws_trace_header,
                                                    'DataType': 'String'}}
                    messages_to_send.append(message_to_send)

                print(f'Executing send_message_batch with arguments: QueueUrl={target_queue_url}, '
                      f'Entries={messages_to_send}')
                send_message_batch_response: dict = sqs_client.send_message_batch(QueueUrl=target_queue_url,
                                                                                  Entries=messages_to_send)
                print(f'Received send_message_batch response: {send_message_batch_response}')
            else:
                statistics = {'NumberOfMessagesTransferredToTarget': number_of_messages_transferred_to_target,
                              'NumberOfMessagesFailedToDeleteFromSource':
                                  number_of_messages_failed_to_delete_from_source,
                              'NumberOfMessagesFailedToSendToTarget': number_of_messages_failed_to_send_to_target,
                              'TimeElapsed': str((datetime.utcnow() - start_execution).total_seconds())}
                print(f'Quiting the loop to receive the messages from source queue with URL: {source_queue_url} '
                      f'because there are no messages received during the loop #{loop_count} and {(now - start)} '
                      f'second(-s) of script\'s execution. Statistics: {statistics}')
                return statistics

        elif not is_source_queue_fifo and not is_target_queue_fifo:  # If both queues are standard
            receive_message_response: dict = \
                sqs_client.receive_message(QueueUrl=source_queue_url,
                                           MaxNumberOfMessages=messages_transfer_batch_size,
                                           MessageAttributeNames=['All'],
                                           AttributeNames=['All'])
            print(f'receive_message response: {receive_message_response}')
            received_messages: List[dict] = receive_message_response.get('Messages')

            if received_messages is not None:
                for received_message in received_messages:
                    message_to_send = {'Id': received_message.get('MessageId'),
                                       'MessageBody': received_message.get('Body')}
                    if received_message.get('MessageAttributes') is not None:
                        message_to_send['MessageAttributes'] = received_message.get('MessageAttributes')
                    attributes = received_message.get('Attributes')
                    if attributes is not None:
                        aws_trace_header = attributes.get('AWSTraceHeader')
                        if aws_trace_header is not None:
                            message_to_send['MessageSystemAttributes'] = \
                                {'AWSTraceHeader': {'StringValue': aws_trace_header,
                                                    'DataType': 'String'}}
                    messages_to_send.append(message_to_send)

                print(f'Executing send_message_batch with arguments: QueueUrl={target_queue_url}, '
                      f'Entries={messages_to_send}')
                send_message_batch_response: dict = sqs_client.send_message_batch(QueueUrl=target_queue_url,
                                                                                  Entries=messages_to_send)
                print(f'Received send_message_batch response: {send_message_batch_response}')
            else:
                statistics = {'NumberOfMessagesTransferredToTarget': number_of_messages_transferred_to_target,
                              'NumberOfMessagesFailedToDeleteFromSource':
                                  number_of_messages_failed_to_delete_from_source,
                              'NumberOfMessagesFailedToSendToTarget': number_of_messages_failed_to_send_to_target,
                              'TimeElapsed': str((datetime.utcnow() - start_execution).total_seconds())}
                print(f'Quiting the loop to receive the messages from source queue with URL: {source_queue_url} '
                      f'because there are no messages received during the loop #{loop_count} and {(now - start)} '
                      f'second(-s) of script\'s execution. Statistics: {statistics}')
                return statistics
        elif is_source_queue_fifo and not is_target_queue_fifo:
            receive_message_response: dict = \
                sqs_client.receive_message(QueueUrl=source_queue_url,
                                           MaxNumberOfMessages=messages_transfer_batch_size,
                                           AttributeNames=['All'])
            for message in receive_message_response.get('Messages'):
                if 'MessageDeduplicationId' in receive_message_response:
                    del message['MessageDeduplicationId']
                if 'MessageGroupId' in receive_message_response:
                    del message['MessageGroupId']
            send_message_batch_response: dict = sqs_client.receive_message(QueueUrl=target_queue_url,
                                                                           Entries=receive_message_response.get(
                                                                               'Messages'))

        elif not is_source_queue_fifo and is_target_queue_fifo:
            receive_message_response: dict = \
                sqs_client.receive_message(QueueUrl=source_queue_url,
                                           MaxNumberOfMessages=messages_transfer_batch_size,
                                           AttributeNames=['All'])
            for message in receive_message_response.get('Messages'):
                message['MessageDeduplicationId'] = str(uuid.uuid4())
                message['MessageGroupId'] = str(uuid.uuid4())
            send_message_batch_response: dict = sqs_client.send_message_batch(QueueUrl=target_queue_url,
                                                                              Entries=receive_message_response.get(
                                                                                  'Messages'))

        successfully_sent_results = send_message_batch_response.get('Successful')
        print(f'Successfully sent results from send_message_batch_response response: {successfully_sent_results}')

        entries: List = []

        if successfully_sent_results is not None:
            number_of_messages_transferred_to_target += len(successfully_sent_results)

            for result in successfully_sent_results:
                result_id = result.get('Id')
                for message in receive_message_response.get('Messages'):
                    if result_id == message.get('MessageId'):
                        receipt_handle = message.get('ReceiptHandle')
                        entries.append({'Id': result_id, 'ReceiptHandle': receipt_handle})
                        print(f'Found and added entry to delete message: Id={result_id}, '
                              f'ReceiptHandle={receipt_handle}')
                print(f'Executing delete_message_batch with arguments: QueueUrl={source_queue_url}, Entries= {entries}')
                delete_message_batch_response: dict = sqs_client.delete_message_batch(QueueUrl=source_queue_url,
                                                                                      Entries=entries)
                print(f'Received delete_message_batch response: {delete_message_batch_response}')
                failed_delete_message = delete_message_batch_response.get('Failed')
                if failed_delete_message is not None:
                    number_of_messages_failed_to_delete_from_source += len(failed_delete_message)

            failed_send_results: dict = send_message_batch_response.get('Failed')
            if failed_send_results is not None:
                number_of_messages_failed_to_send_to_target += len(failed_send_results)

        now = int(time.time())
        if receive_message_response.get('Messages') is not None:
            number_of_messages_transferred += len(receive_message_response.get('Messages'))
        loop_count += 1

    return {'NumberOfMessagesTransferredToTarget': number_of_messages_transferred_to_target,
            'NumberOfMessagesFailedToDeleteFromSource': number_of_messages_failed_to_delete_from_source,
            'NumberOfMessagesFailedToSendToTarget': number_of_messages_failed_to_send_to_target,
            'TimeElapsed': str((datetime.utcnow() - start_execution).total_seconds())}
