import logging
import uuid

from botocore.exceptions import ClientError
from pytest_bdd import (
    parsers, when, given
)

from resource_manager.src.util import kinesis_data_streams_utils
from resource_manager.src.util.common_test_utils import (extract_param_value)


@when(parsers.parse('put "{messages_to_sent_number}" records separately to Kinesis Data Stream\n{input_parameters}'))
@given(parsers.parse('put "{messages_to_sent_number}" records to Kinesis Data Stream\n{input_parameters}'))
def put_records_separately_to_kinesis_data_stream(ssm_test_cache, resource_pool, boto3_session,
                                                  messages_to_sent_number, input_parameters):
    """
    Put records to Amazon Kinesis Data Streams separately
    :param ssm_test_cache: The ssm test cache
    :param resource_pool: The resource pool
    :param boto3_session: The boto3 session
    :param messages_to_sent_number: The number of messages
    :param input_parameters: The input parameters
    """
    kinesis_data_stream_name = extract_param_value(input_parameters, 'KinesisDataStreamName', resource_pool,
                                                   ssm_test_cache)
    client = boto3_session.client('kinesis')
    for i in range(int(messages_to_sent_number)):
        message = f'This is the {i} message.'
        client.put_record(StreamName=kinesis_data_stream_name,
                          Data=bytes(message, 'utf-8'),
                          PartitionKey=str(uuid.uuid4()))
        logging.info(f'Message "{message}" was sent to stream = {kinesis_data_stream_name}"')


@when(parsers.parse('put "{messages_to_sent_number}" records in a batch to Kinesis Data Stream\n{input_parameters}'))
@given(parsers.parse('put "{messages_to_sent_number}" records in a batch to Kinesis Data Stream\n{input_parameters}'))
def put_records_in_batch_to_kinesis_data_stream(ssm_test_cache, resource_pool, boto3_session,
                                                messages_to_sent_number, input_parameters):
    """
    Put records to Amazon Kinesis Data Streams in the batch
    :param ssm_test_cache: The ssm test cache
    :param resource_pool: The resource pool
    :param boto3_session: The boto3 session
    :param messages_to_sent_number: The number of messages
    :param input_parameters: The input parameters
    """
    kinesis_data_stream_name = extract_param_value(input_parameters, 'KinesisDataStreamName', resource_pool,
                                                   ssm_test_cache)
    client = boto3_session.client('kinesis')
    records = []
    for i in range(int(messages_to_sent_number)):
        message = f'This is the {i} message.'
        records.append({'Data': bytes(message, 'utf-8'), 'PartitionKey': str(uuid.uuid4())})
    client.put_records(StreamName=kinesis_data_stream_name,
                       Records=records)
    logging.info(f'{messages_to_sent_number} records were sent to stream = {kinesis_data_stream_name}"')


@when(parsers.parse('put "{messages_to_sent_number:d}" records asynchronously in "{threads_number:d}" threads '
                    'with "{delay_in_secs_between_threads:d}" seconds delay between each other to '
                    'Kinesis Data Stream\n{input_parameters}'))
@given(parsers.parse('put "{messages_to_sent_number:d}" records asynchronously in "{threads_number:d}" threads '
                     'with "{delay_in_secs_between_threads:d}" seconds delay between each other to '
                     'Kinesis Data Stream\n{input_parameters}'))
def put_records_async_to_kinesis_data_stream(ssm_test_cache, resource_pool, boto3_session,
                                             messages_to_sent_number, threads_number, delay_in_secs_between_threads,
                                             input_parameters):
    """
    Stress test for Kinesis Data Streams to put records in a batch asynchronously to perform stress test.
    Use multiple threads to make lots of simultaneous PutRecords requests.
    :param ssm_test_cache: The ssm test cache
    :param resource_pool: The resource pool
    :param boto3_session: The boto3 session
    :param messages_to_sent_number: The number of messages in each batch
    :param threads_number: The number of threads to be used to sent records
    :param delay_in_secs_between_threads: The delay in seconds between threads
    :param input_parameters: The input parameters
    """
    kinesis_data_stream_name = extract_param_value(input_parameters, 'KinesisDataStreamName', resource_pool,
                                                   ssm_test_cache)
    kinesis_data_streams_utils.put_records_in_batch_async(boto3_session, kinesis_data_stream_name,
                                                          messages_to_sent_number, threads_number,
                                                          delay_in_secs_between_threads)


@when(parsers.parse('get maximum "{messages_to_get_number:d}" records asynchronously in "{threads_number:d}" threads '
                    'with "{delay_in_secs_between_threads:d}" seconds delay between each other from '
                    'Kinesis Data Stream and handle "{error_code}" error\n{input_parameters}'))
@given(parsers.parse('get maximum "{messages_to_get_number:d}" records asynchronously in "{threads_number:d}" threads '
                     'with "{delay_in_secs_between_threads:d}" seconds delay between each other from '
                     'Kinesis Data Stream and handle "{error_code}" error\n{input_parameters}'))
def get_records_async_from_kinesis_data_stream(ssm_test_cache, resource_pool, boto3_session,
                                               messages_to_get_number, threads_number, delay_in_secs_between_threads,
                                               error_code, input_parameters):
    """
    Get records from Amazon Kinesis Data Streams in the batch asynchronously
    :param ssm_test_cache: The ssm test cache
    :param resource_pool: The resource pool
    :param boto3_session: The boto3 session
    :param messages_to_get_number: The number of messages in each batch
    :param threads_number: The number of threads to be used to get records
    :param delay_in_secs_between_threads: The delay in seconds between threads
    :param error_code: The error code associated to a ClientError exception
    :param input_parameters: The input parameters
    """
    kinesis_data_stream_name = extract_param_value(input_parameters, 'KinesisDataStreamName', resource_pool,
                                                   ssm_test_cache)
    try:
        kinesis_data_streams_utils.get_records_in_batch_async(boto3_session, kinesis_data_stream_name,
                                                              messages_to_get_number, threads_number,
                                                              delay_in_secs_between_threads)
    except ClientError as e:
        if e.response['Error']['Code'] == 'ReadProvisionedThroughputExceeded':
            logging.info(f'Expected error was occurred: {e}')


@when(parsers.parse('get maximum "{records_limit:d}" records from Kinesis Data Stream\n{input_parameters}'))
@given(parsers.parse('get maximum "{records_limit:d}" records from Kinesis Data Stream\n{input_parameters}'))
def get_latest_records_from_kinesis_data_stream(ssm_test_cache, resource_pool, boto3_session,
                                                records_limit, input_parameters):
    """
    Get latest records from Amazon Kinesis Data Streams
    :param ssm_test_cache: The ssm test cache
    :param resource_pool: The resource pool
    :param boto3_session: The boto3 session
    :param records_limit: Number of records retrieved from Amazon Kinesis Data Streams
    :param input_parameters: The input parameters
    """
    kinesis_data_stream_name = extract_param_value(input_parameters, 'KinesisDataStreamName', resource_pool,
                                                   ssm_test_cache)
    client = boto3_session.client('kinesis')
    shard_id = client.describe_stream(StreamName=kinesis_data_stream_name)['StreamDescription']['Shards'][0]['ShardId']
    shard_iterator = client.get_shard_iterator(StreamName=kinesis_data_stream_name, ShardId=shard_id,
                                               ShardIteratorType='TRIM_HORIZON')['ShardIterator']
    records_number = len(client.get_records(ShardIterator=shard_iterator, Limit=records_limit)['Records'])
    logging.info(f'Received {records_number} records from {kinesis_data_stream_name} stream '
                 f'and {shard_iterator} shard iterator')
