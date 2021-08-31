import logging
from datetime import datetime
from time import sleep

import pytest
from pytest_bdd import scenario


@scenario('../features/decrease_number_of_shards_usual_case.feature',
          'Execute Digito-DecreaseNumberOfShards_2020-09-21 in usual case')
def test_decrease_number_of_shards_usual_case():
    """Execute SSM automation document Digito-DecreaseNumberOfShards_2020-09-21"""


@scenario('../features/decrease_number_of_shards_rollback_previous.feature',
          'Execute SSM automation document Digito-DecreaseNumberOfShards_2020-09-21 in rollback')
def test_decrease_number_of_shards_rollback_previous():
    """Execute SSM automation document Digito-DecreaseNumberOfShards_2020-09-21 in rollback"""


@scenario('../features/decrease_number_of_shards_failed.feature',
          'Execute SSM automation document Digito-DecreaseNumberOfShards_2020-09-21 to test failure case')
def test_decrease_number_of_shards_failed():
    """Execute SSM automation document Digito-DecreaseNumberOfShards_2020-09-21 to test failure case"""


@pytest.fixture(scope='function', autouse=True)
def teardown_kinesis_data_streams_rollback_shard_count(boto3_session, ssm_test_cache, function_logger):
    """
    Revert back the shard count of the Amazon Kinesis Data Stream
    """
    yield
    stream_name = ssm_test_cache['before']['StreamName']
    old_shard_count = ssm_test_cache['before']['OldShardCount']
    client = boto3_session.client('kinesis')
    logging.info(f'Reverting back the shard count to {old_shard_count} for {stream_name} stream')
    client.update_shard_count(StreamName=stream_name, TargetShardCount=old_shard_count, ScalingType='UNIFORM_SCALING')
    script_timeout = 10 * 60
    logging.info(f'Waiting for the ACTIVE status of the {stream_name} stream during {script_timeout} seconds')

    start = datetime.now()
    attempt = 1
    while (datetime.now() - start).total_seconds() < script_timeout:
        attempt += 1
        stream_description = client.describe_stream(StreamName=stream_name)['StreamDescription']
        stream_status = stream_description['StreamStatus']
        if stream_status == 'ACTIVE':
            logging.info(f'The stream {stream_name} became in ACTIVE status after {attempt} attempts '
                         f'and {(datetime.now() - start).total_seconds()} seconds')
            count = client.describe_stream_summary(StreamName=stream_name)['StreamDescriptionSummary']['OpenShardCount']
            if count == old_shard_count:
                logging.info(f'The stream {stream_name} was reverted back to the old {count} shard counts.')
            else:
                logging.info(f'The stream {stream_name} was updated to the {count} shard counts but it is not the '
                             f'old value of the shard counts which was desired to rollback.')
            return
        sleep(15)
    logging.info(f'The stream {stream_name} was not reverted after {attempt} attempts '
                 f'and {(datetime.now() - start).total_seconds()} seconds')
