import logging
import time
import uuid
from concurrent.futures.thread import ThreadPoolExecutor

from boto3 import Session


def generate_records(messages_to_sent_number: int):
    """
    Generate records to sent to a stream
    :param messages_to_sent_number: The number of messages in each batch
    :return: The generated records
    """
    records = []
    for i in range(int(messages_to_sent_number)):
        records.append({'Data': bytes(str(i), 'utf-8'), 'PartitionKey': str(uuid.uuid4())})
    return records


def put_records_in_batch_async(boto3_session: Session, stream_name: str,
                               messages_to_sent_number: int, threads_number: int, delay_in_secs_between_threads: int):
    """
    Stress test for Kinesis Data Streams to put records in a batch asynchronously to perform stress test.
    Use multiple threads to make lots of simultaneous PutRecords requests.
    :param delay_in_secs_between_threads: The delay in seconds between threads
    :param threads_number: The number of threads to be used to sent records
    :param messages_to_sent_number: The number of messages in each batch
    :param stream_name: The stream name
    :param boto3_session The boto3 session
    """
    futures = []
    logging.info(f'Start Kinesis Data Streams PutRecords asynchronously in the {threads_number} threads')
    with ThreadPoolExecutor() as executor:
        for _ in range(threads_number):
            records = generate_records(messages_to_sent_number)
            futures.append(
                executor.submit(put_records, boto3_session, stream_name, records)
            )
            time.sleep(delay_in_secs_between_threads)
    logging.info('Kinesis Data Streams asynchronous PutRecords were done')


def put_records(boto3_session, stream_name: str, records: list):
    """
    Put records to Amazon Kinesis Data Streams in the batch
    :param records: The records to sent
    :param stream_name: The stream name
    :param boto3_session The boto3 session
    """
    client = boto3_session.client('kinesis')
    failed_record_count = client.put_records(StreamName=stream_name, Records=records)['FailedRecordCount']
    logging.info(f'Execution of put_records to {stream_name} Kinesis Data Stream was completed, '
                 f'the number of failed records to sent: {failed_record_count}')


def get_records(boto3_session, shard_iterator: str, limit: int):
    """
    Get records from Amazon Kinesis Data Streams in the batch
    :param limit:
    :param shard_iterator:
    :param boto3_session The boto3 session
    """
    client = boto3_session.client('kinesis')
    client.get_records(ShardIterator=shard_iterator, Limit=limit)


def get_records_in_batch_async(boto3_session, stream_name, messages_to_get_number, threads_number,
                               delay_in_secs_between_threads):
    futures = []
    logging.info(f'Start Kinesis Data Streams GetRecords asynchronously in the {threads_number} threads')
    client = boto3_session.client('kinesis')
    shard_id = client.describe_stream(StreamName=stream_name)['StreamDescription']['Shards'][0]['ShardId']
    shard_iterator = client.get_shard_iterator(StreamName=stream_name, ShardId=shard_id,
                                               ShardIteratorType='TRIM_HORIZON')['ShardIterator']
    with ThreadPoolExecutor() as executor:
        for _ in range(threads_number):
            futures.append(
                executor.submit(get_records, boto3_session, shard_iterator, messages_to_get_number)
            )
            time.sleep(delay_in_secs_between_threads)
    logging.info('Kinesis Data Streams asynchronous GetRecords were done')
