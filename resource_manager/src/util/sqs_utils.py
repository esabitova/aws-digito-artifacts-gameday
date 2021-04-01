import logging
import json


def send_message_to_standard_queue(boto3_session, queue_url: str, body: str):
    """
    Use send_message aws method to send message to queue
    :param boto3_session boto3 client session
    :param queue_url The URL of the queue
    :param body Message body
    """
    sqs_client = boto3_session.client('sqs')
    sqs_client.send_message(
        QueueUrl=queue_url,
        MessageBody=body
    )


def send_message_to_fifo_queue(boto3_session, queue_url: str, body: str, message_group_id: str, token: str):
    """
    Use send_message aws method to send message to queue
    :param boto3_session boto3 client session
    :param queue_url The URL of the queue
    :param body Message body
    :param token Unique token for MessageDeduplicationId for FIFO queue message
    :param message_group_id MessageGroupId for FIFO queue
    """
    sqs_client = boto3_session.client('sqs')
    sqs_client.send_message(
        QueueUrl=queue_url,
        MessageBody=body,
        MessageDeduplicationId=token,
        MessageGroupId=message_group_id
    )


def get_number_of_messages(boto3_session, queue_url: str):
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
    if response['Attributes']:
        visible_messages = "0"
        if 'ApproximateNumberOfMessages' in response['Attributes']:
            visible_messages = response['Attributes']['ApproximateNumberOfMessages']
        logging.info(f'Queue has {visible_messages} visible messages')
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
