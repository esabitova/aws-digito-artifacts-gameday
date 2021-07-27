import boto3
import logging
import time
from botocore.config import Config
from datetime import datetime, timedelta
from typing import Any, Callable, Iterator, List

boto3_config = Config(retries={'max_attempts': 20, 'mode': 'standard'})

PUT_METRIC_ALARM_PARAMS = ['AlarmName', 'AlarmDescription', 'ActionsEnabled', 'OKActions',
                           'AlarmActions', 'InsufficientDataActions', 'MetricName', 'Namespace', 'Statistic',
                           'ExtendedStatistic',
                           'Dimensions', 'Period', 'Unit', 'EvaluationPeriods', 'DatapointsToAlarm',
                           'Threshold', 'ComparisonOperator', 'TreatMissingData', 'EvaluateLowSampleCountPercentile',
                           'Metrics', 'Tags', 'ThresholdMetricId']


def _execute_boto3_cloudwatch(delegate: Callable[[Any], dict]) -> dict:
    """
    Executes the given delegate with cloudwatch client parameter
    :param delegate: The delegate to execute (with boto3 function)
    :return: The output of the given function
    """
    cloudwatch_client = boto3.client('cloudwatch', config=boto3_config)
    response = delegate(cloudwatch_client)
    if not response['ResponseMetadata']['HTTPStatusCode'] == 200:
        logging.error(response)
        raise ValueError('Failed to execute request')
    return response


def _execute_boto3_cloudwatch_paginator(func_name: str, search_exp: str = None, **kwargs) -> Iterator[Any]:
    """
    Executes the given function with pagination
    :param func_name: The function name of cloudwatch client
    :param search_exp: The search expression to return elements
    :param kwargs: The arguments of `func_name`
    :return: The iterator over elements on pages
    """
    dynamo_db_client = boto3.client('cloudwatch')
    paginator = dynamo_db_client.get_paginator(func_name)
    page_iterator = paginator.paginate(**kwargs)
    if search_exp:
        return page_iterator.search(search_exp)
    else:
        return page_iterator


def _describe_metric_alarms(alarm_names: List[str]) -> Iterator[dict]:
    """
    Returns all alarms setup in the current region
    """
    return _execute_boto3_cloudwatch_paginator(func_name='describe_alarms',
                                               search_exp='MetricAlarms[]',
                                               AlarmTypes=['MetricAlarm'],
                                               AlarmNames=alarm_names)


def _put_metric_alarm(**kwargs):
    """
    Updates or creates metric alarm with the given paramters:
    :param kwargs: The parametes for boto3 put_metric_alarm
    """
    return _execute_boto3_cloudwatch(
        delegate=lambda x: x.put_metric_alarm(**kwargs))


def get_metric_alarms_for_table(table_name: str, alarms_names: List[str]) -> Iterator[dict]:
    source_alarms = _describe_metric_alarms(alarm_names=alarms_names)
    for alarm in filter(lambda x: x.get('Namespace', '') == 'AWS/DynamoDB', source_alarms):
        for dimension in alarm['Dimensions']:
            if dimension['Name'] == 'TableName' and \
                    dimension['Value'] == table_name:
                yield alarm


def copy_alarms_for_dynamo_db_table(events, context):
    """
    Copies all the given alarm names from the source to the target table
    """
    if 'SourceTableName' not in events:
        raise KeyError('Requires SourceTableName')
    if 'TargetTableName' not in events:
        raise KeyError('Requires TargetTableName')
    if 'DynamoDBSourceTableAlarmNames' not in events:
        raise KeyError('Requires DynamoDBSourceTableAlarmNames')

    source_table_name: str = events['SourceTableName']
    target_table_name: str = events['TargetTableName']
    alarms_names: str = events.get('DynamoDBSourceTableAlarmNames', [])
    logging.info(
        f"Coping alarms for dynamodb table. Source: {source_table_name}, "
        f"Target: {target_table_name}. Alarm Names: {alarms_names}")

    source_alarms = get_metric_alarms_for_table(table_name=source_table_name, alarms_names=alarms_names)

    alarms_copied_count: int = 0

    for alarm in source_alarms:
        for dimension in alarm['Dimensions']:
            if dimension['Name'] == 'TableName' and \
                    dimension['Value'] == source_table_name:
                dimension['Value'] = target_table_name
                alarm['AlarmName'] = f"{alarm['AlarmName']}_{target_table_name}"

        keys = [*alarm.keys()]
        for key in keys:
            if key not in PUT_METRIC_ALARM_PARAMS:
                del alarm[key]
        _put_metric_alarm(**alarm)
        alarms_copied_count += 1

    return {
        "AlarmsChanged": alarms_copied_count
    }


