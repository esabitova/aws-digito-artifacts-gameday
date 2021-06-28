# coding=utf-8
import logging
import time

from pytest_bdd import (
    scenario,
    when,
    parsers
)

from resource_manager.src.util.common_test_utils import extract_param_value
import resource_manager.src.util.dynamo_db_utils as dynamo_db_utils
from resource_manager.src.util.cw_util import get_metric_alarm_state
from resource_manager.src.util.enums.alarm_state import AlarmState
from resource_manager.src.util.param_utils import parse_param_value


@scenario('../features/dynamodb_recovery-replication_latency.feature',
          'Replication Latency - green')
def test_alarm_green():
    pass


@scenario('../features/dynamodb_recovery-replication_latency.feature',
          'Replication Latency - red')
def test_alarm_red():
    pass


@when(parsers.parse('put random test items until alarm {alarm_name_ref} becomes {alarm_expected_state} '
                    'for {time_to_wait} seconds, '
                    'check every {interval} seconds\n{input_parameters}'))
def put_items_async(boto3_session, resource_pool, cfn_installed_alarms, cfn_output_params,
                    ssm_test_cache, alarm_name_ref, alarm_expected_state, interval, time_to_wait,
                    input_parameters):
    table_name: str = extract_param_value(input_parameters, "DynamoDBTableName", resource_pool, ssm_test_cache)
    dynamo_db_client = boto3_session.client('dynamodb')
    timeout_timestamp = time.time() + int(time_to_wait)
    alarm_name = parse_param_value(alarm_name_ref, {'cfn-output': cfn_output_params,
                                                    'cache': ssm_test_cache,
                                                    'alarm': cfn_installed_alarms})
    alarm_state = AlarmState.INSUFFICIENT_DATA
    iteration = 1
    elapsed = 0
    while elapsed < timeout_timestamp:
        start = time.time()
        item = dynamo_db_utils.generate_random_item(boto3_session, table_name)
        dynamo_db_client.put_item(TableName=table_name, Item=item)
        alarm_state = get_metric_alarm_state(session=boto3_session,
                                             alarm_name=alarm_name)
        logging.info(f'#{iteration}; Alarm:{alarm_name}; State: {alarm_state};'
                     f'Elapsed: {elapsed} sec;')
        if alarm_state == AlarmState[alarm_expected_state]:
            return
        end = time.time()
        elapsed += (end - start)
        iteration += 1
        time.sleep(int(interval))

    raise TimeoutError(f'After {time_to_wait} alarm {alarm_name} is in {alarm_state} state;'
                       f'Expected state: {alarm_expected_state}'
                       f'Elapsed: {elapsed} sec;'
                       f'{iteration} iterations;')
