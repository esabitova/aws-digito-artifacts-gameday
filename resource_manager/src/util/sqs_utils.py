import json
import logging


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