def get_ec2_metric_max_datapoint(dimensions, metric_name, start_time_utc, end_time_utc, metric_namespace="AWS/EC2"):
    """
    Returns metric data point witch represents highest data point value for given metric name and EC2 instance id.
    :param dimensions: The metric dimensions array
    :param metric_name: The metric name
    :param start_time_utc: The metric interval start time in UTC
    :param end_time_utc: The metric interval end time in UTC
    :param metric_namespace: The metric namespace, defaults to "AWS/EC2"
    :return: The highest data point value.
    """
    cw = boto3.client('cloudwatch', config=boto3_config)
    response = cw.get_metric_statistics(
        Namespace=metric_namespace,
        MetricName=metric_name,
        Dimensions=dimensions,
        # CPU metric delay is 5 minutes
        StartTime=start_time_utc,
        EndTime=end_time_utc,
        # Minimum period for CPU/Memory metric - 1 minutes
        Period=60,
        Statistics=["Maximum"],
        Unit='Percent'
    )

    data_points = response['Datapoints']
    logging.info("[{}] metric for interval [{}::{}] data points: {}".format(metric_name, str(start_time_utc),
                                                                            str(end_time_utc), data_points))

    # get the first (earliest) datapoint value
    earliest_dp_value = 0.0
    min_dp_timestamp = time.time()
    for dp in data_points:
        current_dp_timestamp = dp['Timestamp'].timestamp()
        if min_dp_timestamp > current_dp_timestamp:
            min_dp_timestamp = current_dp_timestamp
            earliest_dp_value = float(dp['Maximum'])
    return earliest_dp_value


def describe_metric_alarm_state(alarm_name):
    """
    Returns alarm state for given alarm name.
    :param alarm_name: The alarm name
    :return: The alarm state.
    """
    cw = boto3.client('cloudwatch', config=boto3_config)
    response = cw.describe_alarms(
        AlarmNames=[alarm_name],
        AlarmTypes=[
            'MetricAlarm'
        ]
    )
    metric_alarms = response.get('MetricAlarms')
    if not metric_alarms:
        raise Exception("MetricAlarm [{}] does not exist.".format(alarm_name))
    return metric_alarms[0]['StateValue']


def verify_cpu_stress(events, context):
    """
    Verify CPU stress for given instances.
    :param events: The object which contains passed parameters from SSM document
    :param context: The context object for SSM documnent.
    """
    if 'InstanceIds' not in events\
            or 'StressDuration' not in events\
            or 'StressPercentage' not in events\
            or 'ExpectedRecoveryTime' not in events:
        raise KeyError('Requires InstanceIds, StressDuration, StressPercentage, ExpectedRecoveryTime in events')

    instance_ids = events['InstanceIds']
    exp_load_percentage = float(events['StressPercentage'])
    stress_duration = int(events['StressDuration'])
    exp_recovery_time = int(events['ExpectedRecoveryTime'])

    verify_ec2_stress(instance_ids, stress_duration, exp_load_percentage, 360, 'CPUUtilization', exp_recovery_time)


def verify_memory_stress(events, context):
    """
    Monitors Memory stress behaviour for given instances.
    :param events: The object which contains passed parameters from SSM document
    :param context: The context object for SSM documnent.
    """
    if 'InstanceIds' not in events \
            or 'StressDuration' not in events \
            or 'StressPercentage' not in events \
            or 'ExpectedRecoveryTime' not in events:
        raise KeyError('Requires InstanceIds, StressDuration, StressPercentage, ExpectedRecoveryTime in events')

    instance_ids = events['InstanceIds']
    exp_load_percentage = float(events['StressPercentage'])
    stress_duration = int(events['StressDuration'])
    exp_recovery_time = int(events['ExpectedRecoveryTime'])
    metric_namespace = events['MetricNamespace']
    asg_name = events['AutoScalingGroupName']
    pre_dimensions = [{"Name": "AutoScalingGroupName", "Value": asg_name}]

    # for some reason the memory load created is 70% of the requested load
    verify_ec2_stress(instance_ids, stress_duration, exp_load_percentage * 0.70,
                      360, 'mem_used_percent', exp_recovery_time,
                      metric_namespace, pre_dimensions)


