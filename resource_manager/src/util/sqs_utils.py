import logging
import json
import time
from boto3 import Session
from botocore.exceptions import ClientError


def send_message_to_standard_queue(boto3_session, queue_url: str, body: str, message_attributes: dict = None) -> dict:
    """
    Use send_message aws method to send message to queue
    :param boto3_session boto3 client session
    :param queue_url The URL of the queue
    :param message_attributes Message attributes
    :param body Message body
    """
    sqs_client = boto3_session.client('sqs')
    logging.debug(f'Arguments for send_message method: QueueUrl={queue_url}, MessageBody={body}, '
                  f'MessageAttributes={message_attributes}')
    if message_attributes is not None:
        response = sqs_client.send_message(QueueUrl=queue_url, MessageBody=body, MessageAttributes=message_attributes)
    else:
        response = sqs_client.send_message(QueueUrl=queue_url, MessageBody=body)
    logging.debug(f'Response of send_message method for standard queue: {response}')
    return response


def send_message_to_fifo_queue(boto3_session, queue_url: str, body: str, message_group_id: str, token: str,
                               message_attributes: dict = None) -> dict:
    """
    Use send_message aws method to send message to queue
    :param boto3_session boto3 client session
    :param queue_url The URL of the queue
    :param body Message body
    :param token Unique token for MessageDeduplicationId for FIFO queue message
    :param message_group_id MessageGroupId for FIFO queue
    """
    sqs_client = boto3_session.client('sqs')
    logging.debug(f'Arguments for send_message method: QueueUrl={queue_url}, MessageBody={body}, '
                  f'MessageDeduplicationId={token}, MessageGroupId= {message_group_id}'
                  f', MessageAttributes={message_attributes}')
    if message_attributes is not None:
        response = sqs_client.send_message(QueueUrl=queue_url, MessageBody=body, MessageDeduplicationId=token,
                                           MessageGroupId=message_group_id, MessageAttributes=message_attributes)
    else:
        response = sqs_client.send_message(QueueUrl=queue_url, MessageBody=body, MessageDeduplicationId=token,
                                           MessageGroupId=message_group_id)
    logging.debug(f'Response of send_message method for FIFO queue: {response}')
    return response


def send_messages_until_access_denied(boto3_session, queue_url, time_to_wait):
    """
    Keep sending messages until access denied is caught
    Raise error if max time to wait reached or any other error is caught
    :param boto3_session boto3 client session
    :param queue_url The URL of the queue
    :param time_to_wait Max time in seconds to keep sending
    """
    time_to_wait = int(time_to_wait)
    start_time = time.time()
    elapsed_time = 0
    while elapsed_time < time_to_wait:
        try:
            send_message_to_standard_queue(
                boto3_session, queue_url, 'This is message',
                {'test_attribute_name_1': {'StringValue': 'test_attribute_value_1', 'DataType': 'String'}}
            )
        except ClientError as error:
            if error.response['Error']['Code'] == 'AccessDenied':
                logging.info('Message sending failed due to access denied')
                return
            else:
                raise error
        time.sleep(20)
        elapsed_time = time.time() - start_time
    logging.info(f'Sending messages ended after {time_to_wait} seconds')
    raise Exception('Sending messages timed out, expected access denied error')


def send_messages_until_success(boto3_session, queue_url, time_to_wait, number_of_messages):
    """
    Keep sending messages until number of messages sent or time to wait is reached
    Ignore access denied error, raise error in any other case
    :param boto3_session boto3 client session
    :param queue_url The URL of the queue
    :param time_to_wait Time in seconds to keep sending
    :param number_of_messages Number of successful sends required
    """
    time_to_wait = int(time_to_wait)
    number_of_messages = int(number_of_messages)
    start_time = time.time()
    elapsed_time = 0
    messages_sent = 0
    while elapsed_time < time_to_wait and messages_sent < number_of_messages:
        try:
            send_message_to_standard_queue(
                boto3_session, queue_url, 'This is message',
                {'test_attribute_name_1': {'StringValue': 'test_attribute_value_1', 'DataType': 'String'}}
            )
            messages_sent += 1
        except ClientError as error:
            if error.response['Error']['Code'] == 'AccessDenied':
                logging.info('Message sending failed due to access denied, continue sending')
            else:
                raise error
        time.sleep(20)
        elapsed_time = time.time() - start_time
    if messages_sent == 0:
        raise Exception('No messages were sent before timeout')
    logging.info(f'Sent {messages_sent} messages')


def get_number_of_messages(boto3_session: Session, queue_url: str):
    """
    Use get_queue_attributes aws method to get ApproximateNumberOfMessages for the queue
    :param boto3_session boto3 client session
    :param queue_url The URL of the queue
    :return Number of messages in queue
    """
    sqs_client = boto3_session.client('sqs')
    response = sqs_client.get_queue_attributes(
        QueueUrl=queue_url,
        AttributeNames=['ApproximateNumberOfMessages']
    )
    if 'Attributes' in response:
        visible_messages = "0"
        if 'ApproximateNumberOfMessages' in response['Attributes']:
            visible_messages = response['Attributes']['ApproximateNumberOfMessages']
        logging.debug(f'Queue with url {queue_url} has {visible_messages} visible messages')
        return visible_messages
    raise Exception('Queue not found')


def get_policy(boto3_session, queue_url: str):
    """
    Use get_queue_attributes aws method to get Policy for the queue
    :param boto3_session boto3 client session
    :param queue_url The URL of the queue
    :return Policy of the queue
    """
    sqs_client = boto3_session.client('sqs')
    response = sqs_client.get_queue_attributes(
        QueueUrl=queue_url,
        AttributeNames=['Policy']
    )
    if 'Attributes' in response and 'Policy' in response['Attributes']:
        return json.loads(response['Attributes']['Policy'])
    # Return empty policy if queue has no policy
    return {}


def get_queue_attribute(boto3_session, queue_url: str, attribute_name: str):
    """
    Use get_queue_attributes aws method to get any attribute by name
    :param boto3_session boto3 client session
    :param queue_url The URL of the queue
    :param attribute_name Attribute name
    :return Attribute value
    """
    sqs_client = boto3_session.client('sqs')
    response = sqs_client.get_queue_attributes(
        QueueUrl=queue_url,
        AttributeNames=[attribute_name]
    )
    if 'Attributes' in response and attribute_name in response['Attributes']:
        return response['Attributes'][attribute_name]
    raise Exception('Queue not found')