def verify_alarm_triggered(events, context):
    """
    Verify if alarm triggered
    """
    if 'AlarmName' not in events or ('DurationInMinutes' not in events and 'DurationInSeconds' not in events):
        raise KeyError('Requires AlarmName and either DurationInMinutes or DurationInSeconds in events')

    cw = boto3.client('cloudwatch', config=boto3_config)

    if 'DurationInMinutes' in events:
        start_date = datetime.now() - timedelta(minutes=int(events['DurationInMinutes']))
    else:
        start_date = datetime.now() - timedelta(seconds=int(events['DurationInSeconds']))

    response = cw.describe_alarm_history(
        AlarmName=events['AlarmName'],
        HistoryItemType='StateUpdate',
        MaxRecords=2,
        ScanBy='TimestampDescending',
        StartDate=start_date)

    for alarm_history_item in response['AlarmHistoryItems']:
        if alarm_history_item['HistorySummary'] == "Alarm updated from OK to ALARM":
            return

    raise Exception('Alarm was not triggered')


def verify_ec2_stress(instance_ids, stress_duration, exp_load_percentage, metric_delay, metric_name,
                      exp_recovery_time, metric_namespace="AWS/EC2", pre_dimensions=[]):
    """
    Helper to verify stress test execution based on metric (CPU/Memory Utilization). Metric indicates whether stress
    testing was performed to specified load level, if not test is failed.
    :param instance_ids: The list of EC2 instance Ids to monitor
    :param stress_duration: The duration of stress test
    :param exp_load_percentage: The CPU/Memory percentage load for stress
    :param metric_delay: The CPU/Memory load metric delay in seconds to be used verify if stress is happening
    :param metric_name: The CPU/Memory load metric name in seconds to be used verify if stress is happening
    :param exp_recovery_time: The expected application recovery time in seconds after stress test
    :param metric_namespace: The metric namespace defaults to AWS/EC2
    :param pre_dimensions: The dimensions array to use before the instance dimension, defaults to []
    """

    # Delta is time which we already spend on performing stress test and waiting for recovery time
    delta = stress_duration + exp_recovery_time
    # Wait for metric available (for CPUUtilization minimum 5 minutes delay)
    metric_wait_time = metric_delay - delta if metric_delay - delta > 0 else 0
    time.sleep(metric_wait_time)

    # Start/End time interval for metric
    end_time_utc = datetime.utcnow()
    start_time_utc = end_time_utc - timedelta(seconds=delta)

    logging.info(
        "starttime: {}, endtime: {}, delay: {}".format(str(start_time_utc),
                                                       str(end_time_utc),
                                                       metric_wait_time))

    for instance_id in instance_ids:
        dimensions = pre_dimensions or []
        dimensions.append({"Name": "InstanceId", "Value": instance_id})
        actual_load = get_ec2_metric_max_datapoint(dimensions, metric_name,
                                                   start_time_utc, end_time_utc,
                                                   metric_namespace)
        if actual_load < exp_load_percentage:
            raise Exception(
                "Instance [{}] expected [{}] load [{}%] but was [{}%], start_time: [{}], end_time: [{}]".format(
                    instance_id, metric_name,
                    exp_load_percentage,
                    actual_load, str(start_time_utc), str(end_time_utc)))


def get_metric_alarm_threshold_values(event, context):
    """
    Get alarm threshold and return values above and below
    """
    alarm_name = event['AlarmName']
    cw = boto3.client('cloudwatch', config=boto3_config)
    response = cw.describe_alarms(
        AlarmNames=[alarm_name],
        AlarmTypes=['MetricAlarm']
    )
    metric_alarms = response.get('MetricAlarms')
    if not metric_alarms:
        raise Exception("MetricAlarm [{}] does not exist.".format(alarm_name))
    threshold = metric_alarms[0]['Threshold']
    if threshold == 0:
        raise Exception("MetricAlarm [{}] has no threshold set.".format(alarm_name))

    value_above_threshold = threshold + 1
    value_below_threshold = threshold - 1

    return {
        'Threshold': int(threshold),
        'ValueAboveThreshold': int(value_above_threshold),
        'ValueBelowThreshold': int(value_below_threshold)
    }
